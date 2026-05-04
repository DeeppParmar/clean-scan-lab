# EcoLens — Smart Waste Classification & Recycling System

> Microsoft Sustainability AI Project, 2026

EcoLens is an advanced AI-powered application designed to revolutionize waste sorting and recycling. By leveraging a two-stage hybrid computer vision pipeline, EcoLens acts as a highly accurate, real-time material classifier that not only identifies what an object is but also provides actionable, eco-friendly disposal instructions.

## 🚀 Technology Stack
- **Frontend:** React + Vite + TailwindCSS + shadcn/ui (Glassmorphism aesthetics)
- **Backend:** FastAPI + Uvicorn + Python 3.13
- **Deep Learning:** PyTorch + Ultralytics (YOLOv8) + Torchvision (MobileNetV2)
- **Database / Auth:** Supabase (PostgreSQL)

## 🧠 Core AI Architecture
EcoLens employs a unique **Two-Stage Inference Pipeline** to solve the notorious "garbage context" problem:
1. **Localization (YOLOv8 - TACO Dataset):** Scans the environment to locate physical objects, identifying general clusters like "bottle", "can", or "wrapper".
2. **Classification (MobileNetV2 - Garbage v2 Dataset):** Extracts the cropped objects and feeds them into a fine-tuned MobileNetV2 network capable of classifying the raw material into 10 distinct categories (e.g., *plastic, glass, metal, paper, organic, battery*).
3. **The Heuristic Engine:** Resolves conflicts between shape (YOLO) and texture (MobileNet). 

### 🔧 Recent Upgrades & Innovations
- **Universal Metal Detector:** A custom algorithm (`_is_metal_material`) that analyzes the physics of light on surfaces. It uses **Specular Adjacency** (bright hotspots next to dark shadows), **Block Contrast Variance**, and **Laplacian Edge Sharpness** to reliably detect metals—from shiny silver cutlery to crumpled foil and crushed red painted cans—completely independently of their color.
- **Dynamic HSV Vetoes:** Uses intelligent NumPy mask ratios to prevent green/yellow/brown organic waste (like banana peels) from being falsely classified as textiles or plastics.
- **Dense Sliding-Window Fallback:** If YOLO misses small or obscured items in a complex trash pile, the system automatically slices the image into overlapping quadrants and performs a hyper-aggressive dense detection pass, stitching the results back together using Non-Maximum Suppression (NMS).
- **Grad-CAM Diagnostics:** Generates real-time heatmaps in FP16 mixed precision, allowing users to see exactly which pixels the MobileNetV2 model relied on to make its classification.

## 📦 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/DeeppParmar/clean-scan-lab.git
   ```

2. **Backend Setup:**
   ```bash
   cd backend
   pip install -r requirements.txt
   python -m uvicorn main:app --reload
   ```

3. **Frontend Setup:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## 🌐 API Overview
- `POST /api/analyze`: Processes an image array, runs the two-stage inference, and returns bounding boxes, categories, eco-scores, and recycling instructions.
- `GET /api/stream`: WebSocket or polling endpoint for continuous live-feed classification.
- `GET /api/health`: Validates GPU status and model loaded states.

---
*Built to make the world cleaner, one pixel at a time.*
