"""
EcoLens — /api/history router
"""
from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from database import get_scan_record, list_scan_records
from models.schemas import Detection, ScanResult, ScanSummary

router = APIRouter()


@router.get("/history", response_model=list[ScanSummary])
async def get_history(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    category: str | None = Query(None, description="Filter by dominant_category"),
):
    """Paginated scan history (lightweight — no mask points)."""
    records = await list_scan_records(limit=limit, offset=offset, category=category)

    summaries: list[ScanSummary] = []
    for r in records:
        summaries.append(
            ScanSummary(
                scan_id=str(r.get("id", "")),
                timestamp=r.get("timestamp"),  # type: ignore[arg-type]
                image_url=r.get("image_path", ""),
                dominant_category=r.get("dominant_category"),
                eco_score=float(r.get("eco_score") or 0.0),
                object_counts=r.get("object_counts_json") or {},
                latency_ms=float(r.get("latency_ms") or 0.0),
            )
        )
    return summaries


@router.get("/history/{scan_id}", response_model=ScanResult)
async def get_scan(scan_id: str):
    """Full scan detail including mask points."""
    record = await get_scan_record(scan_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Scan '{scan_id}' not found")

    raw_detections = record.get("detections_json") or []
    detections = [Detection(**d) for d in raw_detections]

    return ScanResult(
        scan_id=str(record["id"]),
        timestamp=record["timestamp"],
        image_url=record.get("image_path", ""),
        heatmap_urls=record.get("heatmap_paths_json") or {},
        detections=detections,
        dominant_category=record.get("dominant_category"),
        eco_score=float(record.get("eco_score") or 0.0),
        object_counts=record.get("object_counts_json") or {},
        latency_ms=float(record.get("latency_ms") or 0.0),
    )
