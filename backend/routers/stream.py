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
        from services.rule_engine import apply_rules
        from models.schemas import Detection
        last_stable_detections: list[Detection] = []
        recent_categories: list[str] = []
        grace_frames: int = 0
        try:
            while True:
                data = await frame_queue.get()
                frame = decode_jpeg_bytes(data)
                if frame is None:
                    continue

                t0 = time.perf_counter()
                
                # Use the optimized robust YOLO + MobileNet batch inference pipeline
                detections = await detector.detect(frame, is_stream=True)
                
                if detections:
                    # Stabilize classifications for single-item frames (common webcam use-case)
                    if len(detections) == 1:
                        cat = detections[0].category
                        recent_categories.append(cat)
                        if len(recent_categories) > 3:
                            recent_categories.pop(0)
                        
                        # Use the mode (most common category over last 3 frames)
                        stable_cat = max(set(recent_categories), key=recent_categories.count)
                        if stable_cat != cat:
                            rules = apply_rules(stable_cat, 1)
                            detections[0].category = stable_cat
                            detections[0].label = stable_cat.capitalize()
                            for k, v in rules.items():
                                setattr(detections[0], k, v)
                    
                    last_stable_detections = detections
                    grace_frames = 0
                else:
                    if grace_frames < 3 and last_stable_detections:
                        # Keep previous detections up to 3 frames to prevent blinking
                        detections = last_stable_detections
                        grace_frames += 1
                    else:
                        last_stable_detections = []
                        recent_categories.clear()
                
                latency_ms = round((time.perf_counter() - t0) * 1000, 1)

                eco_score = calculate_eco_score(detections)
                object_counts = {}
                if detections:
                    categories = [d.category for d in detections]
                    unique = set(categories)
                    dominant_category = "mixed" if len(unique) > 1 else categories[0]
                    object_counts = dict(Counter(categories))
                else:
                    dominant_category = None

                result = StreamResult(
                    frame_id=str(uuid.uuid4()),
                    detections=detections,
                    eco_score=eco_score,
                    dominant_category=dominant_category,
                    object_counts=object_counts,
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
