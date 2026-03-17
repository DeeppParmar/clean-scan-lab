"""
EcoLens — Database & Storage Layer (Supabase)
Replaces SQLite/SQLAlchemy with Supabase Postgres + Storage Buckets.
"""
from __future__ import annotations

import io
import uuid
from datetime import datetime
from typing import Any

import httpx
from loguru import logger
from supabase import create_client, Client

from config import settings

# ─── Supabase client (service-role for backend writes) ───────────────────────
_supabase: Client | None = None


def get_supabase() -> Client:
    """Return the global Supabase client, initialised lazily."""
    global _supabase
    if _supabase is None:
        _supabase = create_client(settings.supabase_url, settings.supabase_service_key)
    return _supabase


async def check_db_health() -> bool:
    """Ping scan_records table to verify DB connectivity."""
    try:
        client = get_supabase()
        client.table("scan_records").select("id").limit(1).execute()
        return True
    except Exception as exc:
        logger.error(f"DB health check failed: {exc}")
        return False


# ─── Scan Record CRUD ────────────────────────────────────────────────────────

async def insert_scan_record(record: dict[str, Any]) -> dict[str, Any]:
    """Insert a scan record row into scan_records. Returns the inserted row."""
    client = get_supabase()
    data = {
        "id": record.get("id", str(uuid.uuid4())),
        "timestamp": record.get("timestamp", datetime.utcnow().isoformat()),
        "image_path": record.get("image_path"),
        "heatmap_paths_json": record.get("heatmap_paths_json", {}),
        "detections_json": record.get("detections_json", []),
        "dominant_category": record.get("dominant_category"),
        "eco_score": record.get("eco_score"),
        "object_counts_json": record.get("object_counts_json", {}),
        "latency_ms": record.get("latency_ms"),
    }
    resp = client.table("scan_records").insert(data).execute()
    return resp.data[0] if resp.data else data


async def get_scan_record(scan_id: str) -> dict[str, Any] | None:
    """Fetch a single scan record by UUID."""
    client = get_supabase()
    resp = (
        client.table("scan_records")
        .select("*")
        .eq("id", scan_id)
        .maybe_single()
        .execute()
    )
    return resp.data


async def list_scan_records(
    limit: int = 20,
    offset: int = 0,
    category: str | None = None,
) -> list[dict[str, Any]]:
    """Paginated history, optionally filtered by dominant_category."""
    client = get_supabase()
    query = (
        client.table("scan_records")
        .select("id,timestamp,image_path,dominant_category,eco_score,object_counts_json,latency_ms")
        .order("timestamp", desc=True)
        .range(offset, offset + limit - 1)
    )
    if category:
        query = query.eq("dominant_category", category)
    resp = query.execute()
    return resp.data or []


async def get_total_scans() -> int:
    client = get_supabase()
    resp = client.table("scan_records").select("id", count="exact").execute()
    return resp.count or 0


async def get_daily_trend(days: int = 7) -> list[dict[str, Any]]:
    """
    Returns last N days with date, scan_count, avg_eco_score.
    Uses Supabase RPC for date aggregation.
    """
    client = get_supabase()
    # Build via raw SQL through RPC or Postgres function
    query = f"""
        SELECT
            DATE(timestamp) AS date,
            COUNT(*) AS scan_count,
            ROUND(AVG(eco_score)::numeric, 1) AS avg_eco_score
        FROM scan_records
        WHERE timestamp >= NOW() - INTERVAL '{days} days'
        GROUP BY DATE(timestamp)
        ORDER BY DATE(timestamp) DESC
    """
    resp = client.rpc("get_daily_trend", {"days_back": days}).execute()
    # Fallback: use execute_sql approach via httpx
    return resp.data or []


async def get_category_distribution() -> dict[str, int]:
    """COUNT(*) GROUP BY dominant_category across all time."""
    client = get_supabase()
    resp = (
        client.table("scan_records")
        .select("dominant_category")
        .execute()
    )
    distribution: dict[str, int] = {}
    for row in resp.data or []:
        cat = row.get("dominant_category") or "unknown"
        distribution[cat] = distribution.get(cat, 0) + 1
    return distribution


async def get_avg_eco_score() -> float:
    client = get_supabase()
    resp = client.table("scan_records").select("eco_score").execute()
    scores = [r["eco_score"] for r in (resp.data or []) if r.get("eco_score") is not None]
    return round(sum(scores) / len(scores), 1) if scores else 0.0


async def get_scans_today() -> int:
    from datetime import date
    today = date.today().isoformat()
    client = get_supabase()
    resp = (
        client.table("scan_records")
        .select("id", count="exact")
        .gte("timestamp", f"{today}T00:00:00")
        .execute()
    )
    return resp.count or 0


async def get_top_category() -> str | None:
    dist = await get_category_distribution()
    if not dist:
        return None
    return max(dist, key=dist.get)  # type: ignore[arg-type]


# ─── Storage Helpers ─────────────────────────────────────────────────────────

async def upload_image_to_storage(
    image_bytes: bytes,
    scan_id: str,
    bucket: str,
    filename: str,
    content_type: str = "image/jpeg",
) -> str:
    """
    Upload bytes to Supabase Storage bucket.
    Returns the public URL of the uploaded file.
    """
    client = get_supabase()
    path = f"{scan_id}/{filename}"
    try:
        client.storage.from_(bucket).upload(
            path, image_bytes, {"content-type": content_type, "upsert": "true"}
        )
        public_url = client.storage.from_(bucket).get_public_url(path)
        return public_url
    except Exception as exc:
        logger.error(f"Storage upload failed [{bucket}/{path}]: {exc}")
        raise
