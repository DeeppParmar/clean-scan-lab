"""
EcoLens — Pydantic v2 Schemas
Request / Response models used across routers and services.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ─── Core Detection ──────────────────────────────────────────────────────────

class Detection(BaseModel):
    id: str
    label: str
    category: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    bbox: list[float] = Field(..., min_length=4, max_length=4)
    mask_points: Optional[list[list[float]]] = None
    track_id: Optional[int] = None

    # From rule engine
    recyclable: bool = False
    bin_color: str = "black"
    disposal_instructions: str = ""
    suggestion: str = ""
    action: str = "Dispose"
    hazardous: bool = False


# ─── Scan Result ─────────────────────────────────────────────────────────────

class ScanResult(BaseModel):
    scan_id: str
    timestamp: datetime
    image_url: str
    heatmap_urls: dict[str, str] = {}
    detections: list[Detection] = []
    dominant_category: Optional[str] = None
    dominant_count: int = 0
    eco_score: float = 0.0
    object_counts: dict[str, int] = {}
    latency_ms: float = 0.0


class ScanSummary(BaseModel):
    """Lightweight version for history listing — no mask points."""
    scan_id: str
    timestamp: datetime
    image_url: str
    dominant_category: Optional[str] = None
    eco_score: float = 0.0
    object_counts: dict[str, int] = {}
    latency_ms: float = 0.0


# ─── Request ─────────────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    image: str = Field(..., description="Base64-encoded JPEG/PNG/WebP image")


# ─── Stats / Dashboard ───────────────────────────────────────────────────────

class DailyPoint(BaseModel):
    date: str
    scan_count: int
    avg_eco_score: float


class DashboardStats(BaseModel):
    total_scans: int
    total_today: int
    top_category: Optional[str]
    avg_eco_score: float
    sorted_correctly_pct: float
    category_distribution: dict[str, int] = {}
    daily_trend: list[DailyPoint] = []


# ─── Health ──────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    db_connected: bool


# ─── Stream ──────────────────────────────────────────────────────────────────

class StreamResult(BaseModel):
    frame_id: str
    detections: list[Detection] = []
    eco_score: float = 0.0
    dominant_category: Optional[str] = None
    latency_ms: float = 0.0
