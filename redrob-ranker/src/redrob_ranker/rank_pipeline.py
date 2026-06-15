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


def run(candidates_path: str, out_path: str) -> None:
    candidates_path = Path(candidates_path)
    raws = _load_candidates(candidates_path)

    meta = pd.read_parquet(C.CAND_META)            # row order == cand_vecs order
    cand_vecs = np.load(C.CAND_VECS)
    jd_vec = np.load(C.JD_VEC)
    sem_all = cosine_to_jd(cand_vecs, jd_vec)       # (N,)

    # map candidate_id -> semantic via meta order
    id_to_sem = dict(zip(meta["candidate_id"].tolist(), sem_all.tolist()))

    scored = []
    for raw in raws:
        cand = Candidate(raw)
        sem = float(id_to_sem.get(cand.id, 0.0))
        scored.append((cand, score_candidate(cand, sem)))

    # exclude honeypots entirely from contention (defensive; score is already 0)
    contenders = [(c, s) for (c, s) in scored if not s["is_honeypot"]]

    # Round FIRST, then sort by (rounded_score desc, candidate_id asc). Rounding before the
    # sort is essential: the official validator requires that equal *displayed* scores are
    # ordered by candidate_id ascending. Sorting on raw scores and rounding afterward can
    # produce equal displayed scores in the wrong id order.
    for _, s in contenders:
        s["rscore"] = round(s["score"], C.SCORE_DECIMALS)
    contenders.sort(key=lambda cs: (-cs[1]["rscore"], cs[0].id))
    top = contenders[: C.TOP_K]

    rows_out = []
    for i, (cand, s) in enumerate(top, start=1):
        sc = s["rscore"]
        text = reasoning.make(cand, s, i)
        rows_out.append([cand.id, i, f"{sc:.{C.SCORE_DECIMALS}f}", text])

    out_path = Path(out_path)
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(C.SUBMISSION_HEADER)
        w.writerows(rows_out)
    print(f"wrote {len(rows_out)} rows to {out_path}")
