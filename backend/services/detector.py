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
                "battery", "biological", "cardboard", "clothes",
                "glass", "metal", "paper", "plastic", "shoes", "trash"
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

    def _is_metal_material(self, crop_bgr: np.ndarray) -> bool:
        """
        Universal metal material detector.
        Works on cans (crushed or intact), foil, cutlery, 
        metal containers, pipes — any metal regardless of color or shape.
        Based on material properties: specularity pattern, 
        surface texture, local contrast variance.
        """
        gray = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2HSV)
        h, w = gray.shape[:2]

        # --- Signal 1: Specular Adjacency ---
        # Metal creates bright hotspots directly next to dark areas
        # This bright-dark transition is the physical signature of hard reflective surfaces
        v = hsv[:, :, 2].astype(np.float32)
        bright_mask = v > 210
        dark_mask = v < 60
        # Dilate both masks slightly and check overlap proximity
        kernel = np.ones((5, 5), np.uint8)
        bright_dilated = cv2.dilate(bright_mask.astype(np.uint8), kernel)
        dark_dilated = cv2.dilate(dark_mask.astype(np.uint8), kernel)
        adjacency_map = bright_dilated & dark_dilated
        specular_adjacency_ratio = np.sum(adjacency_map) / adjacency_map.size
        has_specular_adjacency = specular_adjacency_ratio > 0.04

        # --- Signal 2: Local Block Contrast Variance ---
        # Metal lighting varies dramatically block to block
        # Organic/paper/textile are more tonally uniform across blocks
        block_size = max(8, min(h, w) // 8)
        block_contrasts = []
        for row in range(0, h - block_size, block_size):
            for col in range(0, w - block_size, block_size):
                block = gray[row:row+block_size, col:col+block_size]
                block_contrasts.append(float(block.max()) - float(block.min()))
        
        if block_contrasts:
            contrast_variance = np.std(block_contrasts)
            # High variance = some blocks very bright, some very dark = metal lighting
            has_high_block_variance = contrast_variance > 40
        else:
            has_high_block_variance = False

        # --- Signal 3: Edge Sharpness (Laplacian) ---
        # Metal surfaces produce very sharp, well-defined edges
        # Organic waste edges are softer and more irregular
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        laplacian_var = laplacian.var()
        # Metal: high laplacian variance from sharp reflective edges
        has_sharp_edges = laplacian_var > 300

        # --- Signal 4: Non-organic dominant color ---
        # Veto organic hue range — if dominant color is clearly non-food
        # (red, blue, silver, black) it supports metal classification
        sat = hsv[:, :, 1]
        hue = hsv[:, :, 0]
        # Organic hue range: greens/yellows/browns (10-85)
        organic_hue_mask = (hue > 10) & (hue < 85) & (sat > 50)
        organic_pixel_ratio = np.sum(organic_hue_mask) / organic_hue_mask.size
        # Non-organic and not just background grey
        high_sat_non_organic = (np.sum(sat > 80) / sat.size > 0.15) and organic_pixel_ratio < 0.25
        is_grey_metal = np.mean(sat) < 35 and np.mean(hsv[:,:,2]) > 80
        has_non_organic_color = high_sat_non_organic or is_grey_metal

        signals = (
            int(has_specular_adjacency) +
            int(has_high_block_variance) +
            int(has_sharp_edges) +
            int(has_non_organic_color)
        )

        logger.debug(
            f"Metal check — specular_adj:{has_specular_adjacency} "
            f"block_var:{has_high_block_variance} sharp:{has_sharp_edges} "
            f"color:{has_non_organic_color} → {signals}/4"
        )
        return signals >= 2

    def _hsv_veto(self, crop_bgr: np.ndarray, predicted_category: str) -> Optional[str]:
        hsv = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2HSV)
        warm_mask = ((hsv[:,:,0] > 10) & (hsv[:,:,0] < 45) & (hsv[:,:,1] > 60))
        is_warm_organic = (np.sum(warm_mask) / warm_mask.size) > 0.25
        is_metal = self._is_metal_material(crop_bgr)

        if predicted_category in {"biological", "organic", "food"} and is_metal:
            return "metal"

        if predicted_category in {"clothes", "shoes", "textile"} and is_warm_organic:
            return "biological"

        if predicted_category == "metal" and is_warm_organic and not is_metal:
            return "biological"

        return None

    def _run_inference(self, image: np.ndarray, is_stream: bool = False) -> list[Detection]:
        img_for_yolo = resize_image(image, max_size=640)
        h, w = img_for_yolo.shape[:2]
        orig_h, orig_w = image.shape[:2]
        scale_x = orig_w / w
        scale_y = orig_h / h

        yolo_conf = 0.12 if is_stream else 0.08
        results = self._yolo(
            img_for_yolo, conf=yolo_conf, iou=0.40, agnostic_nms=True,
            half=(self._device.type == "cuda"), verbose=False
        )

        raw_boxes = []
        for result in results:
            for box in result.boxes:
                if int(box.cls[0].item()) != 0:
                    raw_boxes.append({
                        "xyxy": box.xyxy[0].tolist(),
                        "cls": int(box.cls[0].item()),
                        "conf": float(box.conf[0].item())
                    })

        # Fallback Dense Pass to catch small or obscured objects
        if not is_stream:
            logger.debug("Running dense fallback pass (sliding window)")
            quads = [
                (0, 0, w//2 + 20, h//2 + 20),
                (w//2 - 20, 0, w, h//2 + 20),
                (0, h//2 - 20, w//2 + 20, h),
                (w//2 - 20, h//2 - 20, w, h)
            ]
            for (qx1, qy1, qx2, qy2) in quads:
                qx1, qy1, qx2, qy2 = max(0, qx1), max(0, qy1), min(w, qx2), min(h, qy2)
                q_img = img_for_yolo[qy1:qy2, qx1:qx2]
                if q_img.size == 0: continue
                q_res = self._yolo(
                    q_img, conf=0.04, iou=0.40, agnostic_nms=True,
                    half=(self._device.type == "cuda"), verbose=False
                )
                for qb in q_res[0].boxes:
                    if int(qb.cls[0].item()) != 0:
                        bx1, by1, bx2, by2 = qb.xyxy[0].tolist()
                        raw_boxes.append({
                            "xyxy": [bx1+qx1, by1+qy1, bx2+qx1, by2+qy1],
                            "cls": int(qb.cls[0].item()),
                            "conf": float(qb.conf[0].item())
                        })
            
            # Simple NMS to merge sliding window overlap
            raw_boxes = sorted(raw_boxes, key=lambda x: x['conf'], reverse=True)
            keep = []
            for box in raw_boxes:
                overlap = False
                for k in keep:
                    ix1, iy1 = max(box['xyxy'][0], k['xyxy'][0]), max(box['xyxy'][1], k['xyxy'][1])
                    ix2, iy2 = min(box['xyxy'][2], k['xyxy'][2]), min(box['xyxy'][3], k['xyxy'][3])
                    iw, ih = max(0, ix2 - ix1), max(0, iy2 - iy1)
                    inter = iw * ih
                    area1 = (box['xyxy'][2] - box['xyxy'][0]) * (box['xyxy'][3] - box['xyxy'][1])
                    area2 = (k['xyxy'][2] - k['xyxy'][0]) * (k['xyxy'][3] - k['xyxy'][1])
                    union = area1 + area2 - inter
                    if union > 0 and (inter / union) > 0.45:
                        overlap = True
                        break
                if not overlap:
                    keep.append(box)
            raw_boxes = keep

        detections: list[Detection] = []
        valid_items = []
        category_counts = {}
        batch_tensors = []
        box_metadata = []

        for i, b in enumerate(raw_boxes):
            x1, y1, x2, y2 = b["xyxy"]

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

            yolo_class_id = b["cls"]
            yolo_conf_val = b["conf"]
            batch_tensors.append(tensor)
            box_metadata.append((None, i, x1, y1, x2, y2, yolo_class_id, yolo_conf_val, crop))

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

        for j, (result, i, x1, y1, x2, y2, yolo_class_id, yolo_conf_val, crop) in enumerate(box_metadata):
            # --- TOP-K VOTING ---
            top_categories = [self._class_names[topk_indices[j][r].item()] for r in range(k)]
            top_confidences = [topk_vals[j][r].item() for r in range(k)]

            vote_scores = {}
            for rank, (cat, conf) in enumerate(zip(top_categories, top_confidences)):
                weight = 1.0 / (rank + 1)  # rank 1 gets full weight, rank 2 gets half, etc.
                vote_scores[cat] = vote_scores.get(cat, 0) + conf * weight

            raw_category = max(vote_scores, key=vote_scores.get)
            confidence_val = top_confidences[0]  # still use top-1 conf for threshold checks

            # Structural overrides using YOLO COCO classes
            if yolo_class_id in [63, 64, 65, 66, 67] and yolo_conf_val > 0.25:
                if raw_category in ["clothes", "shoes", "textile", "general", "trash"]:
                    raw_category = "battery"
                    confidence_val = max(confidence_val, 0.85)

            elif 46 <= yolo_class_id <= 55 and yolo_conf_val > 0.30:
                if raw_category not in ["clothes", "shoes", "textile", "metal", "glass", "battery"]:
                    if not self._is_metal_material(crop):
                        raw_category = "biological"
                        confidence_val = max(confidence_val, 0.95)

            elif yolo_class_id == 40 and yolo_conf_val > 0.25:
                if raw_category != "glass":
                    raw_category = "glass"
                confidence_val = max(confidence_val, 0.90)

            elif yolo_class_id in [39, 41] and yolo_conf_val > 0.25:
                valid_materials = ["plastic", "glass", "metal", "paper"]
                if raw_category not in valid_materials:
                    for r_rank in range(1, k):
                        alt_cat = self._class_names[topk_indices[j][r_rank].item()]
                        if alt_cat in valid_materials:
                            raw_category = alt_cat
                            confidence_val = max(0.40, topk_vals[j][r_rank].item() + 0.3)
                            break
                    else:
                        raw_category = "plastic"
                elif raw_category in ["glass", "plastic"]:
                    confidence_val = min(0.98, confidence_val + 0.35)

            elif raw_category in ["metal", "battery", "trash"]:
                if self._is_metal_material(crop):
                    raw_category = "metal"
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

            ORGANIC_CLASSES = {"biological", "organic", "food"}
            ORGANIC_CONFIDENCE_FLOOR = 0.70

            # Only apply confidence floor if YOLO didn't predict a food class (46-55)
            is_yolo_food = 46 <= yolo_class_id <= 55

            if raw_category in ORGANIC_CLASSES and confidence_val < ORGANIC_CONFIDENCE_FLOOR and not is_yolo_food:
                # Find best non-organic alternative from top-k
                fallback_found = False
                for rank in range(1, k):
                    alt_cat = self._class_names[topk_indices[j][rank].item()]
                    alt_conf = topk_vals[j][rank].item()
                    if alt_cat not in ORGANIC_CLASSES:
                        raw_category = alt_cat
                        confidence_val = alt_conf
                        fallback_found = True
                        break
                if not fallback_found:
                    raw_category = "trash"  # safe fallback
                    confidence_val = 0.50

            # HSV veto check
            veto_result = self._hsv_veto(crop, raw_category)  # call after top-k voting sets raw_category
            if veto_result is not None:
                logger.debug(f"HSV veto fired: {raw_category} → {veto_result}")
                raw_category = veto_result
                confidence_val = max(confidence_val, 0.65)

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
