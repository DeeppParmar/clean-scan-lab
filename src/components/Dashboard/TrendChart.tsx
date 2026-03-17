import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip, Dot } from "recharts";
import { getScoreColor } from "@/utils/ecoScore";

interface DayScan {
  date: string;
  count: number;
  avg_eco_score: number;
}

interface Props {
  data: DayScan[];
}

function CustomDot(props: any) {
  const { cx, cy, payload } = props;
  return (
    <Dot cx={cx} cy={cy} r={4} fill={getScoreColor(payload.avg_eco_score)} stroke="none" />
  );
}

export function TrendChart({ data }: Props) {
  return (
    <div className="bg-bg-surface border border-border rounded-xl p-5">
      <h3 className="text-[10px] font-mono text-text-muted uppercase tracking-wider mb-4">7-Day Eco Trend</h3>
      <div className="h-40">
        <ResponsiveContainer>
          <LineChart data={data}>
            <XAxis
              dataKey="date"
              tick={{ fontSize: 10, fontFamily: '"DM Mono"', fill: "#6B7C6F" }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              domain={[0, 100]}
              tick={{ fontSize: 10, fontFamily: '"DM Mono"', fill: "#6B7C6F" }}
              axisLine={false}
              tickLine={false}
              width={30}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#141916",
                border: "1px solid rgba(255,255,255,0.07)",
                borderRadius: "8px",
                fontSize: "11px",
                fontFamily: '"DM Mono", monospace',
                color: "#E8EDE9",
              }}
              formatter={(value: number) => [`Score: ${value}`, "Avg Eco"]}
              labelFormatter={(label) => `${label}`}
            />
            <Line
              type="monotone"
              dataKey="avg_eco_score"
              stroke="#3DDA84"
              strokeWidth={2}
              dot={<CustomDot />}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
