"""Naive embedding-only baseline — the CONTRAST OBJECT for the Discovery-Gap demo.

This is intentionally dumb: rank purely by cosine(JD, candidate text), no traps handled.
It reproduces what most teams build, and lets us show how many keyword-stuffers and
honeypots it drags into the top-100 that our gated system removes.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from . import config as C
from .embed import cosine_to_jd


def rank_baseline() -> pd.DataFrame:
    meta = pd.read_parquet(C.CAND_META)
    vecs = np.load(C.CAND_VECS)
    jd = np.load(C.JD_VEC)
    sem = cosine_to_jd(vecs, jd)
    meta = meta.assign(semantic=sem).sort_values(
        ["semantic", "candidate_id"], ascending=[False, True]
    )
    return meta.head(C.TOP_K).reset_index(drop=True)
