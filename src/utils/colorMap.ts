import { WasteCategory } from "@/types/detection";

export const CATEGORY_COLORS: Record<WasteCategory, string> = {
  plastic: "#378ADD",
  organic: "#F5A623",
  metal: "#888780",
  paper: "#D4B483",
  ewaste: "#E84040",
  glass: "#1D9E75",
  unknown: "#6B7C6F",
};

export const CATEGORY_LABELS: Record<WasteCategory, string> = {
  plastic: "Plastic",
  organic: "Organic",
  metal: "Metal",
  paper: "Paper",
  ewaste: "E-Waste",
  glass: "Glass",
  unknown: "Unknown",
};
