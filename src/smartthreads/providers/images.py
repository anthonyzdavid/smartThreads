from __future__ import annotations

import base64
import mimetypes
from pathlib import Path

from .base import ProviderError


def read_image_base64(path: str) -> str:
    image_path = Path(path)
    if not image_path.exists():
        raise ProviderError(f"image does not exist: {path}")
    if not image_path.is_file():
        raise ProviderError(f"image path is not a file: {path}")
    return base64.b64encode(image_path.read_bytes()).decode("ascii")


def image_data_url(path: str) -> str:
    mime_type, _ = mimetypes.guess_type(path)
    return f"{mime_type or 'image/jpeg'};base64,{read_image_base64(path)}"
