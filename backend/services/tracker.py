"""
EcoLens — Stream Tracker Service
Each WebSocket connection gets its own session that uses
the shared MobileNetV2 classifier for per-frame classification.
"""
from __future__ import annotations

import uuid
from typing import Optional

import numpy as np
from loguru import logger

from config import settings
from models.schemas import Detection
from services.detector import detector
from services.rule_engine import apply_rules
from utils.label_map import normalize_category
from utils.image_utils import resize_image

# Max concurrent WebSocket tracker sessions
MAX_SESSIONS: int = settings.max_ws_connections

# Active session registry: connection_id → TrackerSession
_active_sessions: dict[str, "TrackerSession"] = {}


class TrackerSession:
    """Owns a classification context for a WebSocket stream connection."""

    def __init__(self, connection_id: str) -> None:
        self.id = connection_id
        self._last_category: Optional[str] = None
        self._stable_count: int = 0  # frames with same category
        logger.info(f"TrackerSession created [{connection_id}]")

    def track_frame(self, frame: np.ndarray) -> list[Detection]:
        """Classify one frame using the shared MobileNetV2 model.
        Uses temporal smoothing: only changes output after 3 consecutive
        frames with a different classification to reduce flickering."""
        import cv2
        from PIL import Image
        import torch

        h, w = frame.shape[:2]

        # Convert BGR → RGB PIL → tensor
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)
        tensor = detector.transform(pil_img).unsqueeze(0).to(detector.device)

        with torch.no_grad():
            logits = detector.classifier(tensor)
            probs = torch.softmax(logits, dim=1)

        confidence_val, idx = probs.max(1)
        confidence_val = confidence_val.item()
        raw_category = detector._class_names[idx.item()]

        # Confidence gate
        if confidence_val < 0.40:
            return []

        category, label = normalize_category(raw_category)

        # Temporal smoothing — reduce flickering in video stream
        if category == self._last_category:
            self._stable_count += 1
        else:
            self._stable_count = 1
            self._last_category = category

        # Only report after 2 stable frames
        if self._stable_count < 2:
            return []

        rules = apply_rules(category, count=1)
        return [
            Detection(
                id=str(uuid.uuid4()),
                label=label,
                category=category,
                confidence=confidence_val,
                bbox=[0.0, 0.0, 1.0, 1.0],
                track_id=1,  # single tracked classification
                **rules,
            )
        ]

    def close(self) -> None:
        logger.info(f"TrackerSession closed [{self.id}]")


# ─── Session lifecycle helpers ────────────────────────────────────────────────

def create_session() -> Optional["TrackerSession"]:
    """Create a new tracker session. Returns None if capacity is full."""
    if len(_active_sessions) >= MAX_SESSIONS:
        return None
    sid = str(uuid.uuid4())
    session = TrackerSession(sid)
    _active_sessions[sid] = session
    return session


def remove_session(session: "TrackerSession") -> None:
    """Remove tracker session from registry and clean up."""
    session.close()
    _active_sessions.pop(session.id, None)


def active_session_count() -> int:
    return len(_active_sessions)
