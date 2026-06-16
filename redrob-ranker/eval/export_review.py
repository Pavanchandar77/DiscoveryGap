#!/usr/bin/env python3
"""Export a stratified sample of candidates for INDEPENDENT human review.

The self-labels (eval/build_labels.py) share logic with the ranker, so scoring against
them is circular. This produces a blind, human-readable review sheet so a person can rate
fit (tier 0-4) using only the JD and the candidate's real fields — an independent check.
Pair with eval/review_agreement.py after the human fills `human_tier`.

Strata: our top picks, mid, cutoff edge, random non-selected, and honeypot/stuffer controls.

Usage: python eval/export_review.py --candidates ./data/candidates.jsonl --submission submission.csv
"""
from __future__ import annotations
import argparse, csv, json, random, sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from redrob_ranker.schema import Candidate  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def _profile_blurb(c: Candidate) -> dict:
    descs = [(h.get("description") or "").strip() for h in c.history]
    descs = [d for d in descs if d][:2]
    assess = c.signals.get("skill_assessment_scores", {}) or {}
    return {
        "title": c.title, "years_experience": c.years_experience,
        "location": c.location, "industry": c.industry,
        "summary": (c.summary or "")[:500],
        "career_1": descs[0][:400] if descs else "",
        "career_2": descs[1][:400] if len(descs) > 1 else "",
        "skills": ", ".join((s.get("name") or "") for s in c.skills)[:300],
        "recruiter_response_rate": c.signals.get("recruiter_response_rate"),
        "last_active_date": c.signals.get("last_active_date"),
        "open_to_work": c.signals.get("open_to_work_flag"),
        "notice_period_days": c.signals.get("notice_period_days"),
        "assessment_scores": "; ".join(f"{k}:{v}" for k, v in list(assess.items())[:6]),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", required=True)
    ap.add_argument("--submission", required=True)
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    rng = random.Random(a.seed)

    cands = {c.id: c for c in (Candidate(json.loads(l)) for l in open(a.candidates) if l.strip())}
    ranked = [r["candidate_id"] for r in csv.DictReader(open(a.submission))]
    rank_of = {cid: i + 1 for i, cid in enumerate(ranked)}
    labels = pd.read_parquet(ROOT / "eval" / "self_labels.parquet")
    hp = list(labels.loc[labels.is_honeypot, "candidate_id"])
    stf = list(labels.loc[labels.is_stuffer, "candidate_id"])
    not_ranked = [cid for cid in cands if cid not in rank_of]

    picks = []  # (candidate_id, stratum)
    def take(pool, n, stratum):
        for cid in rng.sample(pool, min(n, len(pool))):
            picks.append((cid, stratum))
    take(ranked[:15], 8, "our_top")
    take(ranked[15:50], 8, "our_mid")
    take(ranked[90:100], 6, "our_cutoff")
    take(not_ranked, 10, "not_selected")
    take(hp, 4, "honeypot_control")
    take(stf, 4, "stuffer_control")

    rng.shuffle(picks)
    review_rows, key_rows = [], []
    for rid, (cid, stratum) in enumerate(picks, 1):
        b = _profile_blurb(cands[cid])
        review_rows.append({"review_id": rid, **b, "human_tier (0-4)": "", "human_notes": ""})
        key_rows.append({"review_id": rid, "candidate_id": cid, "stratum": stratum,
                         "our_rank": rank_of.get(cid, "")})

    rev = ROOT / "eval" / "review_sample.csv"
    key = ROOT / "eval" / "review_key.csv"
    with open(rev, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(review_rows[0].keys())); w.writeheader(); w.writerows(review_rows)
    with open(key, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(key_rows[0].keys())); w.writeheader(); w.writerows(key_rows)
    print(f"wrote {len(review_rows)} blind rows -> {rev}")
    print(f"wrote answer key -> {key}")
    print("Fill `human_tier (0-4)` in review_sample.csv (0=no fit, 4=excellent), then run "
          "eval/review_agreement.py.")


if __name__ == "__main__":
    main()
