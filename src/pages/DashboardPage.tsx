import { useEffect, useState } from "react";
import { ScanLine, TrendingUp, Award, CheckCircle, Package } from "lucide-react";
import { KPICard } from "@/components/Dashboard/KPICard";
import { WasteDonut } from "@/components/Dashboard/WasteDonut";
import { DailyBarChart } from "@/components/Dashboard/DailyBarChart";
import { TrendChart } from "@/components/Dashboard/TrendChart";
import { ScanHistory } from "@/components/Dashboard/ScanHistory";
import { getDashboardStats, getScanHistory } from "@/services/api";
import { CATEGORY_LABELS } from "@/utils/colorMap";
import { getScoreColor } from "@/utils/ecoScore";
import type { DashboardStats, ScanResult } from "@/types/detection";

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [history, setHistory] = useState<ScanResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const [s, h] = await Promise.all([getDashboardStats(), getScanHistory()]);
        setStats(s);
        setHistory(h);
      } catch (err: any) {
        setError(err.message || "Failed to load dashboard");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="dot-wave"><span /><span /><span /></div>
        <span className="text-xs font-mono text-text-muted ml-3">Loading dashboard…</span>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] text-center p-8">
        <p className="text-sm font-mono text-accent-red">{error || "No data available"}</p>
        <p className="text-xs font-mono text-text-muted mt-2">Make sure the backend is running and scan some images first.</p>
      </div>
    );
  }

  return (
    <div className="p-4 md:p-6 space-y-6 max-w-[1400px] mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-heading font-bold text-text-primary">Waste Intelligence</h1>
        <p className="text-xs font-mono text-text-muted mt-1">Live Dashboard</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="Total Scans"
          value={(stats.total_scans || 0).toLocaleString()}
          subtitle={`+${stats.total_today || 0} today`}
          icon={<ScanLine size={16} />}
        />
        <KPICard
          title="Top Waste Type"
          value={stats.top_category ? (CATEGORY_LABELS[stats.top_category] ?? stats.top_category) : "N/A"}
          subtitle="Most detected"
          icon={<Package size={16} />}
        />
        <KPICard
          title="Avg Eco Score"
          value={stats.avg_eco_score || 0}
          subtitle="Last 7 days"
          icon={<TrendingUp size={16} />}
          color={getScoreColor(stats.avg_eco_score || 0)}
        />
        <KPICard
          title="Correctly Sorted"
          value={`${stats.sorted_correctly_pct || 0}%`}
          subtitle="Accuracy rate"
          icon={<CheckCircle size={16} />}
        />
      </div>

      {/* Trend chart */}
      <TrendChart data={stats.daily_trend} />

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <WasteDonut data={stats.category_distribution || {}} />
        <DailyBarChart data={stats.daily_trend || []} />
      </div>

      {/* Scan history */}
      <ScanHistory scans={history} />
    </div>
  );
}

