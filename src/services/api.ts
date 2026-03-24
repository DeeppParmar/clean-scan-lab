import axios from "axios";
import type { ScanResult, DashboardStats, HealthStatus } from "@/types/detection";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
  timeout: 30000,
  headers: {
    "ngrok-skip-browser-warning": "true"
  }
});

export async function analyzeScan(file: File): Promise<ScanResult> {
  // Convert File to base64 string
  const base64Str = await new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = (error) => reject(error);
  });

  const { data } = await api.post<ScanResult>("/api/analyze", {
    image: base64Str,
  });
  return data;
}

export async function getDashboardStats(): Promise<DashboardStats> {
  const { data } = await api.get<DashboardStats>("/api/stats");
  return data;
}

export async function getScanHistory(
  offset: number = 0,
  limit: number = 20,
  category?: string
): Promise<ScanResult[]> {
  const { data } = await api.get<ScanResult[]>("/api/history", {
    params: { offset, limit, category },
  });
  return data;
}

export async function checkHealth(): Promise<HealthStatus> {
  const { data } = await api.get<HealthStatus>("/health");
  return data;
}

export default api;
