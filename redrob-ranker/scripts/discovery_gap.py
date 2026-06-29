#!/usr/bin/env python3
"""Discovery-Gap 2.0 — not just rank differences, but WHY keyword-search misses the gems.

Contrasts the naive embedding/keyword baseline (what an ATS does) with our gated ranker, and
for each hidden gem we lift, explains the failure of traditional hiring: the real signals ATS
can't see (product-ML at scale, corroborated assessments, a trajectory toward the role, high
confidence) and the reason it ranked them low (missing buzzwords). Writes eval/discovery_gap.md.

Usage: python scripts/discovery_gap.py --submission submission.csv
"""
from __future__ import annotations
import argparse, csv, json, sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from redrob_ranker import config as C                       # noqa: E402
from redrob_ranker.schema import Candidate                   # noqa: E402
from redrob_ranker.embed import cosine_to_jd                 # noqa: E402
from redrob_ranker.score import score_candidate              # noqa: E402


def _why_missed(cand: Candidate, s: dict) -> list[str]:
    cap = s["info"]["capability"]
    why = []
    if cap.get("prod_scale", 0) >= 0.6:
        why.append(f"product-company ML experience at scale ({cap['prod_scale']:.0%})")
    if cap.get("corroboration", 0) >= 0.6:
        why.append(f"assessment-corroborated skills ({cap['corroboration']:.0%})")
    if s["info"]["growth"].get("trajectory", 0) >= 0.5:
        why.append(f"career trajectory toward the role ({s['info']['growth']['trajectory']:.0%})")
    pl = s["info"]["adaptability"].get("plainlang_hits") or []
    if pl:
        why.append(f"describes building the systems: {', '.join(pl[:2])}")
    if s.get("confidence", 0) >= 0.6:
        why.append(f"high confidence ({s['confidence']:.0%})")
    n_core = len(cap.get("core_hit", []))
    if n_core <= 2:
        why.append(f"BUT only {n_core} JD buzzword(s) in skills[] — why ATS ranked them low")
    return why


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--submission", required=True)
    a = ap.parse_args()

    raws = {r["candidate_id"]: r for r in
            (json.loads(l) for l in open(ROOT / "data" / "candidates.jsonl") if l.strip())}
    labels = pd.read_parquet(ROOT / "eval" / "self_labels.parquet")
    hp = set(labels.loc[labels.is_honeypot, "candidate_id"])
    stf = set(labels.loc[labels.is_stuffer, "candidate_id"])

    # Full ATS-style baseline order: pure JD-cosine over the whole pool.
    meta = pd.read_parquet(C.CAND_META)
    sem = cosine_to_jd(np.load(C.CAND_VECS), np.load(C.JD_VEC))
    base_df = meta.assign(sem=sem).sort_values(["sem", "candidate_id"], ascending=[False, True])
    base_rank = {cid: i + 1 for i, cid in enumerate(base_df["candidate_id"].tolist())}

    ours = [row["candidate_id"] for row in csv.DictReader(open(a.submission))]
    our_rank = {cid: i + 1 for i, cid in enumerate(ours)}

    base100 = base_df["candidate_id"].tolist()[:100]
    base_hp = sum(i in hp for i in base100); base_stf = sum(i in stf for i in base100)
    our_hp = sum(i in hp for i in ours[:100]); our_stf = sum(i in stf for i in ours[:100])

    # Hidden gems: in our top-20 but ATS-ranked far lower; lead with the biggest mispricing.
    gems = [cid for cid in ours[:20] if base_rank.get(cid, 10**9) > 100]
    gems.sort(key=lambda cid: -(base_rank.get(cid, 10**9) - our_rank[cid]))   # highest TMI first
    cards = []
    for cid in gems[:8]:
        s = score_candidate(Candidate(raws[cid]), 0.5)
        why = _why_missed(Candidate(raws[cid]), s)
        tmi = base_rank.get(cid) - our_rank[cid]
        cards.append((cid, our_rank[cid], base_rank.get(cid), tmi, Candidate(raws[cid]).title, why))

    lines = [f"""# Talent Mispricing: what traditional hiring systematically gets wrong

We don't just rank candidates — we measure how badly a keyword/similarity ATS **misprices**
them. The Talent Mispricing Index (TMI) = how many ranking positions the ATS undervalues a
candidate by (`ats_rank − our_rank`).

| metric | naive ATS baseline | our engine |
|---|---|---|
| honeypots in top-100 | {base_hp} | {our_hp} |
| keyword-stuffers in top-100 | {base_stf} | {our_stf} |

The baseline is pure JD-similarity — what most ATS/keyword rankers do. It walks into the
engineered traps and, worse, **buries real talent that doesn't use the buzzwords**. The most
mispriced talent in our top-20, biggest first:
"""]
    for cid, orank, brank, tmi, title, why in cards:
        lines.append(f"### {title} — our rank **{orank}**, ATS rank **{brank}**  ·  **TMI +{tmi}**")
        lines.append(f"_Undervalued by {tmi} ranking positions._\n")
        lines.append("\n".join(f"- {w}" for w in why) + "\n")
    if not cards:
        lines.append("_(No top-20 gem was buried past ATS rank 100 in this run.)_")

    md = "\n".join(lines)
    out = ROOT / "eval" / "discovery_gap.md"
    out.write_text(md, encoding="utf-8")
    safe_md = md[:1500].encode(sys.stdout.encoding or 'utf-8', errors='replace').decode(sys.stdout.encoding or 'utf-8')
    print(safe_md); print("...\nwrote", out)


if __name__ == "__main__":
    main()
