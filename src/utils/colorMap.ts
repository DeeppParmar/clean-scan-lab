import { WasteCategory } from "@/types/detection";

export const CATEGORY_COLORS: Record<WasteCategory, string> = {
  plastic: "#378ADD",
  organic: "#F5A623",
  metal: "#888780",
  paper: "#D4B483",
  ewaste: "#E84040",
  glass: "#1D9E75",
  textile: "#06B6D4",
  general: "#64748B",
  mixed: "#A855F7",
  unknown: "#6B7C6F",
};

export const CATEGORY_LABELS: Record<WasteCategory, string> = {
  plastic: "Plastic",
  organic: "Organic",
  metal: "Metal",
  paper: "Paper",
  ewaste: "E-Waste",
  glass: "Glass",
  textile: "Textile",
  general: "General Trash",
  mixed: "Mixed Waste",
  unknown: "Unknown",
};
