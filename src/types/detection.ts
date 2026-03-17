export type WasteCategory =
  | "plastic"
  | "organic"
  | "metal"
  | "paper"
  | "ewaste"
  | "glass"
  | "unknown";

export interface Detection {
  id: string;
  label: string;
  category: WasteCategory;
  confidence: number;
  bbox: [number, number, number, number];
  mask_points?: number[][];
  suggestion: string;
  bin_color: string;
  action: string;
  track_id?: number;
}

export interface ScanResult {
  scan_id: string;
  timestamp: string;
  image_url: string;
  heatmap_urls?: Record<WasteCategory, string>;
  detections: Detection[];
  dominant_category: WasteCategory;
  dominant_count: number;
  eco_score: number;
  object_counts: Record<WasteCategory, number>;
  latency_ms: number;
}

export interface DashboardStats {
  total_scans: number;
  total_today: number;
  top_category: WasteCategory;
  avg_eco_score: number;
  sorted_correctly_pct: number;
  category_distribution: Record<WasteCategory, number>;
  daily_scans: { date: string; count: number; avg_eco_score: number }[];
}

export interface HealthStatus {
  status: "ok" | "degraded" | "offline";
  model_loaded: boolean;
  db_connected: boolean;
}

export type ScanStatus = "idle" | "loading" | "success" | "error";
