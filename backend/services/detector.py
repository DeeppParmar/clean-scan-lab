"""
EcoLens — Waste Classifier Service
Singleton — loaded ONCE via FastAPI lifespan, never reloaded.
Inference runs in ThreadPoolExecutor so the event loop stays free.

Uses YOLOv8 (yolov8n.pt) for localization (finding generic objects).
Each cropped object is then classified by a fine-tuned MobileNetV2
(12 waste-specific classes).
"""
from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
from uuid import uuid4

import numpy as np
import torch
import torchvision.models as models
from torchvision import transforms
from torch import nn
from PIL import Image
import cv2

from loguru import logger
from ultralytics import YOLO

from config import settings
from models.schemas import Detection
from services.rule_engine import apply_rules
from utils.label_map import normalize_category
from utils.image_utils import resize_image


class DetectorService:
    """Singleton pipeline: YOLO (localization) + MobileNetV2 (classification)."""

    def __init__(self) -> None:
        self._yolo: Optional[YOLO] = None
        self._classifier: Optional[torch.nn.Module] = None
        self._class_names: list[str] = []
        self._transform = None
        self._device = None
        self._executor = ThreadPoolExecutor(max_workers=2)
        self.is_loaded: bool = False

    # ─── Public ──────────────────────────────────────────────────────────────

    def load(self) -> None:
        """
        Called ONCE inside FastAPI lifespan startup.
        Loads generic YOLOv8 for localization and fine-tuned MobileNetV2 for classification.
        """
        import json
        import os

        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # 1. Load YOLO for bounding boxes
        logger.info(f"Loading YOLO localization model: yolov8n.pt")
        self._yolo = YOLO("yolov8n.pt")

        # 2. Load custom MobileNetV2 Classifier
        classes_path = "waste_classifier_classes.json"
        
        # Load classes if available, otherwise fallback to default list
        if os.path.exists(classes_path):
            with open(classes_path, "r") as f:
                self._class_names = json.load(f)
            logger.info(f"Loaded {len(self._class_names)} custom classes for MobileNet")
        else:
            logger.warning(f"Could not find {classes_path}, using default classes")
            self._class_names = [
                "battery", "biological", "brown-glass", "cardboard", "clothes",
                "green-glass", "metal", "paper", "plastic", "shoes", "trash", "white-glass"
            ]

        self._classifier = models.mobilenet_v2(weights=None)
        self._classifier.classifier = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(self._classifier.last_channel, 512),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(512, len(self._class_names))
        )
        
        weights_path = "waste_classifier.pth"
        if os.path.exists(weights_path):
             self._classifier.load_state_dict(
                 torch.load(weights_path, map_location=self._device)
             )
             logger.info(f"Successfully loaded MobileNetV2 weights from {weights_path}")
        else:
             logger.warning(f"CRITICAL: {weights_path} not found! MobileNet will output random predictions until trained.")

        self._classifier.to(self._device)
        self._classifier.eval()

        self._transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])

        # Warm-up
        dummy = np.zeros((640, 640, 3), dtype=np.uint8)
        self._yolo(dummy, verbose=False)
        self.is_loaded = True
        logger.info("Two-stage waste detection pipeline ready ✓")

    @property
    def model(self) -> YOLO:
        if self._yolo is None:
            raise RuntimeError("DetectorService.load() has not been called")
        return self._yolo

    @property
    def classifier(self) -> torch.nn.Module:
        """Access the MobileNetV2 model (used by heatmap service)."""
        if self._classifier is None:
            raise RuntimeError("DetectorService.load() has not been called")
        return self._classifier

    @property
    def device(self) -> torch.device:
        if self._device is None:
            raise RuntimeError("DetectorService.load() has not been called")
        return self._device

    @property
    def transform(self):
        return self._transform

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

        # Resize image for YOLO
        img_for_yolo = resize_image(image, max_size=640)
        h, w = img_for_yolo.shape[:2]
        
        # Original image dimensions for extracting proper crops
        orig_h, orig_w = image.shape[:2]
        scale_x = orig_w / w
        scale_y = orig_h / h

        # STAGE 1: YOLO finds bounding boxes 
        # Extremely low YOLO confidence stringency to ensure maximum object recall. 
        # We rely entirely on MobileNetV2 downstream to sort valid rubbish from noise.
        # iou=0.8 and agnostic_nms=False to prevent deletion of items stacked inside/on top of each other
        results = self._yolo(
            img_for_yolo, conf=0.04, iou=0.8, agnostic_nms=False, verbose=False
        )

        detections: list[Detection] = []
        valid_items = []
        category_counts = {}

        for result in results:
            for i, box in enumerate(result.boxes):
                x1, y1, x2, y2 = box.xyxy[0].tolist()

                # Area filter: discard detections covering < 0.2% of image
                # Setting this extremely low captures small elements like pills/lids in cluttered bins
                area_ratio = ((x2 - x1) * (y2 - y1)) / (w * h)
                if area_ratio < 0.002:
                    continue
                
                # Scale coordinates back to original image size for cropping
                orig_x1, orig_y1 = int(x1 * scale_x), int(y1 * scale_y)
                orig_x2, orig_y2 = int(x2 * scale_x), int(y2 * scale_y)
                
                # Ensure coordinates are within bounds
                orig_x1, orig_y1 = max(0, orig_x1), max(0, orig_y1)
                orig_x2, orig_y2 = min(orig_w, orig_x2), min(orig_h, orig_y2)

                # Expand crop slightly (10%) to give MobileNet context
                dw = int((orig_x2 - orig_x1) * 0.1)
                dh = int((orig_y2 - orig_y1) * 0.1)
                orig_x1 = max(0, orig_x1 - dw)
                orig_y1 = max(0, orig_y1 - dh)
                orig_x2 = min(orig_w, orig_x2 + dw)
                orig_y2 = min(orig_h, orig_y2 + dh)

                # STAGE 2: Crop + classify with MobileNet
                crop = image[orig_y1:orig_y2, orig_x1:orig_x2]
                if crop.size == 0 or crop.shape[0] == 0 or crop.shape[1] == 0:
                    continue

                pil_img = Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))
                tensor = self._transform(pil_img).unsqueeze(0).to(self._device)

                with torch.no_grad():
                    logits = self._classifier(tensor)
                    probs = torch.softmax(logits, dim=1)
                    confidence, idx = probs.max(1)
                
                confidence_val = confidence.item()
                raw_category = self._class_names[idx.item()]
                
                # HEURISTIC: Prevent MobileNet from hallucinating "clothes/shoes" on crumpled plastic wrappers
                if raw_category in ["clothes", "shoes", "textile"]:
                    if confidence_val < 0.95:
                        raw_category = "plastic"
                
                # Only keep if classifier is confident
                if confidence_val < settings.classifier_conf:
                    continue
                
                # Map raw category from MobileNet to standard categories used by rule_engine
                category, label = normalize_category(raw_category)
                
                category_counts[category] = category_counts.get(category, 0) + 1
                
                # Normalize bounding box for API output (0.0 to 1.0)
                norm_bbox = [x1 / w, y1 / h, x2 / w, y2 / h]
                valid_items.append((result, i, confidence_val, norm_bbox, category, label))

        # Build Detection objects with count-aware rules
        for result, i, confidence_val, norm_bbox, category, label in valid_items:
            rules = apply_rules(category, category_counts[category])
            detections.append(
                Detection(
                    id=str(uuid4()),
                    label=label,
                    category=category,
                    confidence=confidence_val,
                    bbox=norm_bbox,
                    mask_points=None,
                    **rules,
                )
            )

        logger.debug(f"Inference complete — {len(detections)} detections")
        return detections


# Module-level singleton
detector = DetectorService()
