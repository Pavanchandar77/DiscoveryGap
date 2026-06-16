#!/usr/bin/env python3
"""Measure agreement between our ranking and INDEPENDENT human review.

Reads eval/review_sample.csv (with `human_tier (0-4)` filled by a human) + eval/review_key.csv,
and reports whether our ranking agrees with human judgment — the non-circular check that the
self-label metrics cannot give. Surfaces concrete disagreements to inspect.

Usage: python eval/review_agreement.py
"""
from __future__ import annotations
import csv, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]


def main():
    rev = list(csv.DictReader(open(ROOT / "eval" / "review_sample.csv")))
    key = {r["review_id"]: r for r in csv.DictReader(open(ROOT / "eval" / "review_key.csv"))}

    rows = []
    for r in rev:
        raw = (r.get("human_tier (0-4)") or "").strip()
        if raw == "":
            continue
        k = key[r["review_id"]]
        rows.append({"tier": int(float(raw)), "stratum": k["stratum"],
                     "our_rank": int(k["our_rank"]) if k["our_rank"] else None,
                     "cid": k["candidate_id"]})
    if not rows:
        print("No human_tier values filled in eval/review_sample.csv yet."); return

    print(f"reviewed rows scored by human: {len(rows)}\n")
    # mean human tier by stratum — our_top should be high, controls/not_selected low
    strata = {}
    for r in rows:
        strata.setdefault(r["stratum"], []).append(r["tier"])
    print("mean human tier by stratum (our_top should be highest; controls lowest):")
    for s in ["our_top", "our_mid", "our_cutoff", "not_selected", "honeypot_control", "stuffer_control"]:
        v = strata.get(s)
        if v:
            print(f"  {s:18s} n={len(v):2d}  mean={sum(v)/len(v):.2f}")

    # rank vs human-tier agreement (Spearman) for everything that has a rank
    ranked = [r for r in rows if r["our_rank"] is not None]
    if len(ranked) >= 4:
        def rankdata(xs):
            order = sorted(range(len(xs)), key=lambda i: xs[i])
            rk = [0.0] * len(xs)
            for pos, i in enumerate(order): rk[i] = pos + 1
            return rk
        a = rankdata([r["our_rank"] for r in ranked])          # lower our_rank = better
        b = rankdata([-r["tier"] for r in ranked])             # higher tier = better
        n = len(a); d2 = sum((a[i] - b[i]) ** 2 for i in range(n))
        rho = 1 - 6 * d2 / (n * (n * n - 1))
        print(f"\nSpearman(our_rank, human judgment) over {n} ranked rows: rho={rho:.3f}  "
              f"(1.0 = perfect agreement; we WANT positive)")

    # concrete disagreements to eyeball
    fp = [r for r in rows if r["stratum"] in ("our_top", "our_mid") and r["tier"] <= 1]
    miss = [r for r in rows if r["stratum"] == "not_selected" and r["tier"] >= 3]
    print(f"\npotential FALSE POSITIVES (we ranked high, human rated <=1): {len(fp)}")
    for r in fp: print(f"   {r['cid']} our_rank={r['our_rank']} human_tier={r['tier']}")
    print(f"potential MISSES (not selected, human rated >=3): {len(miss)}")
    for r in miss: print(f"   {r['cid']} human_tier={r['tier']}")
    ctrl = [r["tier"] for r in rows if r["stratum"].endswith("control")]
    if ctrl:
        print(f"\ncontrol sanity (honeypots/stuffers — should be ~0): mean={sum(ctrl)/len(ctrl):.2f}")


if __name__ == "__main__":
    main()
