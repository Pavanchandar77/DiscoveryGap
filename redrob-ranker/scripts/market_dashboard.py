#!/usr/bin/env python3
"""Talent Market Intelligence dashboard — the hero numbers + a frontend-ready JSON payload.

Computes Market Efficiency (how much of the top talent the ATS correctly surfaced), Hidden
Gems found, average/highest Talent Mispricing Index, the single biggest ATS failure, the
ATS-vs-us top-10, and the keyword-stuffer comparison. Prints a Bloomberg-style summary and
(with --json) writes everything a frontend needs to render screens 1-5.

Usage:
  python scripts/market_dashboard.py --submission submission.csv [--json eval/dashboard.json]
"""
from __future__ import annotations
import argparse, csv, json, sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from redrob_ranker import config as C                      # noqa: E402
from redrob_ranker.schema import Candidate                  # noqa: E402
from redrob_ranker.embed import cosine_to_jd, pool_normalize  # noqa: E402
from redrob_ranker.score import score_candidate             # noqa: E402
from redrob_ranker import presentation                      # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--submission", required=True); ap.add_argument("--json", default=None)
    a = ap.parse_args()

    raws = {r["candidate_id"]: r for r in
            (json.loads(l) for l in open(ROOT / "data" / "candidates.jsonl") if l.strip())}
    labels = pd.read_parquet(ROOT / "eval" / "self_labels.parquet")
    stuffers = set(labels.loc[labels.is_stuffer, "candidate_id"])

    meta = pd.read_parquet(C.CAND_META)
    sem_raw = cosine_to_jd(np.load(C.CAND_VECS), np.load(C.JD_VEC))
    ats_df = meta.assign(s=sem_raw).sort_values(["s", "candidate_id"], ascending=[False, True])
    ats_order = ats_df["candidate_id"].tolist()
    ats_rank = {c: i + 1 for i, c in enumerate(ats_order)}
    sem = dict(zip(meta.candidate_id, pool_normalize(sem_raw).tolist()))

    ours = [row["candidate_id"] for row in csv.DictReader(open(a.submission))]
    K = len(ours)
    cards = []
    for i, cid in enumerate(ours, 1):
        c = Candidate(raws[cid]); s = score_candidate(c, sem.get(cid, 0.0))
        s["rscore"] = round(s["score"], C.SCORE_DECIMALS)
        cards.append(presentation.card(c, s, i, ats_rank.get(cid)))

    eff = presentation.market_efficiency(ours[:K], ats_order[:K])
    tmis = [c["tmi"] for c in cards if c["tmi"] is not None]
    # Hero = biggest mispricing among our TOP-20 (a top pick AND badly underpriced — strongest story).
    hero = max(cards[:20], key=lambda c: (c["tmi"] if c["tmi"] is not None else -1))
    gems = [c for c in cards if c["quadrant"] == "Hidden Gem"]

    def titles(ids): return [Candidate(raws[i]).title for i in ids]
    ats_top10, our_top10 = titles(ats_order[:10]), titles(ours[:10])
    stf_ats = sum(i in stuffers for i in ats_order[:K])
    stf_ours = sum(i in stuffers for i in ours[:K])

    print("=" * 60)
    print("  TALENT MARKET INTELLIGENCE")
    print("=" * 60)
    print(f"  Market Efficiency:        {eff:.0%}   ({1-eff:.0%} of top talent mispriced)")
    print(f"  Hidden Gems Found:        {len(gems)}")
    print(f"  Average Mispricing (TMI): {np.mean(tmis):+.0f}")
    print(f"  Highest Mispricing (TMI): {max(tmis):+d}")
    print(f"\n  Biggest ATS failure: {hero['title']}")
    print(f"    ATS rank {hero['ats_rank']}  ->  our rank {hero['our_rank']}   TMI {hero['tmi']:+d}")
    for d in hero["trust_drivers"]:
        print(f"    ✓ {d}")
    print(f"\n  Keyword-stuffers in top-{K}:  ATS {stf_ats}  vs  ours {stf_ours}")

    payload = {
        "market_efficiency_pct": round(100 * eff), "mispriced_pct": round(100 * (1 - eff)),
        "hidden_gems": len(gems), "avg_tmi": round(float(np.mean(tmis))),
        "highest_tmi": int(max(tmis)),
        "hero": hero, "cards": cards,
        "ats_top10": ats_top10, "our_top10": our_top10,
        "stuffers_in_ats_top": stf_ats, "stuffers_in_our_top": stf_ours,
    }
    if a.json:
        Path(a.json).write_text(json.dumps(payload, indent=2))
        print(f"\nwrote frontend payload -> {a.json}")


if __name__ == "__main__":
    main()
