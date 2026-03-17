"""
EcoLens — Security Middleware
Rate limiting via slowapi + file validation (MIME, size, dimensions).
"""
from __future__ import annotations

import magic
from fastapi import HTTPException, Request
from loguru import logger
from slowapi import Limiter
from slowapi.util import get_remote_address

from config import settings
from utils.image_utils import check_image_dimensions

# ─── Rate Limiter ─────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)


# ─── File Validation ──────────────────────────────────────────────────────────
ALLOWED_MIME = frozenset({"image/jpeg", "image/png", "image/webp"})


def validate_image(image_bytes: bytes) -> None:
    """
    Validate raw image bytes before passing to detector.
    Raises HTTPException(400) with specific error messages for any failure.
    """
    # 1. Size check
    if len(image_bytes) > settings.max_image_bytes:
        logger.bind(event="request_rejected", reason="size_exceeded").warning(
            f"Image too large: {len(image_bytes)} bytes"
        )
        raise HTTPException(
            status_code=400,
            detail=f"Image exceeds {settings.max_image_size_mb}MB limit",
        )

    # 2. MIME type check via python-magic (reads magic bytes only)
    mime = magic.from_buffer(image_bytes[:2048], mime=True)
    if mime not in ALLOWED_MIME:
        logger.bind(event="request_rejected", reason="mime_invalid").warning(
            f"Unsupported MIME: {mime}"
        )
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported image format: {mime}. Accepted: JPEG, PNG, WebP",
        )

    # 3. Dimension check
    try:
        check_image_dimensions(image_bytes, max_dim=4096)
    except ValueError as exc:
        logger.bind(event="request_rejected", reason="dimension_exceeded").warning(str(exc))
        raise HTTPException(status_code=400, detail=str(exc)) from exc
