from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi import UploadFile


def _ensure_within_root(path: Path, root: Path) -> bool:
    try:
        return path.is_relative_to(root)
    except AttributeError:
        return str(path).startswith(str(root))


def _extract_previous_relative(
    previous_path: str, public_prefix: str
) -> Optional[Path]:
    if not previous_path:
        return None

    cleaned = previous_path.lstrip("/")
    prefix = public_prefix.strip("/")

    if prefix:
        if cleaned == prefix:
            return None
        prefix_with_sep = prefix + "/"
        if not cleaned.startswith(prefix_with_sep):
            return None
        cleaned = cleaned[len(prefix_with_sep) :]

    return Path(cleaned) if cleaned else None


def save_media_file(
    upload: UploadFile,
    subdir: str,
    previous_path: Optional[str] = None,
    *,
    media_root: Path,
    public_prefix: str,
) -> str:
    """Persist an uploaded file under the configured media directory."""

    media_root = media_root.resolve()
    media_root.mkdir(parents=True, exist_ok=True)

    suffix = Path(upload.filename or "").suffix.lower() or ".bin"
    filename = f"{uuid4().hex}{suffix}"

    sanitized_subdir = subdir.strip("/")
    relative_path = Path(sanitized_subdir) / filename if sanitized_subdir else Path(filename)
    absolute_path = (media_root / relative_path).resolve()
    absolute_path.parent.mkdir(parents=True, exist_ok=True)

    upload.file.seek(0)
    with absolute_path.open("wb") as buffer:
        shutil.copyfileobj(upload.file, buffer)

    previous_relative = _extract_previous_relative(previous_path or "", public_prefix)
    if previous_relative:
        previous_absolute = (media_root / previous_relative).resolve()
        if previous_absolute.is_file() and _ensure_within_root(previous_absolute, media_root):
            try:
                previous_absolute.unlink()
            except FileNotFoundError:
                pass

    public_prefix = public_prefix.strip("/")
    public_path = Path(public_prefix) / relative_path if public_prefix else relative_path
    return "/" + public_path.as_posix()
