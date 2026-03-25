import { motion, AnimatePresence } from "framer-motion";
import type { Detection } from "@/types/detection";
import { CATEGORY_COLORS } from "@/utils/colorMap";

interface Props {
  detections: Detection[];
  hoveredId?: string | null;
  hoveredCategoryIds?: Set<string>;
  onHover?: (id: string | null) => void;
}

export function DetectionOverlay({ detections, hoveredId, hoveredCategoryIds, onHover }: Props) {
  const hasAnyHover = !!hoveredId || (hoveredCategoryIds && hoveredCategoryIds.size > 0);

  return (
    <svg className="absolute inset-0 z-10 w-full h-full pointer-events-auto">
      <AnimatePresence>
        {detections.map((det) => {
          const [x1, y1, x2, y2] = det.bbox;
          const color = CATEGORY_COLORS[det.category] ?? "#6B7C6F";
          const isHovered = hoveredId === det.id;
          const isInCategory = hoveredCategoryIds?.has(det.id) ?? false;
          const isHighlighted = isHovered || isInCategory;
          const opacity = hasAnyHover ? (isHighlighted ? 1 : 0.15) : 1;
          const zIndex = isHighlighted ? 20 : 10;

          // Convert normalized mask points to SVG polygon points (0-100%)
          // Fallback to bbox if mask_points are missing
          const polygonPoints = det.mask_points
            ? det.mask_points.map(p => `${p[0] * 100},${p[1] * 100}`).join(" ")
            : `${x1 * 100},${y1 * 100} ${x2 * 100},${y1 * 100} ${x2 * 100},${y2 * 100} ${x1 * 100},${y2 * 100}`;

          return (
            <motion.g
              key={det.id}
              initial={{ opacity: 0 }}
              animate={{ opacity }}
              transition={{ duration: 0.3 }}
              style={{ zIndex }}
              onMouseEnter={() => onHover?.(det.id)}
              onMouseLeave={() => onHover?.(null)}
              className="cursor-crosshair group"
            >
              {/* Mask Polygon */}
              <motion.polygon
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: isHighlighted ? 0.3 : 0, scale: 1 }}
                transition={{ duration: 0.4, ease: "easeOut" }}
                points={polygonPoints}
                fill={color}
                // Convert percentage strings to numeric for SVG geometry
                transform-origin={`${(x1 + x2) * 50}% ${(y1 + y2) * 50}%`}
                className="pointer-events-auto"
              />

              {/* Bounding Box Stroke */}
              <motion.rect
                initial={{ opacity: 0, pathLength: 0 }}
                animate={{ opacity: isHighlighted ? 1 : 0.6, pathLength: 1 }}
                transition={{ duration: 0.5, ease: "easeOut" }}
                x={`${x1 * 100}%`}
                y={`${y1 * 100}%`}
                width={`${(x2 - x1) * 100}%`}
                height={`${(y2 - y1) * 100}%`}
                rx="4"
                fill="none"
                stroke={color}
                strokeWidth={isHighlighted ? "2.5" : "1.5"}
                className={isHighlighted ? "drop-shadow-[0_0_8px_rgba(0,0,0,0.8)] pointer-events-auto" : "pointer-events-auto"}
              />

              {/* Label Tag */}
              <foreignObject
                x={`${x1 * 100}%`}
                y={`calc(${y1 * 100}% - 24px)`}
                width="160"
                height="24"
                className={`transition-opacity duration-200 pointer-events-none ${isHighlighted ? 'opacity-100 z-50' : 'opacity-0 group-hover:opacity-100'}`}
              >
                <div
                  className="text-[10px] font-mono px-2 py-1 rounded shadow-lg font-bold truncate"
                  style={{ backgroundColor: color, color: "#000" }}
                >
                  {det.label} {Math.round(det.confidence * 100)}%
                </div>
              </foreignObject>
            </motion.g>
          );
        })}
      </AnimatePresence>
    </svg>
  );
}
