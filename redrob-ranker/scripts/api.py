#!/usr/bin/env python3
"""Talent Market Intelligence — backend API.

The seam between the frontend and the ranking engine. A frontend (e.g. built in Google AI
Studio) POSTs a candidates file (.zip / .jsonl / .jsonl.gz) and renders the dashboard JSON it
gets back — it never needs to know how ranking works.

Endpoints:
  GET  /health        -> {"status": "ok"}
  GET  /demo          -> the precomputed full-100K dashboard (eval/dashboard.json), if present
  POST /rank          -> multipart file upload -> dashboard JSON (see src/redrob_ranker/service.py)

Run:  uvicorn scripts.api:app --host 0.0.0.0 --port 8000   (from the repo root)
"""
from __future__ import annotations
import io, gzip, json, zipfile, sys
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from redrob_ranker import config as C            # noqa: E402
from redrob_ranker import service                 # noqa: E402

app = FastAPI(title="Talent Market Intelligence API", version="1.0")
# Open CORS so a frontend on any origin (AI Studio, localhost, your domain) can call it.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

MAX_CANDIDATES = 100_000


def _jd_text() -> str:
    p = C.DATA / "job_description.txt"
    return p.read_text(encoding="utf-8") if p.exists() else (
        "Senior AI Engineer — embeddings, retrieval, ranking, evaluation, production ML at a "
        "product company.")


def _extract_jsonl(filename: str, data: bytes) -> list[dict]:
    name = (filename or "").lower()
    if name.endswith(".zip"):
        zf = zipfile.ZipFile(io.BytesIO(data))
        members = [n for n in zf.namelist() if n.lower().endswith(".jsonl")]
        if not members:
            raise HTTPException(400, "No .jsonl file found inside the zip.")
        # prefer one named like candidates*
        members.sort(key=lambda n: (("candidate" not in n.lower()), len(n)))
        data = zf.read(members[0])
    elif name.endswith(".gz"):
        data = gzip.decompress(data)
    try:
        return [json.loads(l) for l in data.decode("utf-8").splitlines() if l.strip()]
    except Exception as e:
        raise HTTPException(400, f"Could not parse JSONL: {e}")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/demo")
def demo():
    p = ROOT / "eval" / "dashboard.json"
    if not p.exists():
        raise HTTPException(404, "No demo dashboard yet. Run scripts/market_dashboard.py --json eval/dashboard.json")
    return json.loads(p.read_text())


@app.post("/rank")
async def rank(file: UploadFile = File(...), top_k: int = Query(100, ge=1, le=100)):
    raws = _extract_jsonl(file.filename or "upload.jsonl", await file.read())
    if not raws:
        raise HTTPException(400, "No candidate records found.")
    if len(raws) > MAX_CANDIDATES:
        raise HTTPException(413, f"Too many candidates ({len(raws)} > {MAX_CANDIDATES}).")
    return service.rank_and_dashboard(raws, _jd_text(), top_k=top_k)
