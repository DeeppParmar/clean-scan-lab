"""
EcoLens — YOLOv8 Detector Service
Singleton — loaded ONCE via FastAPI lifespan, never reloaded.
Detection runs in ThreadPoolExecutor so the event loop stays free.
"""
from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
from uuid import uuid4

import numpy as np
from loguru import logger
from ultralytics import YOLO

from config import settings
from models.schemas import Detection
from services.rule_engine import apply_rules
from utils.label_map import LABEL_MAP
from utils.image_utils import resize_image

# Only these COCO class indices make sense as waste detections.
# Everything else (person, car, banana, etc.) is silently dropped.
VALID_WASTE_CLASSES: frozenset[int] = frozenset(LABEL_MAP.keys())


class DetectorService:
    """Singleton detector. Call load() once at startup, never again."""

    def __init__(self) -> None:
        self._model: Optional[YOLO] = None
        self._executor = ThreadPoolExecutor(max_workers=2)
        self.is_loaded: bool = False

    # ─── Public ──────────────────────────────────────────────────────────────

    def load(self) -> None:
        """
        Called ONCE inside FastAPI lifespan startup.
        Loads YOLOv8n-seg, switches to half precision, and runs a warm-up pass
        so the first real request has no cold-start latency.
        """
        logger.info("Loading YOLOv8n-seg model…")
        self._model = YOLO(settings.model_path)


        # Warm-up: one dummy pass to avoid first-request cold start
        dummy = np.zeros((640, 640, 3), dtype=np.uint8)
        self._model(dummy, verbose=False)
        self.is_loaded = True
        logger.info("YOLOv8n-seg ready ✓")

    @property
    def model(self) -> YOLO:
        if self._model is None:
            raise RuntimeError("DetectorService.load() has not been called")
        return self._model

    async def detect(self, image: np.ndarray) -> list[Detection]:
        """
        Non-blocking: offloads inference to ThreadPoolExecutor.
        FastAPI event loop never blocks.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor, self._run_inference, image
        )

    # ─── Internal inference (runs in worker thread) ───────────────────────────

    def _run_inference(self, image: np.ndarray) -> list[Detection]:
        image = resize_image(image, max_size=640)
        results = self._model(
            image, conf=settings.yolo_conf, iou=settings.yolo_iou, verbose=False
        )

        detections: list[Detection] = []
        h, w = image.shape[:2]

        for result in results:
            for i, box in enumerate(result.boxes):
                confidence = float(box.conf[0])

                # Area filter: discard detections covering < 1% of image
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                area_ratio = ((x2 - x1) * (y2 - y1)) / (w * h)
                if area_ratio < 0.01:
                    continue

                cls_idx = int(box.cls[0])

                # Whitelist filter: skip any COCO class that isn't waste
                if cls_idx not in VALID_WASTE_CLASSES:
                    continue

                category, label = LABEL_MAP.get(cls_idx, ("unknown", "Unknown Object"))

                # Normalise bbox to 0–1
                bbox = [x1 / w, y1 / h, x2 / w, y2 / h]

                # Mask polygon points (normalised) from segmentation model
                mask_points = None
                if result.masks is not None and i < len(result.masks.xy):
                    pts = result.masks.xy[i].tolist()
                    mask_points = [[p[0] / w, p[1] / h] for p in pts]

                rules = apply_rules(category)
                detections.append(
                    Detection(
                        id=str(uuid4()),
                        label=label,
                        category=category,
                        confidence=confidence,
                        bbox=bbox,
                        mask_points=mask_points,
                        **rules,
                    )
                )

        logger.debug(f"Inference complete — {len(detections)} detections")
        return detections


# Module-level singleton
detector = DetectorService()
