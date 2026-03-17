export function getScoreColor(score: number): string {
  if (score <= 40) return "#E84040";
  if (score <= 70) return "#F5A623";
  return "#3DDA84";
}

export function getScoreTier(score: number): "low" | "mid" | "high" {
  if (score <= 40) return "low";
  if (score <= 70) return "mid";
  return "high";
}
