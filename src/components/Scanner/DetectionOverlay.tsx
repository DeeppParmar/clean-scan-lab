import { motion } from "framer-motion";
import type { Detection } from "@/types/detection";
import { CATEGORY_COLORS } from "@/utils/colorMap";

interface Props {
  detections: Detection[];
}

export function DetectionOverlay({ detections }: Props) {
  return (
    <svg className="absolute inset-0 z-10 pointer-events-none w-full h-full">
      {detections.map((det) => {
        const [x1, y1, x2, y2] = det.bbox;
        const color = CATEGORY_COLORS[det.category];
        return (
          <g key={det.id}>
            <motion.rect
              initial={{ opacity: 0, pathLength: 0 }}
              animate={{ opacity: 1, pathLength: 1 }}
              transition={{ duration: 0.4, ease: "easeOut" }}
              x={`${x1 * 100}%`}
              y={`${y1 * 100}%`}
              width={`${(x2 - x1) * 100}%`}
              height={`${(y2 - y1) * 100}%`}
              rx="4"
              fill="none"
              stroke={color}
              strokeWidth="1.5"
              className="drop-shadow-[0_0_6px_rgba(0,0,0,0.5)]"
            />
            <foreignObject
              x={`${x1 * 100}%`}
              y={`${y1 * 100 - 2.5}%`}
              width="130"
              height="20"
            >
              <div
                className="text-[9px] font-mono px-1.5 py-0.5 rounded-t-sm inline-block font-medium"
                style={{ backgroundColor: color, color: "#0D0F0E" }}
              >
                {det.label} {Math.round(det.confidence * 100)}%
              </div>
            </foreignObject>
          </g>
        );
      })}
    </svg>
  );
}
