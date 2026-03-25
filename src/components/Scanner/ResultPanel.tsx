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
    return null;
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
    <div className="flex flex-col gap-6 w-full animate-in fade-in slide-in-from-bottom-8 duration-700 ease-out">
      
      {/* Top dashboard section */}
      <div className="flex flex-col xl:flex-row gap-6 items-stretch">
        
        {/* Left: Annotated Image Viewer */}
        {previewUrl && (
          <div className="flex-1 relative rounded-2xl overflow-hidden bg-bg-surface/60 border border-border/80 shadow-[0_0_30px_rgba(0,0,0,0.5)] group flex items-center justify-center p-3 sm:min-h-[450px]">
            <img 
              src={previewUrl} 
              alt="Scanned material" 
              className="w-auto h-auto max-w-full max-h-[550px] object-contain transition-transform duration-700 group-hover:scale-[1.01]" 
            />
            <DetectionOverlay 
              detections={result.detections} 
              hoveredId={hoveredId} 
              onHover={setHoveredId} 
            />
          </div>
        )}

        {/* Right: Summary Metrics */}
        <div className="flex flex-col sm:flex-row xl:flex-col gap-4 w-full xl:w-[420px] shrink-0">
          
          {/* Eco Score Block */}
          <div className="bg-bg-surface border border-border/50 rounded-2xl p-6 flex flex-col justify-center items-center backdrop-blur-md flex-1 xl:flex-none xl:h-[220px] shadow-sm relative overflow-hidden group">
            <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />
            <h3 className="text-[10px] font-mono uppercase tracking-[0.2em] font-medium text-text-muted absolute top-4 left-5">System Analysis</h3>
            <div className="scale-110 mt-4">
              <EcoScoreGauge score={result.eco_score} />
            </div>
          </div>

          <div className="flex flex-col gap-4 flex-1">
            {/* Dominant Banner */}
            <div className="px-5 py-4 border rounded-2xl shadow-sm relative overflow-hidden" style={{ backgroundColor: `${dominantColor}15`, borderColor: `${dominantColor}40` }}>
              <div className="absolute top-0 right-0 w-32 h-32 blur-3xl rounded-full opacity-20" style={{ backgroundColor: dominantColor }} />
              <p className="text-[10px] font-mono uppercase tracking-[0.2em] font-bold" style={{ color: dominantColor }}>
                Primary Detection
              </p>
              <h3 className="text-xl sm:text-2xl font-heading font-black text-text-primary uppercase mt-1">
                {CATEGORY_LABELS[result.dominant_category] ?? "Mixed Waste"}
              </h3>
              <p className="text-sm font-mono text-text-muted mt-3 border-t pt-3 flex items-center justify-between" style={{ borderColor: `${dominantColor}20` }}>
                <span className="opacity-70">Total Elements</span>
                <span className="font-bold text-text-primary bg-black/30 px-2 py-0.5 rounded-md">{totalItems}</span>
              </p>
            </div>

            {/* Composition Panel */}
            <div className="px-5 py-5 border border-border/40 bg-bg-surface/50 rounded-2xl backdrop-blur-md relative overflow-hidden flex-1 shadow-sm">
              <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent pointer-events-none" />
              <p className="text-[10px] font-mono text-text-muted uppercase mb-4 tracking-widest font-semibold flex items-center gap-2">
                <Layers size={13} className="opacity-60" />
                Material Breakdown
              </p>
              <div className="flex flex-wrap gap-2.5 relative z-10">
                {composition.map((item) => {
                  const color = CATEGORY_COLORS[item.category] ?? "#6B7C6F";
                  const label = CATEGORY_LABELS[item.category] ?? item.category;
                  return (
                    <div
                      key={item.category}
                      className="inline-flex items-center gap-2.5 px-3 py-1.5 rounded-full border shadow-sm transition-all hover:border-white/20"
                      style={{ backgroundColor: `${color}15`, borderColor: `${color}30`, boxShadow: `0 0 10px ${color}08` }}
                    >
                      <div className="w-2 h-2 rounded-full shadow-[0_0_8px_currentColor]" style={{ backgroundColor: color, color }} />
                      <span className="text-xs font-heading font-semibold text-text-primary tracking-wide">{label}</span>
                      <span className="text-[10px] font-mono text-text-muted font-bold ml-1 bg-black/40 px-1.5 py-0.5 rounded-sm">{item.percentage}%</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Grid: Individual Items */}
      <div className="bg-bg-surface/40 border border-border/50 rounded-3xl p-5 md:p-7 shadow-sm backdrop-blur-sm">
        <h3 className="text-xs font-heading font-bold text-text-muted uppercase tracking-[0.2em] mb-6 flex items-center gap-3">
          <ScanLine size={16} className="text-accent-green" /> 
          Detected Elements Sandbox
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {result.detections.map((det, i) => {
            const CategoryIcon = categoryIcons[det.category] ?? Trash2;
            const disposal = getDisposalInfo(det);
            const color = CATEGORY_COLORS[det.category] ?? "#6B7C6F";
            const confPct = Math.round(det.confidence * 100);
            const isHovered = hoveredId === det.id;

            return (
              <motion.div
                key={det.id}
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.03, duration: 0.4, ease: "easeOut" }}
                onMouseEnter={() => setHoveredId(det.id)}
                onMouseLeave={() => setHoveredId(null)}
                className={`p-4 rounded-xl border transition-all duration-300 cursor-default overflow-hidden relative group
                  ${isHovered ? 'bg-bg-surface border-border scale-[1.02] shadow-[0_8px_30px_rgba(0,0,0,0.4)] z-10' : 'bg-bg-base/60 border-border/30 hover:bg-bg-surface hover:border-border/60'}
                `}
                style={{ borderLeftWidth: 4, borderLeftColor: color }}
              >
                <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent opacity-0 group-hover:opacity-100 duration-300 pointer-events-none" />
                <div className="flex items-center gap-3">
                  <div 
                    className={`p-2.5 rounded-lg transition-colors duration-200 ${isHovered ? 'shadow-inner' : ''}`} 
                    style={{ backgroundColor: `${color}${isHovered ? '25' : '15'}` }}
                  >
                    <CategoryIcon size={18} style={{ color }} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex justify-between items-baseline mb-1.5">
                      <h4 className="font-heading font-bold text-[13px] text-text-primary truncate tracking-wide">{det.label}</h4>
                      <span className="text-[9px] font-mono font-bold ml-2 shrink-0 bg-black/60 px-1.5 py-0.5 rounded shadow-sm border border-white/5" style={{ color }}>
                        {confPct}% CONF
                      </span>
                    </div>
                    {/* Confidence bar */}
                    <div className="w-full h-[3px] bg-border/40 rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${confPct}%` }}
                        transition={{ duration: 0.8, delay: i * 0.03 + 0.2, type: "spring", bounce: 0.2 }}
                        className="h-full rounded-full"
                        style={{ backgroundColor: color }}
                      />
                    </div>
                  </div>
                </div>
                {/* Disposal instruction */}
                <div className="flex items-start gap-2.5 mt-4 pl-12">
                  <disposal.Icon size={13} className="text-text-muted mt-0.5 shrink-0 opacity-70" />
                  <p className="text-[11px] leading-relaxed font-mono text-text-muted/90">{disposal.text}</p>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
