"""EcoLens — Security Middleware"""
from __future__ import annotations

import magic
from fastapi import HTTPException, Request
from loguru import logger
from slowapi import Limiter
from slowapi.util import get_remote_address

from config import settings
from utils.image_utils import check_image_dimensions

limiter = Limiter(key_func=get_remote_address)

ALLOWED_MIME = frozenset({"image/jpeg", "image/png", "image/webp"})


def validate_image(image_bytes: bytes) -> None:
    if len(image_bytes) > settings.max_image_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"Image exceeds {settings.max_image_size_mb}MB limit",
        )

    mime = magic.from_buffer(image_bytes[:2048], mime=True)
    if mime not in ALLOWED_MIME:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported image format: {mime}. Accepted: JPEG, PNG, WebP",
        )

    try:
        check_image_dimensions(image_bytes, max_dim=4096)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
