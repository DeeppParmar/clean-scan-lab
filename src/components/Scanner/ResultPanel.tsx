import { useState } from "react";
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

function getDisposalInfo(det: { action: string; suggestion: string }) {
  const iconMap: Record<string, React.ElementType> = {
    Recycle: Recycle,
    Dispose: Trash2,
    Hazardous: AlertTriangle,
  };
  const key = det.action.includes("Recycle") || det.action.includes("recycle")
    ? "Recycle"
    : det.action.includes("Dispose") || det.action.includes("dispose")
    ? "Dispose"
    : "Hazardous";
  return { Icon: iconMap[key] || Recycle, text: det.suggestion };
}

export function ResultPanel({ result, previewUrl }: Props) {
  const [hoveredId, setHoveredId] = useState<string | null>(null);

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

  // Build summary composition with percentages
  const composition = Object.entries(result.object_counts)
    .sort((a, b) => b[1] - a[1]) // Sort by count desc
    .map(([cat, count]) => ({
      category: cat as WasteCategory,
      count,
      percentage: Math.round((count / totalItems) * 100)
    }));

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
        <div className="relative mx-4 mt-4 rounded-lg overflow-hidden bg-bg-surface border border-border/80 shadow-inner group">
          <img src={previewUrl} alt="Scanned image" className="w-full object-contain max-h-56 transition-transform duration-700 group-hover:scale-[1.02]" />
          <DetectionOverlay 
            detections={result.detections} 
            hoveredId={hoveredId} 
            onHover={setHoveredId} 
          />
        </div>
      )}

      {/* Composition Summary Panel */}
      <div className="px-4 py-3 border-b border-border/50 bg-bg-base/30">
        <p className="text-[10px] font-mono text-text-muted uppercase mb-2">Composition</p>
        <div className="flex flex-wrap gap-2">
          {composition.map((item) => {
            const color = CATEGORY_COLORS[item.category] ?? "#6B7C6F";
            const label = CATEGORY_LABELS[item.category] ?? item.category;
            return (
              <div
                key={item.category}
                className="inline-flex items-center gap-2 px-2.5 py-1.5 rounded-md border border-border/50"
                style={{ backgroundColor: `${color}10` }}
              >
                <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: color }} />
                <span className="text-xs font-heading font-medium text-text-primary">{label}</span>
                <span className="text-[10px] font-mono text-text-muted font-bold ml-1">{item.percentage}%</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Detection list */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-2.5">
        {result.detections.map((det, i) => {
          const CategoryIcon = categoryIcons[det.category] ?? Trash2;
          const disposal = getDisposalInfo(det);
          const color = CATEGORY_COLORS[det.category] ?? "#6B7C6F";
          const confPct = Math.round(det.confidence * 100);
          const isHovered = hoveredId === det.id;

          return (
            <motion.div
              key={det.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.05, duration: 0.3, ease: "easeOut" }}
              onMouseEnter={() => setHoveredId(det.id)}
              onMouseLeave={() => setHoveredId(null)}
              className={`p-3 rounded-lg border transition-all duration-200 cursor-pointer 
                ${isHovered ? 'bg-bg-base border-border scale-[1.01] shadow-md' : 'bg-bg-base/40 border-border/50 hover:bg-bg-base/60'}`}
              style={{ borderLeftWidth: 4, borderLeftColor: color }}
            >
              <div className="flex items-center gap-3">
                <div 
                  className={`p-2 rounded-md transition-colors duration-200 ${isHovered ? 'shadow-inner' : ''}`} 
                  style={{ backgroundColor: `${color}${isHovered ? '25' : '15'}` }}
                >
                  <CategoryIcon size={18} style={{ color }} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex justify-between items-baseline mb-1">
                    <h4 className="font-heading font-semibold text-sm text-text-primary truncate">{det.label}</h4>
                    <span className="text-[10px] font-mono font-bold ml-2 shrink-0 bg-bg-surface px-1.5 py-0.5 rounded shadow-sm border border-border/50" style={{ color }}>
                      {confPct}% CONF
                    </span>
                  </div>
                  {/* Confidence bar — animated */}
                  <div className="w-full h-1 bg-border/40 rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${confPct}%` }}
                      transition={{ duration: 0.8, delay: i * 0.05 + 0.2, type: "spring", bounce: 0.2 }}
                      className="h-full rounded-full"
                      style={{ backgroundColor: color }}
                    />
                  </div>
                </div>
              </div>
              {/* Disposal instruction */}
              <div className="flex items-start gap-2 mt-3 pl-10">
                <disposal.Icon size={12} className="text-text-muted mt-0.5 shrink-0" />
                <p className="text-[11px] leading-snug font-mono text-text-muted/80">{disposal.text}</p>
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Eco Score Gauge */}
      <div className="bg-bg-base/50 p-4 border-t border-border flex justify-center items-center backdrop-blur-sm">
        <EcoScoreGauge score={result.eco_score} />
      </div>
    </div>
  );
}
