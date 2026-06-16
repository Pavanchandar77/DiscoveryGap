"""Orchestration for the online ranking step. Loads precomputed artifacts only.

Guarantees relevant to the HARD RULES:
- emits exactly TOP_K rows, ranks 1..TOP_K unique, score non-increasing,
  ties broken by candidate_id ascending.
- no model load, no network.
"""
from __future__ import annotations
import csv
import json
import numpy as np
import pandas as pd
from pathlib import Path
from . import config as C
from .schema import Candidate
from .embed import cosine_to_jd
from .score import score_candidate
from . import reasoning


def _load_candidates(path: Path) -> list[dict]:
    rows = []
    opener = open
    if str(path).endswith(".gz"):
        import gzip
        opener = lambda p: gzip.open(p, "rt")  # noqa: E731
    with opener(path) as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def rank_records(raws: list[dict], id_to_sem: dict[str, float],
                 top_k: int = C.TOP_K) -> list[list]:
    """Core ranking logic, shared by the artifact-based run() and the sandbox app.

    Given raw candidate dicts and a candidate_id -> JD-semantic-cosine map, returns
    the top_k submission rows: [candidate_id, rank, "score", reasoning]. Honeypots are
    excluded from contention. Rounding happens BEFORE the sort so equal *displayed*
    scores tie-break by candidate_id ascending (required by the official validator).
    """
    scored = []
    for raw in raws:
        cand = Candidate(raw)
        sem = float(id_to_sem.get(cand.id, 0.0))
        scored.append((cand, score_candidate(cand, sem)))

    contenders = [(c, s) for (c, s) in scored if not s["is_honeypot"]]
    for _, s in contenders:
        s["rscore"] = round(s["score"], C.SCORE_DECIMALS)
    contenders.sort(key=lambda cs: (-cs[1]["rscore"], cs[0].id))
    top = contenders[:top_k]

    rows_out = []
    for i, (cand, s) in enumerate(top, start=1):
        text = reasoning.make(cand, s, i)
        rows_out.append([cand.id, i, f"{s['rscore']:.{C.SCORE_DECIMALS}f}", text])
    return rows_out


def write_csv(rows_out: list[list], out_path: str) -> None:
    out_path = Path(out_path)
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(C.SUBMISSION_HEADER)
        w.writerows(rows_out)
    print(f"wrote {len(rows_out)} rows to {out_path}")


def run(candidates_path: str, out_path: str) -> None:
    candidates_path = Path(candidates_path)
    raws = _load_candidates(candidates_path)

    meta = pd.read_parquet(C.CAND_META)            # row order == cand_vecs order
    cand_vecs = np.load(C.CAND_VECS)
    jd_vec = np.load(C.JD_VEC)
    sem_all = cosine_to_jd(cand_vecs, jd_vec)       # (N,)

    # map candidate_id -> semantic via meta order
    id_to_sem = dict(zip(meta["candidate_id"].tolist(), sem_all.tolist()))

    rows_out = rank_records(raws, id_to_sem)
    write_csv(rows_out, out_path)
