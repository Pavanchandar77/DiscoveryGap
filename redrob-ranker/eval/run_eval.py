#!/usr/bin/env python3
"""Score a submission.csv against the self-labeled set + report trap proxies.

Usage: python eval/run_eval.py --submission submission.csv
"""
from __future__ import annotations
import argparse, csv, sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
import metrics  # noqa: E402


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--submission", required=True)
    a = ap.parse_args()
    labels = pd.read_parquet(Path(__file__).resolve().parent / "self_labels.parquet")
    tier = dict(zip(labels.candidate_id, labels.tier))
    hp = set(labels.loc[labels.is_honeypot, "candidate_id"])
    stf = set(labels.loc[labels.is_stuffer, "candidate_id"])

    ids = []
    with open(a.submission) as f:
        r = csv.DictReader(f)
        for row in r:
            ids.append(row["candidate_id"])
    rels = [float(tier.get(i, 0)) for i in ids]
    m = metrics.composite(rels)
    t = metrics.trap_proxies(ids, hp, stf)
    print("=== composite (vs self-labels, NOT hidden truth) ===")
    for k, v in m.items(): print(f"  {k:10s} {v:.4f}")
    print("=== trap proxies (these must be safe) ===")
    print(f"  honeypot_rate@100 {t['honeypot_rate@100']:.3f}  (MUST be 0.0; >0.10 disqualifies)")
    print(f"  stuffer_rate@10   {t['stuffer_rate@10']:.3f}  (lower is better)")


if __name__ == "__main__":
    main()
