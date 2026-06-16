#!/usr/bin/env python3
"""Talent Conviction Engine — text demo of the per-candidate cards (no Streamlit needed).

Prints Fit / Conviction / Discovery Gap + the quadrant, Trust Drivers and Concerns for the
top candidates. Mirrors what the sandbox shows visually.

Usage: python scripts/conviction_demo.py --submission submission.csv --n 6
"""
from __future__ import annotations
import argparse, csv, json, sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from redrob_ranker import config as C                  # noqa: E402
from redrob_ranker.schema import Candidate              # noqa: E402
from redrob_ranker.embed import cosine_to_jd, pool_normalize  # noqa: E402
from redrob_ranker.score import score_candidate         # noqa: E402
from redrob_ranker import presentation                  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--submission", required=True); ap.add_argument("--n", type=int, default=6)
    a = ap.parse_args()
    raws = {r["candidate_id"]: r for r in
            (json.loads(l) for l in open(ROOT / "data" / "candidates.jsonl") if l.strip())}
    meta = pd.read_parquet(C.CAND_META)
    sem_raw = cosine_to_jd(np.load(C.CAND_VECS), np.load(C.JD_VEC))
    ats = meta.assign(s=sem_raw).sort_values(["s", "candidate_id"], ascending=[False, True])
    ats_rank = {c: i + 1 for i, c in enumerate(ats["candidate_id"].tolist())}
    sem = dict(zip(meta.candidate_id, pool_normalize(sem_raw).tolist()))
    ours = [row["candidate_id"] for row in csv.DictReader(open(a.submission))]

    print("=" * 64)
    print("  TALENT CONVICTION ENGINE")
    print("  Fit = relevance · Conviction = certainty · TMI = positions the ATS underprices them")
    print("=" * 64)
    for i, cid in enumerate(ours[:a.n], 1):
        c = Candidate(raws[cid])
        s = score_candidate(c, sem.get(cid, 0.0)); s["rscore"] = round(s["score"], 4)
        card = presentation.card(c, s, i, ats_rank.get(cid))
        tmi = card["tmi"]
        print(f"\n#{card['our_rank']}  {card['title']}   [{card['quadrant']}]")
        print(f"   Fit {card['fit']}   |   Conviction {card['conviction']}%   |   "
              f"Talent Mispricing Index {tmi:+d}  (ATS rank {card['ats_rank']}, "
              f"undervalued by {tmi} positions)")
        print(f"   Evidence Density {card['evidence_density']}%  "
              f"({card['verified_skills']}/{card['claimed_skills']} skills supported)")
        for d in card["trust_drivers"]:
            print(f"   ✓ {d}")
        for cn in card["concerns"]:
            print(f"   ⚠ {cn}")


if __name__ == "__main__":
    main()
