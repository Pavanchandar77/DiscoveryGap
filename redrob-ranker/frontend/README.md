# Discovery — Talent Market Intelligence (frontend)

Hiring systems misprice talent. Traditional ATS / keyword pipelines reward
visibility, so high-signal candidates get buried. **Discovery** ranks a pool of
candidates for a fixed *Senior AI Engineer* role and surfaces the ones the ATS
systematically undervalues — with a **Talent Mispricing Index (TMI)**,
**Conviction**, **Evidence Density**, **Fit**, **Hidden Gems** and a
**Market Efficiency** read.

This repo is the **frontend only**. It never reimplements ranking — it uploads a
candidates file to the backend engine and renders the dashboard JSON it returns.

## Architecture

```
Upload ZIP/JSONL  ─▶  POST /rank  ─▶  ranking engine  ─▶  dashboard JSON  ─▶  6 screens
"See demo"        ─▶  GET  /demo  ─▶  precomputed 100K dashboard JSON  ─────────┘
```

The only coupling between frontend and backend is the JSON contract documented in
the backend repo (`redrob-ranker/FRONTEND_CONTRACT.md`). Either side can change
independently as long as the shape holds.

## Screens (each reads only the contract fields)

1. **Insights / hero dashboard** — `market_efficiency_pct`, `mispriced_pct`, `hidden_gems`, `avg_tmi`, `highest_tmi`
2. **ATS failure (hero)** — `hero.ats_rank → hero.our_rank`, `hero.tmi`, `trust_drivers`, `concerns`
3. **Conviction cards** — `cards[]`: fit / conviction / tmi / evidence_density / quadrant + drivers/concerns
4. **The bet map** — scatter `cards[]` on `fit` (x) × `conviction` (y), bubble = `tmi`, colour = `quadrant`
5. **ATS vs us** — `ats_top10` vs `our_top10`, `stuffers_in_ats_top` vs `stuffers_in_our_top`
6. **Download** — builds the 4-column submission CSV from `cards` (`candidate_id, rank, score=fit/100, reasoning`)

## Run locally

**Prerequisites:** Node.js, and the backend API running (see the `discoverygap`
repo, `redrob-ranker/`).

This frontend lives **inside the backend repo** (`redrob-ranker/frontend/`). In
production the FastAPI app serves the built `dist/` so the dashboard and the API
share one origin — see the repo root README for the single-service deploy.

```bash
# from redrob-ranker/ : start the API on :8000 first, then:
cd frontend
npm install
npm run dev          # http://localhost:3000 — /demo,/rank are proxied to :8000
```

### Configuration

The app calls the API on **relative, same-origin URLs** (`/demo`, `/rank`):
- In dev, `vite.config.ts` proxies those paths to `http://localhost:8000`.
- In production, FastAPI serves this build and the API from the same host.

| Env var | Default | Purpose |
|---|---|---|
| `VITE_API_BASE_URL` | `""` (same origin) | Override only to point at an API on a different host |

- **See demo** → `GET /demo` (instant, precomputed 100K dashboard)
- **Upload** → `POST /rank?top_k=100` with multipart field `file` (`.zip` / `.jsonl` / `.jsonl.gz`)

If the API is unreachable the UI falls back to bundled mock data so the
interface still renders (useful for design previews without a backend).

## Build

```bash
npm run build      # outputs dist/
npm run preview    # serve the production build
npm run lint       # tsc --noEmit
```

## Stack

React 19 + TypeScript, Vite 6, Tailwind CSS v4, Framer Motion, Recharts,
lucide-react.
