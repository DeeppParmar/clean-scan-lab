"""
EcoLens — Waste Classifier Service
Singleton — loaded ONCE via FastAPI lifespan, never reloaded.
Inference runs in ThreadPoolExecutor so the event loop stays free.

Uses a fine-tuned MobileNetV2 (12 waste-specific classes) trained on
the garbage_classification dataset.  NO generic COCO YOLO — the classifier
operates on the whole image (or on user-provided crops).
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

from config import settings
from models.schemas import Detection
from services.rule_engine import apply_rules
from utils.label_map import normalize_category
from utils.image_utils import resize_image


class DetectorService:
    """Singleton classifier pipeline: MobileNetV2 whole-image classification."""

    def __init__(self) -> None:
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
        Loads fine-tuned MobileNetV2 for 12-class waste classification.
        """
        import json
        import os

        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # 1. Load class names
        classes_path = "waste_classifier_classes.json"
        if os.path.exists(classes_path):
            with open(classes_path, "r") as f:
                self._class_names = json.load(f)
            logger.info(f"Loaded {len(self._class_names)} classes: {self._class_names}")
        else:
            logger.warning(f"Could not find {classes_path}, using default classes")
            self._class_names = [
                "battery", "biological", "brown-glass", "cardboard", "clothes",
                "green-glass", "metal", "paper", "plastic", "shoes", "trash", "white-glass"
            ]

        # 2. Build MobileNetV2 with matching classifier head
        self._classifier = models.mobilenet_v2(weights=None)
        self._classifier.classifier = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(self._classifier.last_channel, 512),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(512, len(self._class_names)),
        )

        # 3. Load trained weights
        weights_path = "waste_classifier.pth"
        if os.path.exists(weights_path):
            self._classifier.load_state_dict(
                torch.load(weights_path, map_location=self._device)
            )
            logger.info(f"Loaded MobileNetV2 weights from {weights_path}")
        else:
            logger.warning(
                f"CRITICAL: {weights_path} not found! "
                "Run `python train_classifier.py` to train the model first."
            )

        self._classifier.to(self._device)
        self._classifier.eval()

        # 4. Standard ImageNet preprocessing
        self._transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ])

        self.is_loaded = True
        logger.info("Waste classification pipeline ready ✓")

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
        """
        Single-stage whole-image classification.
        The input image IS the waste item to classify.
        """
        h, w = image.shape[:2]

        # Convert BGR numpy → RGB PIL → tensor
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)
        tensor = self._transform(pil_img).unsqueeze(0).to(self._device)

        # Classify
        with torch.no_grad():
            logits = self._classifier(tensor)
            probs = torch.softmax(logits, dim=1)

        # Get top prediction
        confidence_val, idx = probs.max(1)
        confidence_val = confidence_val.item()
        raw_category = self._class_names[idx.item()]

        # Get top-3 for logging
        top3_probs, top3_idx = probs.topk(3, dim=1)
        top3_info = [
            f"{self._class_names[top3_idx[0][i].item()]}: {top3_probs[0][i].item():.2%}"
            for i in range(3)
        ]
        logger.debug(f"Top-3 predictions: {', '.join(top3_info)}")

        # Confidence gate — reject if model is not confident enough
        if confidence_val < 0.40:
            logger.debug(
                f"Low confidence ({confidence_val:.2%}) for '{raw_category}' — "
                "no detection returned"
            )
            return []

        # Map raw category to standardized category + human label
        category, label = normalize_category(raw_category)

        # Build detection — bbox covers the full image
        rules = apply_rules(category, count=1)
        detection = Detection(
            id=str(uuid4()),
            label=label,
            category=category,
            confidence=confidence_val,
            bbox=[0.0, 0.0, 1.0, 1.0],  # full image
            mask_points=None,
            **rules,
        )

        logger.debug(
            f"Classification: {label} ({category}) — "
            f"confidence {confidence_val:.2%}"
        )
        return [detection]


# Module-level singleton
detector = DetectorService()
