from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi import UploadFile


MEDIA_ROOT = Path.cwd() / "media"


def _ensure_media_root() -> None:
    MEDIA_ROOT.mkdir(parents=True, exist_ok=True)


def save_media_file(upload: UploadFile, subdir: str, previous_path: Optional[str] = None) -> str:
    """Persist an uploaded file under the media directory.

    The function stores files in ``media/<subdir>`` and removes the previous
    file if it exists within the media root.
    """
    _ensure_media_root()

    suffix = Path(upload.filename or "").suffix.lower() or ".bin"
    filename = f"{uuid4().hex}{suffix}"
    relative_path = Path("media") / subdir / filename
    absolute_path = Path.cwd() / relative_path
    absolute_path.parent.mkdir(parents=True, exist_ok=True)

    upload.file.seek(0)
    with absolute_path.open("wb") as buffer:
        shutil.copyfileobj(upload.file, buffer)

    if previous_path:
        previous = Path(previous_path.lstrip("/"))
        previous_absolute = (Path.cwd() / previous).resolve()
        media_root = MEDIA_ROOT.resolve()
        try:
            is_inside_media = previous_absolute.is_relative_to(media_root)
        except AttributeError:
            is_inside_media = str(previous_absolute).startswith(str(media_root))

        if previous_absolute.is_file() and is_inside_media:
            try:
                previous_absolute.unlink()
            except FileNotFoundError:
                pass

    return "/" + relative_path.as_posix()
