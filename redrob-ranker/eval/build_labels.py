#!/usr/bin/env python3
"""Build a SELF-LABELED relevance set (no hidden truth available).

We assign coarse relevance tiers using the JD rules so we can compute proxy metrics and
tune weights. This is NOT the organizers' ground truth — it's our defensible stand-in,
and a sample of it should be hand-corrected. Tiers:
  0 = honeypot or hard-disqualified or clear keyword-stuffer (trap title + AI skills)
  1 = weak / adjacent only
  2 = plausible
  3 = strong fit (fit title + core skills or strong plain-language transfer + product co.)
  4 = excellent fit (3 + active/reachable + product-company ranking/search experience)

Outputs eval/self_labels.parquet with candidate_id, tier, is_honeypot, is_stuffer.
Usage: python eval/build_labels.py --candidates ./data/candidates.jsonl
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from redrob_ranker import config as C            # noqa: E402
from redrob_ranker.schema import Candidate        # noqa: E402
from redrob_ranker.normalize import canon_skills, classify_title, has_product_company  # noqa: E402
from redrob_ranker import honeypot, disqualifiers # noqa: E402


def load(path):
    opener = open
    if str(path).endswith(".gz"):
        import gzip; opener = lambda p: gzip.open(p, "rt")  # noqa: E731
    with opener(path) as f:
        return [json.loads(l) for l in f if l.strip()]


def label(cand: Candidate) -> dict:
    is_hp, _ = honeypot.detect(cand)
    skills = set(canon_skills(cand))
    core_hit = len(skills & set(C.JD_CORE_SKILLS))
    klass = classify_title(cand.title)
    dq_mult, _ = disqualifiers.assess(cand)
    text = cand.all_text.lower()
    plain = sum(1 for p in C.PLAINLANG_FIT_PHRASES if p in text)

    is_stuffer = (klass == "trap" and core_hit >= 4)
    if is_hp:
        tier = 0
    elif is_stuffer or dq_mult < 0.2:
        tier = 0
    elif klass == "fit" and core_hit >= 3 and has_product_company(cand):
        tier = 4 if plain >= 2 else 3
    elif klass == "fit" and (core_hit >= 2 or plain >= 2):
        tier = 3
    elif plain >= 2 or core_hit >= 2:
        tier = 2
    elif core_hit >= 1 or plain >= 1:
        tier = 1
    else:
        tier = 0
    return {"candidate_id": cand.id, "tier": tier,
            "is_honeypot": is_hp, "is_stuffer": is_stuffer}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--candidates", required=True)
    a = ap.parse_args()
    rows = [label(Candidate(r)) for r in load(Path(a.candidates))]
    df = pd.DataFrame(rows)
    out = Path(__file__).resolve().parent / "self_labels.parquet"
    df.to_parquet(out, index=False)
    print(df["tier"].value_counts().sort_index())
    print(f"honeypots={int(df.is_honeypot.sum())} stuffers={int(df.is_stuffer.sum())} -> {out}")


if __name__ == "__main__":
    main()
