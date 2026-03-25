import { useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Recycle, Leaf, AlertTriangle, Trash2, Package, Cpu, Wine, Layers, Shirt, ChevronDown } from "lucide-react";
import type { Detection, ScanResult, WasteCategory } from "@/types/detection";
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

interface CategoryGroup {
  category: WasteCategory;
  detections: Detection[];
  avgConfidence: number;
  disposal: { Icon: React.ElementType; text: string };
}

export function ResultPanel({ result, previewUrl }: Props) {
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const [hoveredCategory, setHoveredCategory] = useState<WasteCategory | null>(null);
  const [expandedCategory, setExpandedCategory] = useState<WasteCategory | null>(null);

  // Group detections by category
  const groupedDetections = useMemo<CategoryGroup[]>(() => {
    if (!result) return [];
    const map = new Map<WasteCategory, Detection[]>();
    for (const det of result.detections) {
      const existing = map.get(det.category) || [];
      existing.push(det);
      map.set(det.category, existing);
    }
    return Array.from(map.entries())
      .sort((a, b) => b[1].length - a[1].length)
      .map(([category, detections]) => ({
        category,
        detections,
        avgConfidence: detections.reduce((sum, d) => sum + d.confidence, 0) / detections.length,
        disposal: getDisposalInfo(detections[0]),
      }));
  }, [result]);

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

  // Build a set of IDs that belong to the hovered category for overlay dimming
  const hoveredCategoryIds = useMemo(() => {
    if (!hoveredCategory || !result) return new Set<string>();
    return new Set(
      result.detections
        .filter((d) => d.category === hoveredCategory)
        .map((d) => d.id)
    );
  }, [hoveredCategory, result]);

  return (
    <div className="flex flex-col gap-6 w-full animate-in fade-in slide-in-from-bottom-8 duration-700 ease-out">
      
      {/* Top dashboard section */}
      <div className="flex flex-col xl:flex-row gap-6 items-stretch">
        
        {/* Left: Annotated Image Viewer */}
        {previewUrl && (
          <div className="flex-1 rounded-2xl overflow-hidden bg-bg-surface/60 border border-border/80 shadow-[0_0_30px_rgba(0,0,0,0.5)] flex items-center justify-center p-3 sm:min-h-[450px]">
            {/* Tightly bound wrapper mapping absolute SVG coordinates to exact image size */}
            <div className="relative inline-block max-w-full max-h-[550px] group">
              <img 
                src={previewUrl} 
                alt="Scanned material" 
                className="w-auto h-auto max-w-full max-h-[550px] object-contain transition-transform duration-700" 
              />
              <DetectionOverlay 
                detections={result.detections} 
                hoveredId={hoveredId} 
                hoveredCategoryIds={hoveredCategoryIds}
                onHover={setHoveredId} 
              />
            </div>
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

      {/* Bottom Grid: Grouped Category Cards */}
      <div className="bg-bg-surface/40 border border-border/50 rounded-3xl p-5 md:p-7 shadow-sm backdrop-blur-sm">
        <h3 className="text-xs font-heading font-bold text-text-muted uppercase tracking-[0.2em] mb-6 flex items-center gap-3">
          <ScanLine size={16} className="text-accent-green" /> 
          Detected Elements Sandbox
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {groupedDetections.map((group, i) => {
            const CategoryIcon = categoryIcons[group.category] ?? Trash2;
            const color = CATEGORY_COLORS[group.category] ?? "#6B7C6F";
            const label = CATEGORY_LABELS[group.category] ?? group.category;
            const avgConfPct = Math.round(group.avgConfidence * 100);
            const isExpanded = expandedCategory === group.category;
            const isHoveredGroup = hoveredCategory === group.category;

            return (
              <motion.div
                key={group.category}
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05, duration: 0.4, ease: "easeOut" }}
                layout
                onMouseEnter={() => {
                  setHoveredCategory(group.category);
                  setExpandedCategory(group.category);
                }}
                onMouseLeave={() => {
                  setHoveredCategory(null);
                  setExpandedCategory(null);
                  setHoveredId(null);
                }}
                className={`rounded-xl border transition-all duration-300 cursor-default overflow-hidden relative group
                  ${isHoveredGroup ? 'bg-bg-surface border-border shadow-[0_8px_30px_rgba(0,0,0,0.4)] z-10' : 'bg-bg-base/60 border-border/30 hover:bg-bg-surface hover:border-border/60'}
                `}
                style={{ borderLeftWidth: 4, borderLeftColor: color }}
              >
                <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent opacity-0 group-hover:opacity-100 duration-300 pointer-events-none" />
                
                {/* Category Header */}
                <div className="p-4">
                  <div className="flex items-center gap-3">
                    <div 
                      className={`p-2.5 rounded-lg transition-colors duration-200 ${isHoveredGroup ? 'shadow-inner' : ''}`} 
                      style={{ backgroundColor: `${color}${isHoveredGroup ? '25' : '15'}` }}
                    >
                      <CategoryIcon size={18} style={{ color }} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex justify-between items-center mb-1.5">
                        <div className="flex items-center gap-2">
                          <h4 className="font-heading font-bold text-[13px] text-text-primary truncate tracking-wide">{label}</h4>
                          {group.detections.length > 1 && (
                            <span 
                              className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded-md border"
                              style={{ color, backgroundColor: `${color}15`, borderColor: `${color}30` }}
                            >
                              ×{group.detections.length}
                            </span>
                          )}
                        </div>
                        <span className="text-[9px] font-mono font-bold ml-2 shrink-0 bg-black/60 px-1.5 py-0.5 rounded shadow-sm border border-white/5" style={{ color }}>
                          {avgConfPct}% AVG
                        </span>
                      </div>
                      {/* Confidence bar */}
                      <div className="w-full h-[3px] bg-border/40 rounded-full overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${avgConfPct}%` }}
                          transition={{ duration: 0.8, delay: i * 0.05 + 0.2, type: "spring", bounce: 0.2 }}
                          className="h-full rounded-full"
                          style={{ backgroundColor: color }}
                        />
                      </div>
                    </div>
                  </div>
                  {/* Disposal instruction */}
                  <div className="flex items-start gap-2.5 mt-3 pl-12">
                    <group.disposal.Icon size={13} className="text-text-muted mt-0.5 shrink-0 opacity-70" />
                    <p className="text-[11px] leading-relaxed font-mono text-text-muted/90">{group.disposal.text}</p>
                  </div>

                  {/* Expand hint for groups with multiple items */}
                  {group.detections.length > 1 && (
                    <div className="flex items-center justify-center mt-2">
                      <motion.div
                        animate={{ rotate: isExpanded ? 180 : 0 }}
                        transition={{ duration: 0.2 }}
                      >
                        <ChevronDown size={14} className="text-text-muted/50" />
                      </motion.div>
                    </div>
                  )}
                </div>

                {/* Expanded Sub-items */}
                <AnimatePresence>
                  {isExpanded && group.detections.length > 1 && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.3, ease: "easeInOut" }}
                      className="overflow-hidden"
                    >
                      <div className="px-4 pb-4 space-y-2 border-t" style={{ borderColor: `${color}20` }}>
                        <p className="text-[9px] font-mono text-text-muted/60 uppercase tracking-widest pt-3 mb-2">
                          Individual Items
                        </p>
                        {group.detections.map((det) => {
                          const detConfPct = Math.round(det.confidence * 100);
                          const isItemHovered = hoveredId === det.id;
                          return (
                            <motion.div
                              key={det.id}
                              initial={{ opacity: 0, x: -8 }}
                              animate={{ opacity: 1, x: 0 }}
                              transition={{ duration: 0.2 }}
                              onMouseEnter={() => setHoveredId(det.id)}
                              onMouseLeave={() => setHoveredId(null)}
                              className={`flex items-center justify-between py-2 px-3 rounded-lg transition-all duration-200 cursor-default
                                ${isItemHovered ? 'bg-white/5 border border-white/10' : 'border border-transparent hover:bg-white/[0.03]'}
                              `}
                            >
                              <div className="flex items-center gap-2">
                                <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: color }} />
                                <span className="text-[11px] font-heading font-medium text-text-primary/80">{det.label}</span>
                              </div>
                              <div className="flex items-center gap-2">
                                <div className="w-12 h-[2px] bg-border/30 rounded-full overflow-hidden">
                                  <div className="h-full rounded-full" style={{ backgroundColor: color, width: `${detConfPct}%` }} />
                                </div>
                                <span className="text-[9px] font-mono font-bold" style={{ color }}>{detConfPct}%</span>
                              </div>
                            </motion.div>
                          );
                        })}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
