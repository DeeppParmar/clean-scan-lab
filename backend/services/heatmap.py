"""EcoLens — Grad-CAM Heatmap Generation"""
import io
from typing import Optional

import cv2
import numpy as np
import torch
from loguru import logger
from pytorch_grad_cam import GradCAM
from pytorch_grad_cam.utils.image import show_cam_on_image
from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget
from torchvision import transforms

from database import upload_image_to_storage
from config import settings
from utils.label_map import CATEGORY_TO_CLASS_IDX

_detector = None


def _get_detector():
    global _detector
    if _detector is None:
        from services.detector import detector as _d
        _detector = _d
    return _detector


_preprocess = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


def _preprocess_image(image: np.ndarray) -> torch.Tensor:
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    tensor = _preprocess(rgb)
    return tensor.unsqueeze(0)


async def generate_heatmaps(
    image: np.ndarray,
    detections: list,
    scan_id: str,
) -> dict[str, str]:
    """Generate and upload Grad-CAM heatmaps per detected category."""
    heatmap_urls: dict[str, str] = {}
    categories = {d.category for d in detections}
    det_service = _get_detector()

    for category in categories:
        try:
            class_idx = CATEGORY_TO_CLASS_IDX.get(category)
            if class_idx is None:
                continue

            target_layers = [det_service.classifier.features[-1]]
            cam = GradCAM(model=det_service.classifier, target_layers=target_layers)
            targets = [ClassifierOutputTarget(class_idx)]

            input_tensor = _preprocess_image(image).to(det_service.device)
            if det_service.device.type == "cuda":
                input_tensor = input_tensor.half()
            grayscale_cam = cam(input_tensor=input_tensor, targets=targets)[0]

            img_rgb = cv2.cvtColor(
                cv2.resize(image, (224, 224)), cv2.COLOR_BGR2RGB
            ).astype(np.float32) / 255.0

            visualization = show_cam_on_image(
                img_rgb, grayscale_cam, use_rgb=True,
                colormap=cv2.COLORMAP_JET, image_weight=0.5,
            )

            viz_bgr = cv2.cvtColor(visualization, cv2.COLOR_RGB2BGR)
            _, buf = cv2.imencode(".jpg", viz_bgr, [cv2.IMWRITE_JPEG_QUALITY, 85])
            img_bytes = buf.tobytes()

            filename = f"{category}.jpg"
            public_url = await upload_image_to_storage(
                img_bytes, scan_id, settings.heatmaps_bucket, filename
            )
            heatmap_urls[category] = public_url

        except Exception as exc:
            logger.warning(f"Grad-CAM failed for category '{category}': {exc}")
            continue

    return heatmap_urls
