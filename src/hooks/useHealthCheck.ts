import { useState, useEffect, useCallback } from "react";
import type { HealthStatus } from "@/types/detection";

export function useHealthCheck() {
  const [health, setHealth] = useState<HealthStatus>({
    status: "ok",
    model_loaded: true,
    db_connected: true,
  });

  const check = useCallback(() => {
    // In production this would call checkHealth() from api.ts
    // For now, simulate healthy status
    setHealth({ status: "ok", model_loaded: true, db_connected: true });
  }, []);

  useEffect(() => {
    check();
    const interval = setInterval(check, 30000);
    return () => clearInterval(interval);
  }, [check]);

  return health;
}
