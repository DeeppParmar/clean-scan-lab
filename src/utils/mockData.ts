import { ScanResult, DashboardStats, WasteCategory, Detection } from "@/types/detection";

const makeDetection = (
  id: string,
  label: string,
  category: WasteCategory,
  confidence: number,
  bbox: [number, number, number, number],
  suggestion: string,
  bin_color: string,
  action: string
): Detection => ({
  id, label, category, confidence, bbox, suggestion, bin_color, action,
});

export const MOCK_SCAN_RESULT: ScanResult = {
  scan_id: "scan-001",
  timestamp: "2026-03-17T10:23:45Z",
  image_url: "",
  detections: [
    makeDetection("d1", "PET Bottle", "plastic", 0.96, [0.12, 0.15, 0.38, 0.72], "Recycle — blue bin", "Blue", "Rinse and place in recycling"),
    makeDetection("d2", "Aluminum Can", "metal", 0.91, [0.45, 0.20, 0.65, 0.68], "Recycle — metal bin", "Silver", "Crush and recycle"),
    makeDetection("d3", "Banana Peel", "organic", 0.88, [0.68, 0.35, 0.90, 0.80], "Compost — green bin", "Green", "Place in compost"),
    makeDetection("d4", "Cardboard Box", "paper", 0.85, [0.05, 0.75, 0.45, 0.95], "Recycle — paper bin", "Brown", "Flatten and recycle"),
    makeDetection("d5", "USB Cable", "ewaste", 0.79, [0.55, 0.05, 0.72, 0.18], "Hazardous — e-waste dropoff", "Red", "Take to certified e-waste center"),
  ],
  dominant_category: "plastic",
  dominant_count: 1,
  eco_score: 72,
  object_counts: { plastic: 1, organic: 1, metal: 1, paper: 1, ewaste: 1, glass: 0, unknown: 0 },
  latency_ms: 320,
};

export const MOCK_DASHBOARD_STATS: DashboardStats = {
  total_scans: 1247,
  total_today: 12,
  top_category: "plastic",
  avg_eco_score: 68,
  sorted_correctly_pct: 84,
  category_distribution: { plastic: 412, organic: 298, metal: 187, paper: 156, ewaste: 89, glass: 105, unknown: 0 },
  daily_scans: [
    { date: "Mar 11", count: 42, avg_eco_score: 65 },
    { date: "Mar 12", count: 38, avg_eco_score: 71 },
    { date: "Mar 13", count: 55, avg_eco_score: 58 },
    { date: "Mar 14", count: 47, avg_eco_score: 73 },
    { date: "Mar 15", count: 61, avg_eco_score: 68 },
    { date: "Mar 16", count: 53, avg_eco_score: 75 },
    { date: "Mar 17", count: 12, avg_eco_score: 72 },
  ],
};

export const MOCK_SCAN_HISTORY: ScanResult[] = Array.from({ length: 8 }, (_, i) => ({
  scan_id: `scan-${String(i + 1).padStart(3, "0")}`,
  timestamp: new Date(2026, 2, 17, 10 - i, Math.floor(Math.random() * 60)).toISOString(),
  image_url: "",
  detections: MOCK_SCAN_RESULT.detections.slice(0, Math.floor(Math.random() * 4) + 1),
  dominant_category: (["plastic", "organic", "metal", "paper", "ewaste", "glass"] as WasteCategory[])[i % 6],
  dominant_count: Math.floor(Math.random() * 3) + 1,
  eco_score: Math.floor(Math.random() * 60) + 30,
  object_counts: { plastic: 1, organic: 1, metal: 0, paper: 0, ewaste: 0, glass: 0, unknown: 0 },
  latency_ms: Math.floor(Math.random() * 200) + 200,
}));
