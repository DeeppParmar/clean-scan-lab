import { NavLink, useLocation } from "react-router-dom";
import { ScanLine, BarChart3, Info, Github, ChevronLeft, ChevronRight, Leaf } from "lucide-react";
import { useHealthCheck } from "@/hooks/useHealthCheck";
import { cn } from "@/lib/utils";

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

const navItems = [
  { to: "/", label: "Scanner", icon: ScanLine },
  { to: "/dashboard", label: "Dashboard", icon: BarChart3 },
  { to: "/about", label: "About", icon: Info },
];

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const location = useLocation();
  const health = useHealthCheck();

  const healthColor =
    health.status === "ok" ? "bg-accent-green" : health.status === "degraded" ? "bg-accent-amber" : "bg-accent-red";
  const healthText =
    health.status === "ok" ? "Model ready" : health.status === "degraded" ? "Loading" : "Offline";

  return (
    <aside
      className={cn(
        "hidden md:flex flex-col h-full bg-bg-surface/80 backdrop-blur-xl border-r border-border transition-all duration-300 ease-in-out shrink-0 relative z-50",
        collapsed ? "w-16" : "w-60"
      )}
    >
      {/* Logo */}
      <div className="flex items-center h-14 px-4 border-b border-border gap-2.5">
        <div className="shrink-0 w-8 h-8 flex items-center justify-center">
          <svg viewBox="0 0 32 32" fill="none" className="w-7 h-7">
            <circle cx="16" cy="16" r="14" stroke="hsl(var(--accent-green))" strokeWidth="1.5" fill="none" />
            <path d="M16 6c0 8-6 12-6 18h12c0-6-6-10-6-18z" fill="hsl(var(--accent-green))" fillOpacity="0.2" stroke="hsl(var(--accent-green))" strokeWidth="1.5" strokeLinejoin="round" />
            <circle cx="16" cy="16" r="4" stroke="hsl(var(--accent-green))" strokeWidth="1.5" fill="none" />
          </svg>
        </div>
        {!collapsed && <span className="font-heading font-bold text-base text-text-primary tracking-tight">EcoLens</span>}
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-3 px-2 space-y-1">
        {navItems.map((item) => {
          const isActive = location.pathname === item.to;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-all duration-300 relative group overflow-hidden",
                isActive
                  ? "bg-accent-green/10 text-accent-green"
                  : "text-text-muted hover:text-text-primary"
              )}
              aria-label={item.label}
            >
              {!isActive && <div className="absolute inset-0 bg-white/5 translate-y-full group-hover:translate-y-0 transition-transform duration-300 ease-out z-0" />}
              <item.icon size={18} className="shrink-0 relative z-10" />
              {!collapsed && <span className="font-heading font-medium tracking-wide relative z-10">{item.label}</span>}
            </NavLink>
          );
        })}
      </nav>

      {/* Bottom section */}
      <div className="px-3 pb-3 space-y-3 border-t border-border pt-3">
        {/* Health indicator */}
        <div className={cn("flex items-center gap-2.5 px-2", collapsed && "justify-center")}>
          <div className={cn("w-2 h-2 rounded-full shrink-0", healthColor)} />
          {!collapsed && <span className="text-[10px] font-mono text-text-muted uppercase tracking-wider">{healthText}</span>}
        </div>

        {!collapsed && (
          <p className="text-[9px] font-mono text-text-muted/60 px-2 uppercase tracking-widest">
            Powered by YOLOv8
          </p>
        )}

        <div className={cn("flex items-center", collapsed ? "justify-center" : "justify-between px-2")}>
          <a
            href="https://github.com"
            target="_blank"
            rel="noopener noreferrer"
            className="text-text-muted hover:text-text-primary transition-colors"
            aria-label="GitHub repository"
          >
            <Github size={16} />
          </a>
          {!collapsed && (
            <button
              onClick={onToggle}
              className="text-text-muted hover:text-text-primary transition-colors"
              aria-label="Collapse sidebar"
            >
              <ChevronLeft size={16} />
            </button>
          )}
        </div>

        {collapsed && (
          <button
            onClick={onToggle}
            className="flex justify-center text-text-muted hover:text-text-primary transition-colors w-full"
            aria-label="Expand sidebar"
          >
            <ChevronRight size={16} />
          </button>
        )}
      </div>
    </aside>
  );
}
