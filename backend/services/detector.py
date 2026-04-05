"""
EcoLens — Hybrid Visual Detector (YOLO + MobileNetV2)
"""

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

    def load(self) -> None:
        """Load YOLO for localization and fine-tuned MobileNetV2 for classification."""
        import json
        import os

        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        logger.info("Model loading wait...")
        logger.info(f"Loading YOLO localization model: yolov8n.pt")
        self._yolo = YOLO("yolov8n.pt")

        classes_path = "waste_classifier_classes.json"
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
             logger.warning(f"CRITICAL: {weights_path} not found!")

        self._classifier.to(self._device)
        self._classifier.eval()

        if self._device.type == "cuda":
            logger.info("Enabling FP16 half-precision for GPU")
            self._classifier.half()

        self._transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])

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

    async def detect(self, image: np.ndarray, is_stream: bool = False) -> list[Detection]:
        """Non-blocking inference via ThreadPoolExecutor."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor, self._run_inference, image, is_stream
        )

    def _run_inference(self, image: np.ndarray, is_stream: bool = False) -> list[Detection]:
        img_for_yolo = resize_image(image, max_size=640)
        h, w = img_for_yolo.shape[:2]
        orig_h, orig_w = image.shape[:2]
        scale_x = orig_w / w
        scale_y = orig_h / h

        yolo_conf = 0.12 if is_stream else 0.08
        results = self._yolo(
            img_for_yolo, conf=yolo_conf, iou=0.55, agnostic_nms=True,
            half=(self._device.type == "cuda"), verbose=False
        )

        detections: list[Detection] = []
        valid_items = []
        category_counts = {}
        batch_tensors = []
        box_metadata = []

        for result in results:
            for i, box in enumerate(result.boxes):
                if int(box.cls[0].item()) == 0:
                    continue
                x1, y1, x2, y2 = box.xyxy[0].tolist()

                area_ratio = ((x2 - x1) * (y2 - y1)) / (w * h)
                if area_ratio < 0.002 or area_ratio > 0.85:
                    continue

                orig_x1, orig_y1 = int(x1 * scale_x), int(y1 * scale_y)
                orig_x2, orig_y2 = int(x2 * scale_x), int(y2 * scale_y)
                orig_x1, orig_y1 = max(0, orig_x1), max(0, orig_y1)
                orig_x2, orig_y2 = min(orig_w, orig_x2), min(orig_h, orig_y2)

                dw = int((orig_x2 - orig_x1) * 0.1)
                dh = int((orig_y2 - orig_y1) * 0.1)
                orig_x1 = max(0, orig_x1 - dw)
                orig_y1 = max(0, orig_y1 - dh)
                orig_x2 = min(orig_w, orig_x2 + dw)
                orig_y2 = min(orig_h, orig_y2 + dh)

                crop = image[orig_y1:orig_y2, orig_x1:orig_x2]
                if crop.size == 0 or crop.shape[0] == 0 or crop.shape[1] == 0:
                    continue

                pil_img = Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))
                tensor = self._transform(pil_img).unsqueeze(0).to(self._device)
                if self._device.type == "cuda":
                    tensor = tensor.half()

                yolo_class_id = int(box.cls[0].item())
                yolo_conf_val = float(box.conf[0].item())
                batch_tensors.append(tensor)
                box_metadata.append((result, i, x1, y1, x2, y2, yolo_class_id, yolo_conf_val))

        if not batch_tensors:
            logger.debug("Inference complete — 0 detections")
            return []

        batch = torch.cat(batch_tensors, dim=0)
        with torch.no_grad():
            logits = self._classifier(batch)
            probs = torch.softmax(logits, dim=1)
            num_classes = len(self._class_names)
            k = min(5, num_classes)
            topk_vals, topk_indices = probs.topk(k, dim=1)

        for j, (result, i, x1, y1, x2, y2, yolo_class_id, yolo_conf_val) in enumerate(box_metadata):
            confidence_val = topk_vals[j][0].item()
            raw_category = self._class_names[topk_indices[j][0].item()]

            # Structural overrides using YOLO COCO classes
            if yolo_class_id in [63, 64, 65, 66, 67] and yolo_conf_val > 0.25:
                if raw_category in ["clothes", "shoes", "textile", "general", "trash"]:
                    raw_category = "battery"
                    confidence_val = max(confidence_val, 0.85)

            elif 52 <= yolo_class_id <= 61 and yolo_conf_val > 0.30:
                if raw_category not in ["clothes", "shoes", "textile", "metal", "glass", "white-glass", "green-glass", "brown-glass", "battery"]:
                    raw_category = "biological"
                    confidence_val = max(confidence_val, 0.95)

            elif yolo_class_id == 40 and yolo_conf_val > 0.25:
                if raw_category not in ["white-glass", "green-glass", "brown-glass"]:
                    raw_category = "white-glass"
                confidence_val = max(confidence_val, 0.90)

            elif yolo_class_id in [39, 41] and yolo_conf_val > 0.25:
                valid_materials = ["plastic", "glass", "white-glass", "green-glass", "brown-glass", "metal", "paper"]
                if raw_category not in valid_materials:
                    for r_rank in range(1, k):
                        alt_cat = self._class_names[topk_indices[j][r_rank].item()]
                        if alt_cat in valid_materials:
                            raw_category = alt_cat
                            confidence_val = max(0.40, topk_vals[j][r_rank].item() + 0.3)
                            break
                    else:
                        raw_category = "plastic"
                elif raw_category in ["glass", "white-glass", "green-glass", "brown-glass", "plastic"]:
                    confidence_val = min(0.98, confidence_val + 0.35)

            elif raw_category in ["metal", "battery", "trash"]:
                confidence_val = min(0.96, confidence_val + 0.35)

            elif raw_category in ["clothes", "shoes", "textile"] and confidence_val < 0.85:
                if k > 1:
                    second_cat = self._class_names[topk_indices[j][1].item()]
                    second_conf = topk_vals[j][1].item()
                    if second_cat == "plastic":
                        raw_category = "plastic"
                        confidence_val = max(0.20, second_conf)
                    else:
                        raw_category = "plastic"
                else:
                    raw_category = "plastic"

            min_conf = max(0.20, settings.classifier_conf) if is_stream else settings.classifier_conf
            if confidence_val < min_conf:
                continue

            category, label = normalize_category(raw_category)
            category_counts[category] = category_counts.get(category, 0) + 1
            norm_bbox = [x1 / w, y1 / h, x2 / w, y2 / h]
            valid_items.append((result, i, confidence_val, norm_bbox, category, label))

        for det_idx, (result, i, confidence_val, norm_bbox, category, label) in enumerate(valid_items):
            rules = apply_rules(category, category_counts[category])
            detections.append(
                Detection(
                    id=f"{category}_{det_idx}",
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


detector = DetectorService()
