import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Eye, X } from "lucide-react";
import type { ScanResult, WasteCategory } from "@/types/detection";
import { CATEGORY_COLORS, CATEGORY_LABELS } from "@/utils/colorMap";
import { getScoreColor } from "@/utils/ecoScore";
import { cn } from "@/lib/utils";

interface Props {
  scans: ScanResult[];
}

const FILTER_CATEGORIES: (WasteCategory | "all")[] = ["all", "plastic", "organic", "metal", "ewaste", "glass"];

export function ScanHistory({ scans = [] }: Props) {
  const safeScans = scans || [];
  const [filter, setFilter] = useState<WasteCategory | "all">("all");
  const [selectedScan, setSelectedScan] = useState<ScanResult | null>(null);
  const [visibleCount, setVisibleCount] = useState(20);

  const filtered = filter === "all" ? safeScans : safeScans.filter((s) => s.dominant_category === filter);
  const visible = filtered.slice(0, visibleCount);

  return (
    <div className="bg-bg-surface border border-border rounded-xl overflow-hidden">
      <div className="px-5 pt-5 pb-3">
        <h3 className="text-[10px] font-mono text-text-muted uppercase tracking-wider mb-3">Scan History</h3>
        {/* Filter tabs */}
        <div className="flex gap-1.5 flex-wrap">
          {FILTER_CATEGORIES.map((cat) => (
            <button
              key={cat}
              onClick={() => { setFilter(cat); setVisibleCount(20); }}
              className={cn(
                "px-3 py-1.5 rounded-md text-[10px] font-mono uppercase tracking-wider transition-all duration-200",
                filter === cat
                  ? "bg-accent-green/15 text-accent-green"
                  : "text-text-muted hover:text-text-primary hover:bg-muted/30"
              )}
            >
              {cat === "all" ? "All" : CATEGORY_LABELS[cat]}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-t border-border text-[10px] font-mono text-text-muted uppercase tracking-wider">
              <th className="px-5 py-3 text-left font-medium">Timestamp</th>
              <th className="px-5 py-3 text-left font-medium">Classes</th>
              <th className="px-5 py-3 text-left font-medium">Eco Score</th>
              <th className="px-5 py-3 text-right font-medium">Action</th>
            </tr>
          </thead>
          <tbody>
            {visible.map((scan) => (
              <tr
                key={scan.scan_id}
                className="border-t border-border/50 hover:bg-[rgba(255,255,255,0.04)] transition-colors duration-150"
              >
                <td className="px-5 py-3 font-mono text-xs text-text-muted">
                  {new Date(scan.timestamp).toLocaleString("en-US", {
                    month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
                  })}
                </td>
                <td className="px-5 py-3">
                  <div className="flex gap-1.5 flex-wrap">
                    {(scan.detections || []).slice(0, 3).map((d) => (
                      <span
                        key={d.id}
                        className="text-[9px] font-mono px-2 py-0.5 rounded-md border"
                        style={{
                          color: CATEGORY_COLORS[d.category],
                          borderColor: `${CATEGORY_COLORS[d.category]}30`,
                          backgroundColor: `${CATEGORY_COLORS[d.category]}10`,
                        }}
                      >
                        {d.label}
                      </span>
                    ))}
                  </div>
                </td>
                <td className="px-5 py-3">
                  <span
                    className="text-xs font-mono font-medium px-2 py-1 rounded-md"
                    style={{
                      color: getScoreColor(scan.eco_score),
                      backgroundColor: `${getScoreColor(scan.eco_score)}15`,
                    }}
                  >
                    {scan.eco_score}
                  </span>
                </td>
                <td className="px-5 py-3 text-right">
                  <button
                    onClick={() => setSelectedScan(scan)}
                    className="text-text-muted hover:text-accent-green transition-colors inline-flex items-center gap-1 text-xs font-mono"
                    aria-label={`View scan ${scan.scan_id}`}
                  >
                    <Eye size={14} /> View
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {visible.length < filtered.length && (
        <div className="p-4 flex justify-center border-t border-border">
          <button
            onClick={() => setVisibleCount((c) => c + 20)}
            className="text-xs font-mono text-text-muted hover:text-accent-green transition-colors"
          >
            Load 20 more
          </button>
        </div>
      )}

      {/* Slide-over */}
      <AnimatePresence>
        {selectedScan && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-bg-base/60 backdrop-blur-sm z-40"
              onClick={() => setSelectedScan(null)}
            />
            <motion.aside
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ type: "spring", damping: 25, stiffness: 300 }}
              className="fixed top-0 right-0 h-full w-full max-w-[400px] bg-bg-surface border-l border-border z-50 overflow-y-auto"
            >
              <div className="p-5 flex items-center justify-between border-b border-border">
                <h3 className="font-heading font-bold text-sm text-text-primary">Scan Detail</h3>
                <button
                  onClick={() => setSelectedScan(null)}
                  className="p-1.5 rounded-md text-text-muted hover:text-text-primary transition-colors"
                  aria-label="Close panel"
                >
                  <X size={18} />
                </button>
              </div>
              <div className="p-5 space-y-4">
                <div>
                  <span className="text-[10px] font-mono text-text-muted uppercase tracking-wider">ID</span>
                  <p className="font-mono text-xs text-text-primary mt-0.5">{selectedScan.scan_id}</p>
                </div>
                <div>
                  <span className="text-[10px] font-mono text-text-muted uppercase tracking-wider">Eco Score</span>
                  <p className="text-2xl font-heading font-bold mt-0.5" style={{ color: getScoreColor(selectedScan.eco_score) }}>
                    {selectedScan.eco_score}
                  </p>
                </div>
                <div>
                  <span className="text-[10px] font-mono text-text-muted uppercase tracking-wider block mb-2">Detections</span>
                  <div className="space-y-2">
                    {(selectedScan.detections || []).map((d) => (
                      <div key={d.id} className="p-3 bg-bg-base/40 border border-border/50 rounded-lg">
                        <div className="flex justify-between items-baseline">
                          <span className="font-heading text-sm text-text-primary">{d.label}</span>
                          <span className="text-[10px] font-mono" style={{ color: CATEGORY_COLORS[d.category] }}>
                            {Math.round(d.confidence * 100)}%
                          </span>
                        </div>
                        <p className="text-[10px] font-mono text-text-muted mt-1">{d.suggestion}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
