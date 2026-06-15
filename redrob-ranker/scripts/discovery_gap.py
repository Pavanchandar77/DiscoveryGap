#!/usr/bin/env python3
"""Discovery-Gap demo: contrast the naive baseline vs our gated ranker.

Shows how many honeypots / keyword-stuffers the naive embedding ranker pulls into the
top-100 that our system removes, and surfaces 'hidden gems' our system lifts. Produces
eval/discovery_gap.md for the pitch / methodology writeup.
Usage: python scripts/discovery_gap.py --submission submission.csv
"""
from __future__ import annotations
import argparse, csv, sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from redrob_ranker.baseline import rank_baseline  # noqa: E402

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--submission", required=True)
    a = ap.parse_args()
    labels = pd.read_parquet(Path(__file__).resolve().parents[1] / "eval" / "self_labels.parquet")
    hp = set(labels.loc[labels.is_honeypot, "candidate_id"])
    stf = set(labels.loc[labels.is_stuffer, "candidate_id"])

    base = rank_baseline()["candidate_id"].tolist()
    ours = [row["candidate_id"] for row in csv.DictReader(open(a.submission))]

    base_hp = sum(i in hp for i in base[:100]); base_stf = sum(i in stf for i in base[:100])
    our_hp = sum(i in hp for i in ours[:100]); our_stf = sum(i in stf for i in ours[:100])
    lifted = [i for i in ours[:50] if i not in base[:50]]

    md = f"""# Discovery Gap: naive baseline vs gated ranker

| metric | naive baseline | our ranker |
|---|---|---|
| honeypots in top-100 | {base_hp} | {our_hp} |
| keyword-stuffers in top-100 | {base_stf} | {our_stf} |

The baseline is a pure embedding-similarity ranker — what most teams build. It walks into
the traps the dataset was engineered around. Our gated ranker removes them via the title
veto, honeypot logic gate, and behavioral down-weighting.

**Hidden gems we lifted into the top-50 that the baseline missed:** {len(lifted)}
({', '.join(lifted[:10])}{'...' if len(lifted) > 10 else ''})
"""
    out = Path(__file__).resolve().parents[1] / "eval" / "discovery_gap.md"
    out.write_text(md); print(md); print("wrote", out)

if __name__ == "__main__":
    main()
