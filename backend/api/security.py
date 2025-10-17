from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from datetime import timedelta
from typing import Any, Dict


PBKDF2_ITERATIONS = 390_000


class TokenError(ValueError):
    """Raised when a JWT token cannot be decoded or validated."""


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    derived = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS
    )
    return f"{_b64encode(salt)}.{_b64encode(derived)}"


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        salt_b64, hashed_b64 = hashed_password.split(".", 1)
    except ValueError:
        return False

    salt = _b64decode(salt_b64)
    derived = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS
    )
    return hmac.compare_digest(_b64encode(derived), hashed_b64)


def create_access_token(
    payload: Dict[str, Any], *, secret: str, expires_delta: timedelta
) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    now = int(time.time())
    data = dict(payload)
    data["iat"] = now
    data["exp"] = now + int(expires_delta.total_seconds())

    header_segment = _b64encode(json.dumps(header, separators=(",", ":"), sort_keys=True).encode())
    payload_segment = _b64encode(json.dumps(data, separators=(",", ":"), sort_keys=True).encode())

    signing_input = f"{header_segment}.{payload_segment}".encode()
    signature = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    signature_segment = _b64encode(signature)

    return "".join([header_segment, ".", payload_segment, ".", signature_segment])


def decode_access_token(token: str, *, secret: str) -> Dict[str, Any]:
    try:
        header_segment, payload_segment, signature_segment = token.split(".")
    except ValueError as exc:
        raise TokenError("Invalid token format") from exc

    signing_input = f"{header_segment}.{payload_segment}".encode()
    expected_signature = _b64encode(
        hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    )

    if not hmac.compare_digest(expected_signature, signature_segment):
        raise TokenError("Invalid token signature")

    header = json.loads(_b64decode(header_segment).decode("utf-8"))
    if header.get("alg") != "HS256":
        raise TokenError("Unsupported token algorithm")

    payload = json.loads(_b64decode(payload_segment).decode("utf-8"))

    exp = payload.get("exp")
    if exp is not None and int(exp) < int(time.time()):
        raise TokenError("Token has expired")

    return payload


__all__ = [
    "TokenError",
    "create_access_token",
    "decode_access_token",
    "hash_password",
    "verify_password",
]
