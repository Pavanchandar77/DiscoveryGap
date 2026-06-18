# Deploy — one Vercel project (frontend + ranking API)

This repo ships the whole product as a **single Vercel project**: the Discovery
dashboard (static Vite build, served by Vercel's CDN) and the ranking API (one
Python serverless function). No second service, no env vars, same origin.

```
GET  /            -> dashboard SPA            (static, redrob-ranker/frontend/dist)
GET  /health      -> {"status":"ok"}          ┐
GET  /demo        -> dashboard JSON           ├─ rewritten to api/index.py (FastAPI)
POST /rank        -> dashboard JSON           ┘
```

## Deploy (default — nothing to configure)

1. Make sure `main` has this commit (the `vercel.json` + `api/` at the repo root).
2. Vercel → **Add New… → Project** → import **`Pavanchandar77/DiscoveryGap`**.
3. Leave **Root Directory = `./`** (repo root). Framework preset = **Other**.
   Build Command / Output Directory are read from `vercel.json` — leave them blank.
4. **Deploy.**

That's it. Vercel:
- runs `cd redrob-ranker/frontend && npm install && npm run build` → static output,
- installs `api/requirements.txt` (fastapi + numpy + python-multipart) and deploys
  `api/index.py` as a function,
- rewrites `/health`, `/demo`, `/rank` to that function.

### Alternative — Root Directory = `redrob-ranker`
If you'd rather scope the project to the engine folder, set **Root Directory =
`redrob-ranker`** instead. That uses `redrob-ranker/vercel.json` +
`redrob-ranker/api/index.py` (equivalent setup). Use **one** of the two — not both.

## After deploy

- **Dashboard**: the project URL.
- **See demo**: calls `GET /demo`. Until a real `eval/dashboard.json` is bundled
  (see below) this returns 404 and the UI **falls back to a curated sample**, so
  the page still looks complete.
- **Upload**: runs the **real ranking engine** on your file. Vercel caps request
  bodies at **~4.5 MB**, so use a small/medium sample here. The full-100K story is
  the demo view.
- **Try-it sample**: the landing page links a ready 654-candidate pool
  (`/sample_candidates.jsonl`, ~1.2 MB) so anyone can test the upload immediately —
  it ranks to 57% mispriced / 43% efficiency, 0 stuffers in our top, honeypots
  removed. Regenerate with `python redrob-ranker/scripts/make_sample_candidates.py`.

## Env vars
None required — the frontend calls the API on relative, same-origin URLs.
(Optional: set `VITE_API_BASE_URL` only if you ever host the API on a different
host.)

## Make “See demo” show real data (optional)
`/demo` serves `redrob-ranker/eval/dashboard.json` if present. Generate it from the
real pool with the offline (BGE) embeddings, then commit it:

```bash
cd redrob-ranker
pip install -r requirements.txt
python scripts/precompute.py                 # offline embeddings -> artifacts/
python scripts/market_dashboard.py --json eval/dashboard.json
```

(Do **not** commit candidate data or model weights — just the resulting
`dashboard.json`.) A synthetic sample is intentionally avoided: the request-time
embed backend is non-semantic, so a faked demo would misrank.

## Local dev
```bash
# API (terminal 1)
cd redrob-ranker
pip install -r requirements.txt -r scripts/api_requirements.txt
uvicorn scripts.api:app --port 8000

# Frontend (terminal 2) — /demo,/rank proxied to :8000
cd redrob-ranker/frontend && npm install && npm run dev   # http://localhost:3000
```

## Ranking accuracy (which embedder runs)
Live `/rank` uses an embedding backend chosen by `REDROB_EMBED_BACKEND`:
- **`hashing`** (default) — fast, self-contained, numpy-only. Used on Vercel. Trap
  detection (stuffers, honeypots, title-veto, evidence) is fully active; pure semantic
  relevance is approximate.
- **`auto` / `bge`** — the semantic model (BAAI/bge-small-en-v1.5) that matches the
  validated offline pipeline. Needs `torch` + `sentence-transformers` (too heavy for a
  Vercel function), so use it on the Docker/Render build:
  ```bash
  docker build -f redrob-ranker/Dockerfile.web \
    --build-arg ACCURATE=true --build-arg EMBED_BACKEND=auto -t discovery-web redrob-ranker
  ```
The most accurate, instant story is always the precomputed **/demo** (full 100K with BGE).
See [`RESPONSIBLE_AI.md`](RESPONSIBLE_AI.md) for explainability and fairness posture.

## Other hosts
Prefer a long-running container (no 4.5 MB upload cap, large `/rank` works)? Use
[`redrob-ranker/Dockerfile.web`](redrob-ranker/Dockerfile.web) — FastAPI serves
the built frontend + API on `$PORT`. [`render.yaml`](render.yaml) deploys it on
Render in one click; the same image runs on Railway / Fly / Cloud Run.
