"""EcoLens — /api/stats router"""
from fastapi import APIRouter

from models.schemas import DashboardStats
from services.analytics import get_stats

router = APIRouter()


@router.get("/stats", response_model=DashboardStats)
async def stats() -> DashboardStats:
    return await get_stats()
