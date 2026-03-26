# EcoLens - Comprehensive Project Documentation

## 1. Executive Summary
EcoLens is an advanced AI-powered waste classification and tracking system designed to accurately identify, categorize, and score disposed items. The platform features a high-performance Python FastAPI backend orchestrating a sophisticated dual-stage machine learning inference pipeline, seamlessly integrated with a modern React/Vite frontend.

---

## 2. System Architecture

### 2.1 High-Level Architecture
The system follows a decoupled client-server architecture:
- **Frontend Layer:** React 18 SPA built with Vite and styled using TailwindCSS. Focuses on glassmorphic aesthetics.
- **Backend API Layer:** FastAPI (Python 3.13) providing RESTful endpoints and managing parallel ML execution.
- **Database & Storage Layer:** Supabase (PostgreSQL) handling persistence for scan metrics and file blob storage (images and generated heatmaps).

### 2.2 Data Models and Relations
The primary data entity is the **Scan Record**, which maps 1:1 with an uploaded image.
- **`scan_records` (PostgreSQL Table)**:
  - `id` (UUID): Unique identifier for the scan.
  - `created_at` (Timestamp): Time of the scan.
  - `eco_score` (Float): Calculated penalty-weighted score (0-100%).
  - `detections` (JSONB): Array of localized items, including their category, raw label, confidence, and scaled bounding box coordinates.
- **Supabase Storage Buckets**:
  - `scan-results`: Stores the optimized original user upload (`{scan_id}.jpg`).
  - `heatmaps`: Stores the generated Grad-CAM visualizations. Maps via foreign-key conceptually (`{scan_id}/{category}.jpg`).

---

## 3. Machine Learning Pipeline

EcoLens employs a highly optimized **Two-Stage Hybrid Object Detection Pipeline** specifically engineered for high-recall in cluttered, difficult environments (e.g., overflowing trash bins) while maintaining low latency.

### 3.1 Stage 1: Localization (YOLOv8)
- **Model:** `yolov8n.pt` (Generic Base Weights).
- **Purpose:** Rapidly scan the input image and propose bounding box regions representing distinct objects.
- **Configuration & Latency Tuning:** 
  - Image is aggressively downscaled to `640px` max before inference.
  - Confidence threshold lowered to `0.08` to enforce maximum recall on obscured or deformed items.
  - Area limits enforced (`0.002` to `0.60`) to filter out micro-noise and massive background boxes.
  - Strict **Agnostic NMS** (`iou=0.55`) is applied to prevent the model from hallucinating double/triple bounding boxes over the same physical object.

### 3.2 Stage 2: Deep Classification (MobileNetV2)
- **Model:** Custom fine-tuned `MobileNetV2` (`waste_classifier.pth`).
- **Input:** Each bounding box crop extracted from Stage 1 (padded by 10% context) is resized to `224x224` and processed independently.
- **Heuristics:** Enforces strict domain logic (e.g., if the model predicts "Clothes/Textile" with `<95%` confidence, the backend aggressively overrides the label to "Plastic" to counteract visual similarities with crumpled garbage bags).

### 3.3 Stage 3: Explainability (Grad-CAM)
- **Engine:** PyTorch Grad-CAM targeting the final `InvertedResidual` block of the MobileNetV2 feature backbone.
- **Purpose:** Generates a visual heat map representing the specific pixel regions that influenced the classifier's activation, blended with the original crop using a `JET` colormap.

---

## 4. Model Training & Fine-Tuning Methodology

The MobileNetV2 classification backbone was trained natively using a specialized two-phase curriculum.

### 4.1 Dataset & Augmentation
- **Base Dataset:** 12-class `garbage_classification` dataset (classes: `battery`, `biological`, `brown-glass`, `cardboard`, `clothes`, `green-glass`, `metal`, `paper`, `plastic`, `shoes`, `trash`, `white-glass`).
- **Heavy Augmentations:** To make the model robust to real-world camera artifacts, the dataset passes through `RandomResizedCrop` (0.7-1.0), `ColorJitter` (brightness, contrast, saturation, hue), `RandomAffine`, `RandomRotation(15)`, and `RandomErasing(p=0.15)`.

### 4.2 Two-Phase Base Training (`train_classifier.py`)
Loaded with ImageNet `MobileNet_V2_Weights.DEFAULT`.
- **Phase 1 (Head Only):** The feature extraction backbone is completely frozen. The custom classification head (Dropout -> Linear 512 -> ReLU -> Linear 12) is trained for up to 8 epochs using Adam optimizer (`1e-3` LR) with Cosine Annealing.
- **Phase 2 (Full Network):** The entire backbone is unfrozen. The network is fine-tuned for an additional 12 epochs using a differential learning rate (`1e-4` for the head, `1e-5` for the feature backbone) to preserve underlying edge-detection weights while adapting to the waste domain. Incorporates Early Stopping (patience=5).

### 4.3 Incremental Fine-Tuning (`finetune_classifier.py`)
To adapt the model specifically for edge cases (e.g., trash bag focus), an incremental fine-tuning script loads the previously derived `waste_classifier.pth` and executes a short, focused 6-epoch burst training across the entire network to correct drift and improve specific class accuracy margins.

---

## 5. Software Workflow & User Flow

### 5.1 The User Flow
1. **Accessing Application:** User loads the Vercel-hosted frontend or local environment.
2. **Uploading:** User drags/drops an image or uses the camera via the main `UploadZone.tsx` interface. 
3. **Processing State:** A scanning animation is displayed.
4. **Insights Dashboard:** Upon completion, the UI dynamically renders:
   - **Detection Overlay:** SVG boxes precisely map onto the original image.
   - **Heatmap Viewer:** Tabbed navigation to view the Grad-CAM reasoning for each detected category.
   - **Analysis Metrics:** The calculated Eco-Score, item breakdown, and rule-based disposal suggestions are presented in the `<ResultPanel>`.
5. **Analytics:** The user navigates to `/dashboard` to view historical metrics, accuracy ratings, and real-time distribution charts.

### 5.2 Server Execution Workflow (Latency Optimized)
1. **Request Intake:** `POST /api/analyze` receives a base64 encoded payload.
2. **Thread Offloading:** FastAPI immediately offloads the image processing to a `ThreadPoolExecutor` (max 2 workers) via `loop.run_in_executor`, ensuring the `asyncio` loop never blocks.
3. **Pipelined Inference:** 
   - YOLO runs synchronous inference on the worker thread.
   - Cropping heuristics execute.
   - MobileNet runs in `torch.no_grad()` evaluation mode on the GPU (or CPU fallback).
4. **Parallel Async I/O:** 
   - Image and Heatmap assets are concurrently uploaded to Supabase Storage.
   - Database record is inserted asynchronously via `scan_records.insert()`.
5. **Response Delivery:** JSON payload containing detections and associated public Supabase URLs is routed back to the client.

---

## 6. Real-Time Capabilities
EcoLens incorporates experimental real-time object tracking over WebSockets (`/ws/stream`). 
- **TrackerSession (`tracker.py`):** Manages a rolling connection handling raw video frames.
- **Temporal Smoothing:** To prevent UI flickering characteristic of real-time multi-stage pipelines, the backend requires 2 consecutive stable classifications from MobileNetV2 before mutating the reported category stream. 
- **Capacity Limits:** System enforces a strict constraint of maximum concurrent WebSocket threads to protect server memory boundaries.

---
*Generated autonomously on behalf of the developer.*
