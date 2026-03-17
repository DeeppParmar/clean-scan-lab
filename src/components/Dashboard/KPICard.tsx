import { cn } from "@/lib/utils";

interface Props {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  color?: string;
  loading?: boolean;
}

export function KPICard({ title, value, subtitle, icon, color, loading }: Props) {
  if (loading) {
    return (
      <div className="bg-bg-surface border border-border rounded-xl p-5 space-y-3 animate-pulse">
        <div className="h-3 w-20 bg-border/30 rounded" />
        <div className="h-7 w-16 bg-border/30 rounded" />
        <div className="h-2.5 w-24 bg-border/20 rounded" />
      </div>
    );
  }

  return (
    <div className="bg-bg-surface border border-border rounded-xl p-5 transition-all duration-200 hover:border-border/80">
      <div className="flex items-center justify-between mb-3">
        <span className="text-[10px] font-mono text-text-muted uppercase tracking-wider">{title}</span>
        <div className="text-text-muted/40">{icon}</div>
      </div>
      <p className={cn("text-2xl font-heading font-bold tabular-nums", color ? "" : "text-text-primary")} style={color ? { color } : undefined}>
        {value}
      </p>
      {subtitle && <p className="text-[10px] font-mono text-text-muted mt-1">{subtitle}</p>}
    </div>
  );
}
