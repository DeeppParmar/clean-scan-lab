import { Leaf, Github, Zap, Eye, Shield, BarChart3 } from "lucide-react";

export default function AboutPage() {
  return (
    <div className="p-4 md:p-6 max-w-3xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-heading font-bold text-text-primary">About EcoLens</h1>
        <p className="text-sm font-mono text-text-muted mt-2 leading-relaxed">
          EcoLens is an AI-powered waste classification and recycling assistant built as part of the
          Microsoft 2026 Sustainability Initiative. It uses state-of-the-art computer vision to identify
          waste materials in real-time and provide actionable recycling guidance.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {[
          { icon: Eye, title: "Real-Time Detection", desc: "YOLOv8-based object detection with sub-second inference" },
          { icon: Zap, title: "Instant Classification", desc: "6 waste categories with confidence scoring" },
          { icon: Shield, title: "Eco Scoring", desc: "Composite sustainability rating per scan" },
          { icon: BarChart3, title: "Analytics", desc: "Track waste patterns and recycling efficiency" },
        ].map((f) => (
          <div key={f.title} className="bg-bg-surface border border-border rounded-xl p-5">
            <f.icon size={20} className="text-accent-green mb-3" />
            <h3 className="font-heading font-semibold text-sm text-text-primary">{f.title}</h3>
            <p className="text-[11px] font-mono text-text-muted mt-1 leading-relaxed">{f.desc}</p>
          </div>
        ))}
      </div>

      <div className="bg-bg-surface border border-border rounded-xl p-5">
        <h3 className="font-heading font-semibold text-sm text-text-primary mb-2">Tech Stack</h3>
        <div className="flex flex-wrap gap-2">
          {["React 18", "TypeScript", "YOLOv8", "FastAPI", "Tailwind CSS", "Recharts"].map((t) => (
            <span key={t} className="text-[10px] font-mono text-text-muted px-2.5 py-1 bg-muted/30 rounded-md border border-border/50">
              {t}
            </span>
          ))}
        </div>
      </div>

      <div className="flex items-center gap-3 pt-2">
        <a
          href="https://github.com"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 text-xs font-mono text-text-muted hover:text-accent-green transition-colors"
        >
          <Github size={16} /> View on GitHub
        </a>
      </div>
    </div>
  );
}
