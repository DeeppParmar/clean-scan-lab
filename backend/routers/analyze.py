"""
EcoLens — /api/analyze router
POST endpoint that runs the full scan pipeline.
"""
from __future__ import annotations

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

    # ── 1. Decode base64 ────────────────────────────────────────────────────
    try:
        image_bytes, image = decode_base64_image(body.image)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not decode image: {exc}") from exc

    # ── 2. Security validation ───────────────────────────────────────────────
    validate_image(image_bytes)

    # ── 3. Run detector ──────────────────────────────────────────────────────
    try:
        detections = await detector.detect(image)
    except Exception as exc:
        logger.exception(f"Model inference failed [{scan_id}]")
        raise HTTPException(status_code=500, detail="Model inference failed") from exc

    # ── 4. No-detection guard ────────────────────────────────────────────────
    if not detections:
        logger.bind(event="request_rejected", reason="no_detections").info(
            f"No detections above threshold [{scan_id}]"
        )
        raise HTTPException(
            status_code=422, detail="No objects detected above confidence threshold"
        )

    # ── 5. Eco-score + aggregation ───────────────────────────────────────────
    eco_score = calculate_eco_score(detections)
    category_counts = Counter(d.category for d in detections)
    dominant_category = category_counts.most_common(1)[0][0]
    dominant_count = category_counts[dominant_category]
    object_counts = dict(category_counts)

    # ── 6. Annotate result image & upload to Supabase ────────────────────────
    annotated = annotate_image(image, detections)
    annotated_bytes = encode_image_to_jpeg_bytes(annotated)
    image_url = await upload_image_to_storage(
        annotated_bytes, scan_id, settings.scan_results_bucket, "result.jpg"
    )

    # ── 7. Heatmaps (fire as background if slow, else inline) ────────────────
    latency_so_far = (time.perf_counter() - t_start) * 1000
    heatmap_urls: dict[str, str] = {}

    async def _generate_and_persist_heatmaps():
        nonlocal heatmap_urls
        heatmap_urls = await generate_heatmaps(image, detections, scan_id)
        # Update DB record with heatmap paths
        from database import get_supabase
        get_supabase().table("scan_records").update(
            {"heatmap_paths_json": heatmap_urls}
        ).eq("id", scan_id).execute()

    if latency_so_far > 150:
        # Offload to background — client gets response immediately
        background_tasks.add_task(_generate_and_persist_heatmaps)
    else:
        heatmap_urls = await generate_heatmaps(image, detections, scan_id)

    latency_ms = round((time.perf_counter() - t_start) * 1000, 1)

    # ── 8. Persist to Supabase ───────────────────────────────────────────────
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

    # ── 9. Structured log ─────────────────────────────────────────────────────
    logger.info(
        "scan_complete",
        extra={
            "event": "scan_complete",
            "scan_id": scan_id,
            "latency_ms": latency_ms,
            "detection_count": len(detections),
            "dominant_category": dominant_category,
            "eco_score": eco_score,
            "heatmap_count": len(heatmap_urls),
            "timestamp": now.isoformat() + "Z",
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
