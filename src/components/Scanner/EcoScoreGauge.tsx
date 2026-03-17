import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { getScoreColor } from "@/utils/ecoScore";

interface Props {
  score: number;
}

export function EcoScoreGauge({ score }: Props) {
  const [displayScore, setDisplayScore] = useState(0);
  const radius = 45;
  const circumference = 2 * Math.PI * radius;
  const sweep = 220;
  const arcLength = (sweep / 360) * circumference;
  const color = getScoreColor(score);

  useEffect(() => {
    let frame: number;
    const duration = 1200;
    const start = performance.now();
    const animate = (now: number) => {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplayScore(Math.round(eased * score));
      if (progress < 1) frame = requestAnimationFrame(animate);
    };
    frame = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frame);
  }, [score]);

  return (
    <div className="relative flex flex-col items-center justify-center w-36 h-36">
      <svg viewBox="0 0 160 160" className="w-full h-full -rotate-[200deg]">
        <circle
          cx="80" cy="80" r={radius}
          fill="none"
          stroke="hsl(var(--bg-base))"
          strokeWidth="8"
          strokeDasharray={`${arcLength} ${circumference}`}
          strokeLinecap="round"
        />
        <motion.circle
          cx="80" cy="80" r={radius}
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeDasharray={`${arcLength} ${circumference}`}
          strokeLinecap="round"
          initial={{ strokeDashoffset: arcLength }}
          animate={{ strokeDashoffset: arcLength - (score / 100) * arcLength }}
          transition={{ duration: 1.5, ease: "easeOut" }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center pt-2">
        <span className="text-3xl font-heading font-bold tabular-nums" style={{ color }}>
          {displayScore}
        </span>
        <span className="text-[9px] font-mono text-text-muted uppercase tracking-[0.2em]">Eco Score</span>
      </div>
    </div>
  );
}
