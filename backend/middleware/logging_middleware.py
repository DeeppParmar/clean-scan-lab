"""
EcoLens — Structured Logging Middleware (loguru)
Intercepts every request/response to emit JSON-serialised log records.
"""
from __future__ import annotations

import sys
import time

from fastapi import Request
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


def configure_logging() -> None:
    """Called once at startup to configure loguru sinks."""
    logger.remove()
    # Human-readable to stdout in dev, JSON in prod
    logger.add(sys.stdout, serialize=True, level="INFO", enqueue=True)
    logger.add(
        "logs/ecolens.log",
        serialize=True,
        level="INFO",
        rotation="10 MB",
        retention="7 days",
        enqueue=True,
    )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs timing, status, and path for every HTTP request."""

    async def dispatch(self, request: Request, call_next) -> Response:
        t0 = time.perf_counter()
        response = await call_next(request)
        latency_ms = round((time.perf_counter() - t0) * 1000, 1)

        logger.info(
            "http_request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "latency_ms": latency_ms,
                "client_ip": request.client.host if request.client else "unknown",
            },
        )
        return response
