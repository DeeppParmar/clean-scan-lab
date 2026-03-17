"""
EcoLens — ByteTrack Tracker Service
Each WebSocket connection gets its own TrackerSession (separate YOLO instance).
Sharing tracker state across connections causes track ID cross-contamination.
"""
from __future__ import annotations

import asyncio
import uuid
from typing import Optional

import numpy as np
from loguru import logger
from ultralytics import YOLO

from config import settings
from models.schemas import Detection
from services.rule_engine import apply_rules
from utils.label_map import LABEL_MAP
from utils.image_utils import resize_image

# Max concurrent WebSocket tracker sessions
MAX_SESSIONS: int = settings.max_ws_connections

# Active session registry: connection_id → TrackerSession
_active_sessions: dict[str, "TrackerSession"] = {}


class TrackerSession:
    """Owns a YOLO instance with its persistent ByteTrack state."""

    def __init__(self, connection_id: str) -> None:
        self.id = connection_id
        logger.info(f"TrackerSession created [{connection_id}]")
        self._model = YOLO(settings.model_path)
        try:
            self._model.model.half()
        except Exception:
            pass  # FP32 fallback

    def track_frame(self, frame: np.ndarray) -> list[Detection]:
        """Run ByteTrack inference on one frame. Returns tracked detections."""
        frame = resize_image(frame, max_size=640)
        results = self._model.track(
            frame,
            persist=True,
            conf=settings.yolo_conf,
            tracker="bytetrack.yaml",
            verbose=False,
        )

        detections: list[Detection] = []
        h, w = frame.shape[:2]

        for result in results:
            if result.boxes is None:
                continue
            for i, box in enumerate(result.boxes):
                confidence = float(box.conf[0])
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                area_ratio = ((x2 - x1) * (y2 - y1)) / (w * h)
                if area_ratio < 0.01:
                    continue

                cls_idx = int(box.cls[0])
                category, label = LABEL_MAP.get(cls_idx, ("unknown", "Unknown Object"))
                bbox = [x1 / w, y1 / h, x2 / w, y2 / h]

                # ByteTrack ID
                track_id: Optional[int] = None
                if result.boxes.id is not None and i < len(result.boxes.id):
                    track_id = int(result.boxes.id[i])

                rules = apply_rules(category)
                detections.append(
                    Detection(
                        id=str(uuid.uuid4()),
                        label=label,
                        category=category,
                        confidence=confidence,
                        bbox=bbox,
                        track_id=track_id,
                        **rules,
                    )
                )
        return detections

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
