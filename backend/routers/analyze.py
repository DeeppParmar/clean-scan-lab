"""EcoLens — /api/analyze router"""
import time
import uuid
from collections import Counter
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from loguru import logger
from slowapi.errors import RateLimitExceeded

from config import settings
from database import insert_scan_record, upload_image_to_storage
from middleware.security import limiter, validate_image
from models.schemas import AnalyzeRequest, ScanResult
from services.detector import detector
from services.eco_scorer import calculate_eco_score
from services.heatmap import generate_heatmaps
from utils.image_utils import (
    annotate_image,
    decode_base64_image,
    encode_image_to_jpeg_bytes,
)

router = APIRouter()


@router.post("/analyze", response_model=ScanResult)
@limiter.limit(settings.analyze_rate_limit)
async def analyze(
    request: Request,
    body: AnalyzeRequest,
    background_tasks: BackgroundTasks,
) -> ScanResult:
    t_start = time.perf_counter()
    scan_id = str(uuid.uuid4())
    now = datetime.utcnow()

    try:
        image_bytes, image = decode_base64_image(body.image)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not decode image: {exc}") from exc

    validate_image(image_bytes)

    try:
        detections = await detector.detect(image)
    except Exception as exc:
        logger.exception(f"Model inference failed [{scan_id}]")
        raise HTTPException(status_code=500, detail="Model inference failed") from exc

    if not detections:
        raise HTTPException(status_code=422, detail="No objects detected above confidence threshold")

    eco_score = calculate_eco_score(detections)
    category_counts = Counter(d.category for d in detections)
    categories = [d.category for d in detections]
    unique = set(categories)

    if len(unique) > 1:
        dominant_category = "mixed"
        dominant_count = len(detections)
    else:
        dominant_category = categories[0]
        dominant_count = len(categories)

    object_counts = dict(category_counts)

    annotated = annotate_image(image, detections)
    annotated_bytes = encode_image_to_jpeg_bytes(annotated)
    try:
        image_url = await upload_image_to_storage(
            annotated_bytes, scan_id, settings.scan_results_bucket, "result.jpg"
        )
    except Exception as exc:
        logger.warning(f"Storage upload failed [{scan_id}], continuing without image: {exc}")
        image_url = ""

    latency_so_far = (time.perf_counter() - t_start) * 1000
    heatmap_urls: dict[str, str] = {}

    async def _generate_and_persist_heatmaps():
        nonlocal heatmap_urls
        heatmap_urls = await generate_heatmaps(image, detections, scan_id)
        from database import get_supabase
        get_supabase().table("scan_records").update(
            {"heatmap_paths_json": heatmap_urls}
        ).eq("id", scan_id).execute()

    if latency_so_far > 150:
        background_tasks.add_task(_generate_and_persist_heatmaps)
    else:
        heatmap_urls = await generate_heatmaps(image, detections, scan_id)

    latency_ms = round((time.perf_counter() - t_start) * 1000, 1)

    record = {
        "id": scan_id,
        "timestamp": now.isoformat(),
        "image_path": image_url,
        "heatmap_paths_json": heatmap_urls,
        "detections_json": [d.model_dump() for d in detections],
        "dominant_category": dominant_category,
        "eco_score": eco_score,
        "object_counts_json": object_counts,
        "latency_ms": latency_ms,
    }
    await insert_scan_record(record)

    logger.info(
        "scan_complete",
        extra={
            "event": "scan_complete",
            "scan_id": scan_id,
            "latency_ms": latency_ms,
            "detection_count": len(detections),
            "dominant_category": dominant_category,
            "eco_score": eco_score,
        },
    )

    return ScanResult(
        scan_id=scan_id,
        timestamp=now,
        image_url=image_url,
        heatmap_urls=heatmap_urls,
        detections=detections,
        dominant_category=dominant_category,
        dominant_count=dominant_count,
        eco_score=eco_score,
        object_counts=object_counts,
        latency_ms=latency_ms,
    )
