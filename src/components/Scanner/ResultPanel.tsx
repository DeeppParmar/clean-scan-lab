import { motion } from "framer-motion";
import { Recycle, Leaf, AlertTriangle, Trash2, Package, Cpu, Wine, Layers, Shirt } from "lucide-react";
import type { ScanResult, WasteCategory } from "@/types/detection";
import { CATEGORY_COLORS, CATEGORY_LABELS } from "@/utils/colorMap";
import { DetectionOverlay } from "./DetectionOverlay";
import { EcoScoreGauge } from "./EcoScoreGauge";
import { ScanLine } from "lucide-react";

interface Props {
  result: ScanResult | null;
  previewUrl: string | null;
}

const categoryIcons: Record<WasteCategory, React.ElementType> = {
  plastic: Package,
  organic: Leaf,
  metal: Cpu,
  paper: Recycle,
  ewaste: AlertTriangle,
  glass: Wine,
  textile: Shirt,
  general: Trash2,
  mixed: Layers,
  unknown: Trash2,
};

function getDisposalInfo(det: { action: string; bin_color: string; category: WasteCategory; suggestion: string }) {
  const iconMap: Record<string, React.ElementType> = {
    Recycle: Recycle,
    Compost: Leaf,
    Hazardous: AlertTriangle,
  };
  const key = det.action.includes("Recycle") || det.action.includes("recycle")
    ? "Recycle"
    : det.action.includes("Compost") || det.action.includes("compost")
    ? "Compost"
    : "Hazardous";
  return { Icon: iconMap[key] || Recycle, text: det.suggestion };
}

export function ResultPanel({ result, previewUrl }: Props) {
  if (!result) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center text-text-muted p-8 text-center bg-bg-surface border border-border rounded-xl min-h-[400px]">
        <ScanLine size={48} className="mb-4 opacity-20" />
        <p className="font-mono text-xs uppercase tracking-[0.15em]">Awaiting input stream...</p>
        <p className="font-mono text-[10px] text-text-muted/40 mt-2">Upload an image or use webcam to begin</p>
      </div>
    );
  }

  const dominantColor = CATEGORY_COLORS[result.dominant_category] ?? "#6B7C6F";
  const totalItems = result.detections.length;

  // Build summary counts per category
  const categoryCounts: Record<string, number> = {};
  for (const det of result.detections) {
    categoryCounts[det.category] = (categoryCounts[det.category] || 0) + 1;
  }

  return (
    <div className="flex flex-col bg-bg-surface border border-border rounded-xl overflow-hidden min-h-[400px]">
      {/* Dominant banner */}
      <div className="px-4 py-3 border-b" style={{ backgroundColor: `${dominantColor}15`, borderColor: `${dominantColor}30` }}>
        <p className="text-[9px] font-mono uppercase tracking-[0.2em] font-medium text-text-muted">
          Dominant Waste Type
        </p>
        <p className="text-lg font-heading font-bold text-text-primary uppercase mt-0.5">
          {CATEGORY_LABELS[result.dominant_category] ?? "Mixed Waste"} · {totalItems} {totalItems === 1 ? "item" : "items"}
        </p>
      </div>

      {/* Annotated image */}
      {previewUrl && (
        <div className="relative mx-4 mt-4 rounded-lg overflow-hidden bg-bg-surface border border-border">
          <img src={previewUrl} alt="Scanned image" className="w-full object-contain max-h-48" />
          <DetectionOverlay detections={result.detections} />
        </div>
      )}

      {/* Category summary strip */}
      <div className="flex flex-wrap gap-2 px-4 py-2.5 border-b border-border/50">
        {Object.entries(categoryCounts).map(([cat, count]) => {
          const color = CATEGORY_COLORS[cat as WasteCategory] ?? "#6B7C6F";
          const label = CATEGORY_LABELS[cat as WasteCategory] ?? cat;
          return (
            <span
              key={cat}
              className="inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-[10px] font-mono font-medium"
              style={{ backgroundColor: `${color}15`, color }}
            >
              <span
                className="w-2 h-2 rounded-full shrink-0"
                style={{ backgroundColor: color }}
              />
              {label} ×{count}
            </span>
          );
        })}
      </div>

      {/* Detection list */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-2.5">
        {result.detections.map((det, i) => {
          const CategoryIcon = categoryIcons[det.category] ?? Trash2;
          const disposal = getDisposalInfo(det);
          const color = CATEGORY_COLORS[det.category] ?? "#6B7C6F";
          const confPct = Math.round(det.confidence * 100);
          return (
            <motion.div
              key={det.id}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.06, duration: 0.3, ease: "easeOut" }}
              className="p-3 rounded-lg border border-border/50 bg-bg-base/40"
              style={{ borderLeftWidth: 3, borderLeftColor: color }}
            >
              <div className="flex items-center gap-3">
                <div className="p-1.5 rounded-md" style={{ backgroundColor: `${color}15` }}>
                  <CategoryIcon size={18} style={{ color }} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex justify-between items-baseline">
                    <h4 className="font-heading font-medium text-sm text-text-primary truncate">{det.label}</h4>
                    <span className="text-xs font-mono font-bold ml-2 shrink-0" style={{ color }}>
                      {confPct}%
                    </span>
                  </div>
                  {/* Confidence bar — full width range so 79% vs 96% is visually distinct */}
                  <div className="w-full h-1.5 bg-border/30 mt-2 rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${confPct}%` }}
                      transition={{ duration: 0.5, delay: i * 0.06 + 0.15, ease: "easeOut" }}
                      className="h-full rounded-full"
                      style={{ backgroundColor: color }}
                    />
                  </div>
                </div>
              </div>
              {/* Disposal badge */}
              <div className="flex items-center gap-1.5 mt-2 pl-9">
                <disposal.Icon size={12} className="text-text-muted shrink-0" />
                <span className="text-[10px] font-mono text-text-muted truncate">{disposal.text}</span>
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Eco Score */}
      <div className="p-4 border-t border-border flex justify-center">
        <EcoScoreGauge score={result.eco_score} />
      </div>
    </div>
  );
}
