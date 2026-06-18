import { DashboardData } from "./types";
import { MOCK_DASHBOARD_DATA } from "./mockData";

// Base URL of the FastAPI ranking engine.
// Default "" = same origin: in production FastAPI serves this built app and the
// API from one host; in dev, vite proxies /demo, /rank, /health to :8000
// (see vite.config.ts). Override with VITE_API_BASE_URL to point elsewhere.
const API_BASE = (import.meta as any).env.VITE_API_BASE_URL || "";

/** A problem the user can act on (bad file, too large, server rejected it). */
export class UploadError extends Error {}

async function errorDetail(res: Response, fallback: string): Promise<string> {
  try {
    const body = await res.json();
    if (body && typeof body.detail === "string") return body.detail;
  } catch {
    /* ignore non-JSON bodies */
  }
  return fallback;
}

export async function fetchDemoDashboard(): Promise<DashboardData> {
  try {
    const res = await fetch(`${API_BASE}/demo`);
    if (!res.ok) throw new Error("Demo fetch failed");
    return res.json();
  } catch (err) {
    // No precomputed demo / no backend reachable -> show the curated sample so the
    // experience still renders. (Demo is illustrative, never a failure the user must fix.)
    console.warn("Demo unavailable, using bundled sample", err);
    return new Promise((resolve) => setTimeout(() => resolve(MOCK_DASHBOARD_DATA), 800));
  }
}

export async function uploadCandidatesAndRank(file: File): Promise<DashboardData> {
  let res: Response;
  try {
    const formData = new FormData();
    formData.append("file", file);
    res = await fetch(`${API_BASE}/rank?top_k=100`, { method: "POST", body: formData });
  } catch (err) {
    // Network / no backend (e.g. design preview): fall back to the sample dashboard.
    console.warn("Engine unreachable, using bundled sample", err);
    return new Promise((resolve) => setTimeout(() => resolve(MOCK_DASHBOARD_DATA), 1500));
  }

  if (res.ok) return res.json();

  // The engine reached us but rejected the file — surface a real, actionable error.
  if (res.status === 413) {
    throw new UploadError(
      "That file is too large for this hosted demo (limit ~4.5 MB). Try a smaller sample, or run the Docker/Render build for the full pool."
    );
  }
  if (res.status >= 400 && res.status < 500) {
    throw new UploadError(
      await errorDetail(res, "We couldn't read that file. Upload a candidates .jsonl / .zip / .jsonl.gz in the expected format.")
    );
  }
  throw new UploadError(await errorDetail(res, "The ranking engine hit an error. Please try again."));
}
