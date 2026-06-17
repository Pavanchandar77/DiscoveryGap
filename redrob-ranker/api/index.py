#!/usr/bin/env python3
"""Vercel serverless entrypoint — the ranking API as one Python function.

Vercel serves the built frontend (frontend/dist) as static files on the CDN; the
three API paths (/health, /demo, /rank) are rewritten to this function (see
vercel.json). The engine is numpy-only at request time (deterministic hashing
embed backend), so this fits comfortably in a serverless function.

Note: Vercel caps request bodies at ~4.5 MB, so /rank here suits small/medium
sample uploads; the full-100K story is the precomputed /demo dashboard.
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
        raise HTTPException(404, "No demo dashboard bundled. Generate eval/dashboard.json to enable it.")
    return json.loads(p.read_text())


@app.post("/rank")
async def rank(file: UploadFile = File(...), top_k: int = Query(100, ge=1, le=100)):
    raws = _extract_jsonl(file.filename or "upload.jsonl", await file.read())
    if not raws:
        raise HTTPException(400, "No candidate records found.")
    if len(raws) > MAX_CANDIDATES:
        raise HTTPException(413, f"Too many candidates ({len(raws)} > {MAX_CANDIDATES}).")
    return service.rank_and_dashboard(raws, _jd_text(), top_k=top_k)
