"""
EcoLens — WebSocket stream router
Implements producer/consumer pattern with client-side frame queue.
ByteTrack tracker is per-connection (isolated state).
"""
import asyncio
import time
import uuid
from collections import Counter

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

from models.schemas import StreamResult
from services.eco_scorer import calculate_eco_score
from services.tracker import active_session_count, create_session, remove_session
from services.detector import detector
from utils.image_utils import decode_jpeg_bytes

router = APIRouter()

FRAME_RATE_LIMIT = 10  # Max fps to process from client


@router.websocket("/ws/stream")
async def stream(websocket: WebSocket):
    await websocket.accept()

    # ── Connection capacity check ────────────────────────────────────────────
    if active_session_count() >= 4:
        await websocket.send_json(
            {"error": "Server is at capacity (max 4 concurrent stream sessions). Try again later."}
        )
        await websocket.close(code=1013)
        return

    tracker = create_session()
    if tracker is None:
        await websocket.close(code=1013)
        return

    frame_queue: asyncio.Queue[bytes] = asyncio.Queue(maxsize=2)
    logger.info(f"WebSocket stream opened [{tracker.id}]")

    # ── Frame receiver ────────────────────────────────────────────────────────
    async def receiver():
        last_time = 0.0
        try:
            while True:
                data = await websocket.receive_bytes()
                now = time.time()
                # Rate-limit incoming frames
                if now - last_time < (1.0 / FRAME_RATE_LIMIT):
                    continue
                last_time = now
                # Backpressure: drop oldest if queue full
                if frame_queue.full():
                    try:
                        frame_queue.get_nowait()
                    except asyncio.QueueEmpty:
                        pass
                await frame_queue.put(data)
        except WebSocketDisconnect:
            pass

    # ── Frame processor ────────────────────────────────────────────────────────
    async def processor():
        try:
            while True:
                data = await frame_queue.get()
                frame = decode_jpeg_bytes(data)
                if frame is None:
                    continue

                t0 = time.perf_counter()
                
                # Use the optimized robust YOLO + MobileNet batch inference pipeline
                detections = await detector.detect(frame)
                
                latency_ms = round((time.perf_counter() - t0) * 1000, 1)

                eco_score = calculate_eco_score(detections)
                if detections:
                    categories = [d.category for d in detections]
                    unique = set(categories)
                    dominant_category = "mixed" if len(unique) > 1 else categories[0]
                else:
                    dominant_category = None

                result = StreamResult(
                    frame_id=str(uuid.uuid4()),
                    detections=detections,
                    eco_score=eco_score,
                    dominant_category=dominant_category,
                    latency_ms=latency_ms,
                )
                await websocket.send_json(result.model_dump())
        except WebSocketDisconnect:
            pass

    try:
        await asyncio.gather(receiver(), processor())
    except WebSocketDisconnect:
        pass
    finally:
        remove_session(tracker)
        logger.info(f"WebSocket stream closed [{tracker.id}]")
