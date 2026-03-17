"""
EcoLens — /api/stats router
"""
from __future__ import annotations

from fastapi import APIRouter

from models.schemas import DashboardStats
from services.analytics import get_stats

router = APIRouter()


@router.get("/stats", response_model=DashboardStats)
async def stats() -> DashboardStats:
    """Dashboard statistics: totals, trends, category breakdown."""
    return await get_stats()
