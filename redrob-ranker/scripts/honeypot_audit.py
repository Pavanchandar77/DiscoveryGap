#!/usr/bin/env python3
"""Audit the honeypot detector over a candidate pool.

Prints the flagged count/rate, a breakdown of which consistency rule fired, and a
sample of catches with the underlying numbers so we can judge whether each is a
genuinely impossible profile or a false positive on a legitimate one.

Usage: python scripts/honeypot_audit.py --candidates ./data/candidates.jsonl [--n 15]
"""
from __future__ import annotations
import argparse, json, sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from redrob_ranker.schema import Candidate          # noqa: E402
from redrob_ranker import honeypot                  # noqa: E402


def rule_of(reason: str) -> str:
    if "role durations sum to" in reason: return "1:durations_sum>yoe"
    if "used" in reason and "> career length" in reason: return "2:skill_dur>career"
    if "'expert' skills with ~0 months" in reason: return "3:expert_zero_dur"
    if "role at" in reason and "> total experience" in reason: return "4:single_role>yoe"
    if "precedes earliest education" in reason: return "5:job_before_edu"
    if "education end_year" in reason: return "6:edu_end<start"
    return "other"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", required=True)
    ap.add_argument("--n", type=int, default=15)
    a = ap.parse_args()

    rows = [json.loads(l) for l in open(a.candidates) if l.strip()]
    flagged, rule_counts, examples = [], Counter(), []
    for raw in rows:
        c = Candidate(raw)
        is_hp, reasons = honeypot.detect(c)
        if is_hp:
            flagged.append(c.id)
            for r in reasons:
                rule_counts[rule_of(r)] += 1
            if len(examples) < a.n:
                examples.append((c, reasons))

    n = len(rows)
    print(f"pool={n}  flagged={len(flagged)}  rate={len(flagged)/n:.4f}")
    print("rule firings (a profile can trip several):")
    for rule, ct in sorted(rule_counts.items()):
        print(f"  {rule:24s} {ct}")
    print(f"\n--- {len(examples)} sample catches ---")
    for c, reasons in examples:
        durs = [int(h.get('duration_months') or 0) for h in c.history]
        print(f"\n{c.id}  title={c.title!r}  yoe={c.years_experience}  "
              f"sum_hist_mo={c.total_history_months}  role_durs={durs}")
        for r in reasons:
            print(f"    - {r}")


if __name__ == "__main__":
    main()
