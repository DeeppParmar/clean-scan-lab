"""EcoLens — WebSocket stream router"""
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

FRAME_RATE_LIMIT = 10


@router.websocket("/ws/stream")
async def stream(websocket: WebSocket):
    await websocket.accept()

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

    async def receiver():
        last_time = 0.0
        try:
            while True:
                data = await websocket.receive_bytes()
                now = time.time()
                if now - last_time < (1.0 / FRAME_RATE_LIMIT):
                    continue
                last_time = now
                if frame_queue.full():
                    try:
                        frame_queue.get_nowait()
                    except asyncio.QueueEmpty:
                        pass
                await frame_queue.put(data)
        except WebSocketDisconnect:
            pass

    async def processor():
        from services.rule_engine import apply_rules
        from models.schemas import Detection

        def compute_iou(boxA, boxB):
            xA = max(boxA[0], boxB[0])
            yA = max(boxA[1], boxB[1])
            xB = min(boxA[2], boxB[2])
            yB = min(boxA[3], boxB[3])
            interArea = max(0, xB - xA) * max(0, yB - yA)
            if interArea == 0:
                return 0.0
            boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
            boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
            return interArea / float(boxAArea + boxBArea - interArea)

        tracked_objects = []

        try:
            while True:
                data = await frame_queue.get()
                frame = decode_jpeg_bytes(data)
                if frame is None:
                    continue

                t0 = time.perf_counter()
                detections = await detector.detect(frame, is_stream=True)

                active_tracks = []
                final_detections = []

                for det in detections:
                    best_iou = 0.0
                    best_track = None

                    for track in tracked_objects:
                        iou = compute_iou(det.bbox, track["bbox"])
                        if iou > best_iou:
                            best_iou = iou
                            best_track = track

                    if best_iou > 0.35 and best_track is not None:
                        best_track["bbox"] = det.bbox
                        best_track["history"].append(det.category)
                        if len(best_track["history"]) > 6:
                            best_track["history"].pop(0)
                        best_track["grace"] = 0
                        best_track["last_det"] = det

                        stable_cat = max(set(best_track["history"]), key=best_track["history"].count)
                        if stable_cat != det.category:
                            rules = apply_rules(stable_cat, 1)
                            det.category = stable_cat
                            det.label = stable_cat.capitalize()
                            for k, v in rules.items():
                                setattr(det, k, v)

                        active_tracks.append(best_track)
                        tracked_objects.remove(best_track)
                    else:
                        new_track = {"bbox": det.bbox, "history": [det.category], "grace": 0, "last_det": det}
                        active_tracks.append(new_track)

                    final_detections.append(det)

                for track in tracked_objects:
                    track["grace"] += 1
                    if track["grace"] <= 3:
                        active_tracks.append(track)
                        final_detections.append(track["last_det"])

                tracked_objects = active_tracks
                detections = final_detections

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
