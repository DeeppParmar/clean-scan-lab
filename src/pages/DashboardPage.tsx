import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { ScanLine, TrendingUp, Award, CheckCircle, Package, Settings2 } from "lucide-react";
import { KPICard } from "@/components/Dashboard/KPICard";
import { WasteDonut } from "@/components/Dashboard/WasteDonut";
import { DailyBarChart } from "@/components/Dashboard/DailyBarChart";
import { TrendChart } from "@/components/Dashboard/TrendChart";
import { ScanHistory } from "@/components/Dashboard/ScanHistory";
import { getDashboardStats, getScanHistory, setApiUrl } from "@/services/api";
import { CATEGORY_LABELS } from "@/utils/colorMap";
import { getScoreColor } from "@/utils/ecoScore";
import type { DashboardStats, ScanResult } from "@/types/detection";

const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.1 } }
};

const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 24 } }
};

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
      <div className="flex flex-col items-center justify-center h-[60vh] text-center p-8 max-w-md mx-auto">
        <div className="w-12 h-12 rounded-full bg-surface-elevated/50 flex items-center justify-center mb-4 border border-element/20">
           <Settings2 className="text-text-muted" size={24} />
        </div>
        <p className="text-sm font-mono text-accent-red">{error || "No data available"}</p>
        <p className="text-xs font-mono text-text-muted mt-2">Make sure the backend is running, or provide your Ngrok URL if testing remotely.</p>
        
        <form 
          className="mt-6 w-full flex gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            const input = new FormData(e.currentTarget).get('url') as string;
            if (input) {
              setApiUrl(input.trim());
              window.location.reload();
            }
          }}
        >
          <input 
            name="url"
            type="url" 
            placeholder="e.g. https://*.ngrok-free.dev" 
            className="flex-1 bg-surface text-text-primary px-3 py-2 rounded text-sm outline-none border border-element/50 focus:border-brand-primary placeholder:text-text-muted/50"
            defaultValue={localStorage.getItem("ecolens_api_url") || ""}
          />
          <button 
            type="submit"
            className="px-4 py-2 bg-brand-primary text-background text-sm font-semibold rounded hover:bg-brand-primary/90 transition-colors whitespace-nowrap"
          >
            Connect
          </button>
        </form>
        {localStorage.getItem("ecolens_api_url") && (
          <button 
            type="button"
            onClick={() => { setApiUrl(null); window.location.reload(); }}
            className="mt-4 text-xs text-text-muted hover:text-text-primary transition-colors underline decoration-dotted underline-offset-4"
          >
            Reset to default API URL
          </button>
        )}
      </div>
    );
  }

  return (
    <motion.div 
      className="p-4 md:p-6 space-y-6 max-w-[1400px] mx-auto"
      variants={container}
      initial="hidden"
      animate="show"
    >
      {/* Header */}
      <motion.div variants={item}>
        <h1 className="text-2xl font-heading font-bold text-text-primary">Waste Intelligence</h1>
        <p className="text-xs font-mono text-text-muted mt-1">Live Dashboard</p>
      </motion.div>

      {/* KPI Cards */}
      <motion.div variants={item} className="grid grid-cols-2 lg:grid-cols-4 gap-4">
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
      </motion.div>

      {/* Trend chart */}
      <motion.div variants={item}>
        <TrendChart data={stats.daily_trend} />
      </motion.div>

      {/* Charts row */}
      <motion.div variants={item} className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <WasteDonut data={stats.category_distribution || {}} />
        <DailyBarChart data={stats.daily_trend || []} />
      </motion.div>

      {/* Scan history */}
      <motion.div variants={item}>
        <ScanHistory scans={history} />
      </motion.div>
    </motion.div>
  );
}

