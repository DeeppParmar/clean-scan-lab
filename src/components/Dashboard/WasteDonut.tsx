import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";
import { CATEGORY_COLORS, CATEGORY_LABELS } from "@/utils/colorMap";
import type { WasteCategory } from "@/types/detection";

interface Props {
  data: Record<WasteCategory, number>;
}

export function WasteDonut({ data }: Props) {
  const chartData = Object.entries(data)
    .filter(([, v]) => v > 0)
    .map(([key, value]) => ({
      name: CATEGORY_LABELS[key as WasteCategory] || (key ? key.toString() : "Unknown"),
      value,
      color: CATEGORY_COLORS[key as WasteCategory] || "#888888",
    }));

  const total = chartData.reduce((s, d) => s + d.value, 0);

  return (
    <div className="bg-bg-surface border border-border rounded-xl p-5">
      <h3 className="text-[10px] font-mono text-text-muted uppercase tracking-wider mb-4">Category Distribution</h3>
      <div className="flex flex-col items-center">
        <div className="relative w-48 h-48">
          <ResponsiveContainer>
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                innerRadius={55}
                outerRadius={80}
                paddingAngle={3}
                dataKey="value"
                strokeWidth={0}
              >
                {chartData.map((entry, i) => (
                  <Cell key={i} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: "#141916",
                  border: "1px solid rgba(255,255,255,0.07)",
                  borderRadius: "8px",
                  fontSize: "11px",
                  fontFamily: '"DM Mono", monospace',
                  color: "#E8EDE9",
                }}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
            <span className="text-xl font-heading font-bold text-text-primary">{total}</span>
            <span className="text-[9px] font-mono text-text-muted uppercase">Total</span>
          </div>
        </div>
        <div className="flex flex-wrap justify-center gap-x-4 gap-y-1.5 mt-4">
          {chartData.map((d) => (
            <div key={d.name} className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-full" style={{ backgroundColor: d.color }} />
              <span className="text-[10px] font-mono text-text-muted">{d.name}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
