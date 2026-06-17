import { DashboardData } from "./types";
import { MOCK_DASHBOARD_DATA } from "./mockData";

// Base URL of the FastAPI ranking engine.
// Default "" = same origin: in production FastAPI serves this built app and the
// API from one host; in dev, vite proxies /demo, /rank, /health to :8000
// (see vite.config.ts). Override with VITE_API_BASE_URL to point elsewhere.
const API_BASE = (import.meta as any).env.VITE_API_BASE_URL || "";

export async function fetchDemoDashboard(): Promise<DashboardData> {
  try {
    const res = await fetch(`${API_BASE}/demo`);
    if (!res.ok) throw new Error("Demo fetch failed");
    return res.json();
  } catch (err) {
    console.warn("API failed, falling back to mock data", err);
    return new Promise((resolve) => setTimeout(() => resolve(MOCK_DASHBOARD_DATA), 800));
  }
}

export async function uploadCandidatesAndRank(file: File): Promise<DashboardData> {
  try {
    const formData = new FormData();
    formData.append("file", file);

    const res = await fetch(`${API_BASE}/rank?top_k=100`, {
      method: "POST",
      body: formData,
    });

    if (!res.ok) throw new Error("Rank API failed");
    return res.json();
  } catch (err) {
    console.warn("API failed, falling back to mock data", err);
    return new Promise((resolve) => setTimeout(() => resolve(MOCK_DASHBOARD_DATA), 3000));
  }
}
