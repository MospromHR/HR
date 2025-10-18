import os
from pathlib import Path
from typing import Any, Mapping

import yaml
from dotenv import dotenv_values


def deep_merge(base: dict[str, Any], overlay: Mapping[str, Any]) -> dict[str, Any]:
    """
    Рекурсивный мердж словарей: overlay перекрывает base.
    Списки/скаляры — замена целиком.
    """
    res = dict(base)
    for k, v in overlay.items():
        if k in res and isinstance(res[k], dict) and isinstance(v, Mapping):
            res[k] = deep_merge(res[k], v)  # type: ignore[arg-type]
        else:
            res[k] = v
    return res


def read_yaml_object(path: Path) -> dict[str, Any]:
    txt = path.read_text(encoding="utf-8")
    data = yaml.safe_load(txt) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML должен описывать объект/словарь: {path}")
    return data


def read_dotenv(path: Path, *, nested_delimiter="_", prefix="") -> dict[str, Any]:
    flat: dict[str, str] = {k: v for k, v in dotenv_values(path).items() if k and v is not None and k.startswith(prefix)}
    return env_flat_to_nested(flat, nested_delimiter=nested_delimiter, prefix=prefix)


def read_env(*, nested_delimiter="_", prefix=""):
    flat = {k: v for k, v in os.environ.items() if k.startswith(prefix)}
    return env_flat_to_nested(flat, nested_delimiter=nested_delimiter, prefix=prefix)


def env_flat_to_nested(
    flat: dict[str, str],
    nested_delimiter: str = "_",
    prefix: str = "",
) -> dict[str, Any]:
    nested: dict[str, Any] = {}
    for key, value in flat.items():
        if not key.startswith(prefix):
            continue
        remainder = key[len(prefix):]
        if not remainder:
            continue

        tokens = [token.lower() for token in remainder.split(nested_delimiter) if token]
        if not tokens:
            continue

        if len(tokens) == 1:
            nested[tokens[0]] = value
            continue

        top_key, *rest_tokens = tokens
        leaf_key = "_".join(rest_tokens)

        if top_key not in nested or not isinstance(nested[top_key], dict):
            nested[top_key] = {}

        nested[top_key][leaf_key] = value
    return nested


