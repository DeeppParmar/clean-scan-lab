"""
EcoLens — Image Utilities
"""
from __future__ import annotations

import base64
import io
import uuid
from typing import Optional

import cv2
import numpy as np
from PIL import Image


def decode_base64_image(b64_string: str) -> tuple[bytes, np.ndarray]:
    """Decode base64 encoded image string → (raw_bytes, numpy_bgr_array)."""
    # Strip data URI prefix if present
    if "," in b64_string:
        b64_string = b64_string.split(",", 1)[1]
    image_bytes = base64.b64decode(b64_string)
    nparr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Could not decode image from bytes")
    return image_bytes, image


def decode_jpeg_bytes(data: bytes) -> Optional[np.ndarray]:
    """Decode raw JPEG bytes from WebSocket to numpy BGR array."""
    try:
        nparr = np.frombuffer(data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return frame
    except Exception:
        return None


def resize_image(image: np.ndarray, max_size: int = 640) -> np.ndarray:
    """Resize to max_size on longest side, maintaining aspect ratio."""
    h, w = image.shape[:2]
    if max(h, w) <= max_size:
        return image
    scale = max_size / max(h, w)
    new_w = int(w * scale)
    new_h = int(h * scale)
    return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)


def annotate_image(image: np.ndarray, detections: list) -> np.ndarray:
    """Draw bounding boxes and labels on a copy of the image."""
    img = image.copy()
    h, w = img.shape[:2]

    COLORS: dict[str, tuple[int, int, int]] = {
        "plastic":  (0, 165, 255),
        "organic":  (0, 200, 0),
        "ewaste":   (0, 0, 255),
        "metal":    (180, 180, 180),
        "paper":    (255, 200, 0),
        "glass":    (255, 100, 200),
        "textile":  (200, 0, 200),
        "general":  (80, 80, 80),
        "unknown":  (100, 100, 100),
    }

    for det in detections:
        x1, y1, x2, y2 = (
            int(det.bbox[0] * w),
            int(det.bbox[1] * h),
            int(det.bbox[2] * w),
            int(det.bbox[3] * h),
        )
        color = COLORS.get(det.category, (200, 200, 200))
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)

        label_str = f"{det.label} {det.confidence:.2f}"
        (tw, th), _ = cv2.getTextSize(label_str, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(img, (x1, y1 - th - 6), (x1 + tw + 4, y1), color, -1)
        cv2.putText(img, label_str, (x1 + 2, y1 - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    return img


def encode_image_to_jpeg_bytes(image: np.ndarray, quality: int = 90) -> bytes:
    """Encode numpy BGR image to JPEG bytes."""
    _, buf = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, quality])
    return buf.tobytes()


def check_image_dimensions(image_bytes: bytes, max_dim: int = 4096) -> tuple[int, int]:
    """Return (width, height) from raw bytes. Raises ValueError if too large."""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        w, h = img.size
        if w > max_dim or h > max_dim:
            raise ValueError(f"Image dimensions {w}x{h} exceed {max_dim}px limit")
        return w, h
    except Exception as exc:
        raise ValueError(str(exc)) from exc
