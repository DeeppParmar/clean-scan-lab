import axios from "axios";
import type { ScanResult, DashboardStats, HealthStatus } from "@/types/detection";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
  timeout: 30000,
});

export async function analyzeScan(file: File): Promise<ScanResult> {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await api.post<ScanResult>("/api/scan", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function getDashboardStats(): Promise<DashboardStats> {
  const { data } = await api.get<DashboardStats>("/api/dashboard/stats");
  return data;
}

export async function getScanHistory(
  offset: number = 0,
  limit: number = 20,
  category?: string
): Promise<ScanResult[]> {
  const { data } = await api.get<ScanResult[]>("/api/scans", {
    params: { offset, limit, category },
  });
  return data;
}

export async function checkHealth(): Promise<HealthStatus> {
  const { data } = await api.get<HealthStatus>("/health");
  return data;
}

export default api;
