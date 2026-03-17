# EcoLens — Smart Waste Classification & Recycling System

> **Microsoft Sustainability AI Project, 2026**  
> Production-ready Python backend — YOLOv8 · FastAPI · Supabase · Grad-CAM

```
╔══════════════════════════════════════════════════════════╗
║                     EcoLens v2.0                         ║
║  Client → [POST /api/analyze] ──► Security Middleware    ║
║              │                      (MIME + Rate Limit)  ║
║              ▼                                           ║
║     DetectorService (YOLOv8n-seg)                        ║
║     ├─ FP16 warm-up singleton                            ║
║     └─ ThreadPoolExecutor (non-blocking)                 ║
║              │                                           ║
║     ┌────────┴────────┐                                  ║
║     │                 │                                  ║
║   EcoScorer v2    HeatmapService                         ║
║   (penalty model) (per-class Grad-CAM)                   ║
║     │                 │                                  ║
║     └────────┬────────┘                                  ║
║              ▼                                           ║
║    Supabase (Postgres + Storage Buckets)                 ║
║              │                                           ║
║           Response → Client                              ║
║                                                          ║
║  WebSocket /ws/stream                                    ║
║  Client → [raw JPEG] → Queue → ByteTrack → JSON back     ║
╚══════════════════════════════════════════════════════════╝
```

## Run in 3 Commands

```bash
git clone https://github.com/your-org/ecolens.git
cd ecolens/backend
pip install -r requirements.txt
uvicorn main:app --reload
```

## Environment Variables

Copy `.env.example` → `.env` and fill in:

| Variable | Description | Required |
|----------|-------------|----------|
| `SUPABASE_URL` | Supabase project URL | ✅ |
| `SUPABASE_KEY` | Supabase anon/public key | ✅ |
| `SUPABASE_SERVICE_KEY` | Supabase service role key (backend writes) | ✅ |
| `MODEL_PATH` | Path to YOLOv8n-seg.pt | default: `yolov8n-seg.pt` |
| `YOLO_CONF` | Detection confidence threshold | default: `0.6` |
| `YOLO_IOU` | NMS IOU threshold | default: `0.5` |
| `MAX_IMAGE_SIZE_MB` | Max upload size in MB | default: `10` |
| `ANALYZE_RATE_LIMIT` | Rate limit for POST /api/analyze | default: `30/minute` |
| `MAX_WS_CONNECTIONS` | Max concurrent WebSocket sessions | default: `4` |
| `SCAN_RESULTS_BUCKET` | Supabase Storage bucket for annotated results | default: `scan-results` |
| `HEATMAPS_BUCKET` | Supabase Storage bucket for Grad-CAM heatmaps | default: `heatmaps` |

## API Reference

FastAPI auto-generates interactive docs at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Endpoints Summary

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/analyze` | Run waste classification on an image |
| `GET` | `/api/history` | Paginated scan history |
| `GET` | `/api/history/{scan_id}` | Full scan detail with masks |
| `GET` | `/api/stats` | Dashboard statistics + 7-day trend |
| `GET` | `/health` | Health check (model + DB status) |
| `WS`  | `/ws/stream` | Real-time video stream with ByteTrack |

## Docker

```bash
docker build -t ecolens:latest .
docker run -p 8000:8000 --env-file .env ecolens:latest
```

## Performance Notes

| Hardware | Expected latency (avg) |
|----------|----------------------|
| CPU (i7 / Ryzen 7) | 300–600 ms |
| CPU (M1/M2 Mac) | 150–300 ms |
| GPU (T4 / A10) | 40–80 ms |
| GPU (RTX 3090+) | 15–40 ms |

> Latency includes: validation + YOLOv8 inference + Grad-CAM + Supabase Storage upload.  
> First request has ~0 cold-start overhead due to FP16 warm-up at startup.

## Project Structure

```
backend/
  main.py                    ← FastAPI app + lifespan
  config.py                  ← pydantic-settings
  database.py                ← Supabase client + Storage helpers
  models/schemas.py          ← Pydantic v2 schemas
  routers/
    analyze.py               ← POST /api/analyze (full pipeline)
    history.py               ← GET /api/history[/{id}]
    stats.py                 ← GET /api/stats
    stream.py                ← WS /ws/stream (ByteTrack)
  services/
    detector.py              ← YOLOv8 singleton (FP16, warm-up)
    tracker.py               ← ByteTrack per-session wrapper
    heatmap.py               ← Per-class Grad-CAM → Supabase
    rule_engine.py           ← Disposal rules per category
    eco_scorer.py            ← Eco-score v2 (penalty model)
    analytics.py             ← Dashboard stats + daily trend
  middleware/
    security.py              ← slowapi + python-magic validation
    logging_middleware.py    ← loguru structured JSON logging
  utils/
    image_utils.py           ← Decode, resize, annotate, encode
    label_map.py             ← YOLO COCO → waste category map
  Dockerfile                 ← Multi-stage, non-root user
  requirements.txt
  .env.example
```

## Supabase Setup

The backend uses:
- **Postgres table**: `scan_records` (created via MCP migration)
- **Storage buckets**: `scan-results` (annotated images) + `heatmaps` (Grad-CAM)

Project ID: `uoffgokuvzndzgrfnfgm`  
Region: `us-east-1`

## License

MIT © EcoLens Contributors, 2026
