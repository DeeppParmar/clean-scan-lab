import { ScanLine, TrendingUp, Award, CheckCircle, Package } from "lucide-react";
import { KPICard } from "@/components/Dashboard/KPICard";
import { WasteDonut } from "@/components/Dashboard/WasteDonut";
import { DailyBarChart } from "@/components/Dashboard/DailyBarChart";
import { TrendChart } from "@/components/Dashboard/TrendChart";
import { ScanHistory } from "@/components/Dashboard/ScanHistory";
import { MOCK_DASHBOARD_STATS, MOCK_SCAN_HISTORY } from "@/utils/mockData";
import { CATEGORY_LABELS } from "@/utils/colorMap";
import { getScoreColor } from "@/utils/ecoScore";

export default function DashboardPage() {
  const stats = MOCK_DASHBOARD_STATS;

  return (
    <div className="p-4 md:p-6 space-y-6 max-w-[1400px] mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-heading font-bold text-text-primary">Waste Intelligence</h1>
        <p className="text-xs font-mono text-text-muted mt-1">Mar 11 – Mar 17, 2026</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="Total Scans"
          value={stats.total_scans.toLocaleString()}
          subtitle={`+${stats.total_today} today`}
          icon={<ScanLine size={16} />}
        />
        <KPICard
          title="Top Waste Type"
          value={CATEGORY_LABELS[stats.top_category]}
          subtitle="Most detected"
          icon={<Package size={16} />}
        />
        <KPICard
          title="Avg Eco Score"
          value={stats.avg_eco_score}
          subtitle="Last 7 days"
          icon={<TrendingUp size={16} />}
          color={getScoreColor(stats.avg_eco_score)}
        />
        <KPICard
          title="Correctly Sorted"
          value={`${stats.sorted_correctly_pct}%`}
          subtitle="Accuracy rate"
          icon={<CheckCircle size={16} />}
        />
      </div>

      {/* Trend chart */}
      <TrendChart data={stats.daily_scans} />

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <WasteDonut data={stats.category_distribution} />
        <DailyBarChart data={stats.daily_scans} />
      </div>

      {/* Scan history */}
      <ScanHistory scans={MOCK_SCAN_HISTORY} />
    </div>
  );
}
