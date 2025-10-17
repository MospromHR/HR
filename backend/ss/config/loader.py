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
        p = key[len(prefix):]
        if not p:
            continue
        parts = [p.lower() for p in p.split(nested_delimiter) if p]
        cursor = nested
        for i, part in enumerate(parts):
            is_last = i == len(parts) - 1
            if is_last:
                cursor[part] = value
            else:
                if part not in cursor or not isinstance(cursor[part], dict):
                    cursor[part] = {}
                cursor = cursor[part]
    return nested


