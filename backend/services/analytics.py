"""
EcoLens — Analytics Service
Wraps Supabase database helpers to compute dashboard statistics.
"""

from collections import Counter
from datetime import datetime, timedelta, date

from loguru import logger

from database import (
    get_total_scans,
    get_scans_today,
    get_top_category,
    get_avg_eco_score,
    get_category_distribution,
    list_scan_records,
)
from models.schemas import DashboardStats, DailyPoint
from utils.label_map import RECYCLABLE_CATEGORIES


async def get_stats() -> DashboardStats:
    """Compute full dashboard statistics from Supabase."""
    total_scans = await get_total_scans()
    total_today = await get_scans_today()
    top_category = await get_top_category()
    avg_eco_score = await get_avg_eco_score()
    category_distribution = await get_category_distribution()

    # sorted_correctly_pct: % of scans where dominant_category is a recyclable category
    recyclable_count = sum(
        v for k, v in category_distribution.items() if k in RECYCLABLE_CATEGORIES
    )
    sorted_correctly_pct = (
        round((recyclable_count / total_scans) * 100, 1) if total_scans > 0 else 0.0
    )

    daily_trend = await get_daily_trend(days=7)

    return DashboardStats(
        total_scans=total_scans,
        total_today=total_today,
        top_category=top_category,
        avg_eco_score=avg_eco_score,
        sorted_correctly_pct=sorted_correctly_pct,
        category_distribution=category_distribution,
        daily_trend=daily_trend,
    )


async def get_daily_trend(days: int = 7) -> list[DailyPoint]:
    """
    Returns last N days with date, scan_count, avg_eco_score.
    Computed in-memory from Supabase scan_records (avoid RPC dependency).
    """
    today = date.today()
    # Fetch all records in the window
    records = await list_scan_records(limit=10_000, offset=0)

    # Filter to last N days
    cutoff_dt = datetime.utcnow() - timedelta(days=days)

    day_data: dict[str, list[float]] = {}
    for r in records:
        ts_str = r.get("timestamp")
        if not ts_str:
            continue
        try:
            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        except Exception:
            continue

        if ts.replace(tzinfo=None) < cutoff_dt:
            continue

        day_str = ts.date().isoformat()
        eco = r.get("eco_score") or 0.0
        if day_str not in day_data:
            day_data[day_str] = []
        day_data[day_str].append(float(eco))

    trend: list[DailyPoint] = []
    for day_str, scores in sorted(day_data.items(), reverse=True):
        trend.append(
            DailyPoint(
                date=day_str,
                scan_count=len(scores),
                avg_eco_score=round(sum(scores) / len(scores), 1) if scores else 0.0,
            )
        )
    return trend
