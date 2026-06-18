#!/usr/bin/env python3
"""Vercel serverless entrypoint at the REPO ROOT.

Lets you deploy the DiscoveryGap repo to Vercel with zero project-setting tweaks
(no Root Directory change): Vercel reads ./vercel.json, builds the frontend under
redrob-ranker/frontend, and routes /health, /demo, /rank to this function.

The engine package lives in redrob-ranker/src; config.ROOT resolves to
redrob-ranker from there, so data/ and eval/ paths are correct in the bundle.
(There is an equivalent redrob-ranker/api/index.py for the alternative setup
where the Vercel Root Directory is set to redrob-ranker.)
"""
from __future__ import annotations
import io, gzip, json, zipfile, sys
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "redrob-ranker" / "src"))
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
    p = C.ROOT / "eval" / "dashboard.json"
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
