import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip, Cell } from "recharts";
import { getScoreColor } from "@/utils/ecoScore";

interface DayScan {
  date: string;
  count: number;
  avg_eco_score: number;
}

interface Props {
  data: DayScan[];
}

export function DailyBarChart({ data }: Props) {
  return (
    <div className="bg-bg-surface border border-border rounded-xl p-5">
      <h3 className="text-[10px] font-mono text-text-muted uppercase tracking-wider mb-4">Scans Per Day</h3>
      <div className="h-48">
        <ResponsiveContainer>
          <BarChart data={data} barCategoryGap="30%">
            <XAxis
              dataKey="date"
              tick={{ fontSize: 10, fontFamily: '"DM Mono"', fill: "#6B7C6F" }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
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
              formatter={(value: number, _: string, props: any) => [
                `${value} scans`,
                `Avg score: ${props.payload.avg_eco_score}`,
              ]}
            />
            <Bar dataKey="count" radius={[4, 4, 0, 0]}>
              {data.map((entry, i) => (
                <Cell key={i} fill={getScoreColor(entry.avg_eco_score)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
