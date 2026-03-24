"""
EcoLens — FastAPI Application Entry Point
Microsoft Sustainability AI Project, 2026

Lifespan manages model startup (once) and graceful shutdown.
"""

import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from config import settings
from database import check_db_health
from middleware.logging_middleware import RequestLoggingMiddleware, configure_logging
from middleware.security import limiter
from models.schemas import HealthResponse
from routers import analyze, history, stats, stream
from services.detector import detector


# ─── Lifespan ─────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: configure logging, load model. Shutdown: nothing to tear down."""
    configure_logging()
    logger.info("EcoLens API starting up…")
    detector.load()       # loads ONCE — singleton, never reloaded
    logger.info("EcoLens API ready ✓")
    yield
    logger.info("EcoLens API shutting down.")


# ─── App Factory ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="EcoLens API",
    description=(
        "Smart Waste Classification & Recycling System — "
        "Microsoft Sustainability AI, 2026"
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── Rate limiter state & error handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS (allow all origins in dev — restrict in prod via env)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Structured request logging
app.add_middleware(RequestLoggingMiddleware)

# ── Static files (served locally for dev; Supabase Storage used for prod)
app.mount("/static", StaticFiles(directory="static"), name="static")


# ─── Routers ──────────────────────────────────────────────────────────────────

app.include_router(analyze.router, prefix="/api", tags=["Analysis"])
app.include_router(history.router, prefix="/api", tags=["History"])
app.include_router(stats.router, prefix="/api", tags=["Statistics"])
app.include_router(stream.router, tags=["Stream"])


# ─── Health endpoint ──────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health() -> HealthResponse:
    """Health check — polled by frontend every 30 s. No auth required."""
    db_ok = await check_db_health()
    return HealthResponse(
        status="ok" if detector.is_loaded and db_ok else "degraded",
        model_loaded=detector.is_loaded,
        db_connected=db_ok,
    )
