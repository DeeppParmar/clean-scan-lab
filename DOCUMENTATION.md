# EcoLens - Waste Intelligence System Architecture

## Overview
EcoLens is an advanced AI-powered waste classification and tracking system designed to accurately identify, categorize, and score disposed items. The project is split into a robust Python FastAPI backend that orchestrates a dual-stage machine learning inference pipeline, and a modern React/Vite frontend featuring a glassmorphic dashboard.

---

## 🏗️ Architecture & Flow

### 1. Frontend (React + Vite + TailwindCSS)
- **Framework**: React 18, Vite, TypeScript
- **Styling**: TailwindCSS with a custom pure-black and electric-cyan glassmorphic theme.
- **Routing**: `react-router-dom` handles navigation between the main `ScannerPage` and the analytics `DashboardPage`.
- **Data Visualization**: Recharts is used for displaying trend metrics, daily bar charts, and category distribution donuts.
- **Flow**: User uploads an image via `UploadZone.tsx`. The image is resized/compressed and sent to the backend `/api/analyze` endpoint. The response powers the `DetectionOverlay.tsx` (SVG bounding boxes) and the `<ResultPanel>` dashboard layout.

### 2. Backend (FastAPI + Python 3.13)
- **Framework**: FastAPI with Uvicorn (`--reload`).
- **Endpoints**:
  - `POST /api/analyze`: Main entrypoint for processing an image. Returns bounding boxes, labels, masks, eco-scores, and rule-based disposal suggestions.
  - `GET /api/stats`: Aggregates the `scan_records` from Supabase to compute KPIs and 7-day trends.
  - `GET /api/history`: Returns detailed historical records of past scans.
- **Database**: Supabase (PostgreSQL). Every scan is recorded in a `scan_records` table, and the raw image along with its generated Grad-CAM heatmap is uploaded to a Supabase Storage bucket.

### 3. Machine Learning Pipeline (`services/detector.py`)
The system employs a **Two-Stage Hybrid Object Detection Pipeline** for extremely high recall in cluttered environments (like garbage bins).

#### Stage 1: Localization (YOLOv8)
The uploaded image is passed to a generic `yolov8n.pt` model. 
- The confidence threshold is intentionally lowered (`0.08`) and the minimum area ratio is dropped (`0.002`) to ensure even small, deformed, or partially obscured items are localized.
- **Agnostic NMS** (`agnostic_nms=True`, `iou=0.55`) is strictly enforced to strip out any duplicate overlapping bounding boxes on the exact same physical object.
- The output of this stage is a set of precise bounding box coordinates (crops), completely disregarding YOLO's generic class guesses.

#### Stage 2: Deep Classification (MobileNetV2)
Each bounding box crop from Stage 1 is passed to a custom-trained **MobileNetV2** model (`waste_classifier.pth`).
- The model was fine-tuned on an extensive waste dataset to recognize 12 specific classes (e.g., plastic, battery, brown-glass, clothes, etc.), which are then mapped to 8 normalized system categories (plastic, metal, organic, ewaste, etc.).
- A strict heuristic is enforced here: if the classifier predicts "Textile" with less than 95% confidence, it is aggressively overridden to "Plastic", preventing false positives from crumpled garbage bags.

#### Stage 3: Feature Extraction (Grad-CAM)
The predicted class index is passed to `heatmap.py`, which generates a gradient-weighted class activation map (Grad-CAM) over the original image, visually explaining which pixels triggered the classifier's decision.

### 4. Evaluation & Rules
- **Rule Engine**: `rule_engine.py` applies static logic to the detections to generate human-readable instructions (e.g., "Rinse container before placing in blue bin").
- **Eco Scorer**: `eco_scorer.py` analyzes the composition of the detections (recyclable vs. hazardous vs. general trash) and calculates a penalty-weighted `eco_score` (0-100%).

---

## 🧹 Final Clean Up Audit
As part of the final polishing:
- Removed legacy Python typing imports (`from __future__ import annotations`) that conflicted with Pydantic v2 schemas and caused repeated `422 Unprocessable Entity` crashes.
- Added strict fallback safeguards to all React components (`WasteDonut`, `TrendChart`) to prevent render crashes when scanning an empty database or encountering unknown class mappings.
- Tightly bound the `<svg>` SVG positioning to the actual scaled `<img>` dimensions to guarantee millimeter-perfect bounding boxes regardless of viewport or aspect-ratio distortion.
- Consolidated UI colors and naming conventions across the frontend and backend labels.

## 🚀 Deployment
Ensure the `.env` correctly maps `SUPABASE_URL` and `SUPABASE_KEY` to the production project, and verify the frontend `VITE_API_URL` points to the hosted FastAPI instance. Both can be deployed to edge platforms like Vercel or Render.
