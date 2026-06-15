#!/usr/bin/env python3
"""OFFLINE precompute (may exceed 5 min — NOT the scored ranking step).

Produces the cached artifacts that rank.py consumes:
  artifacts/cand_meta.parquet  — per-candidate normalized fields (+ honeypot flag for audit)
  artifacts/cand_vecs.npy      — (N, d) L2-normalized embeddings, row order == meta
  artifacts/jd_vec.npy         — (d,) JD embedding
  artifacts/skill_alias.json   — observed raw->canonical skill map (audit aid)

Usage:
  python scripts/precompute.py --candidates ./data/candidates.jsonl --jd ./data/job_description.txt
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from redrob_ranker import config as C           # noqa: E402
from redrob_ranker.schema import Candidate       # noqa: E402
from redrob_ranker.normalize import canon_skill  # noqa: E402
from redrob_ranker import honeypot               # noqa: E402
from redrob_ranker.embed import encode_texts, encode_one  # noqa: E402


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    opener = open
    if str(path).endswith(".gz"):
        import gzip
        opener = lambda p: gzip.open(p, "rt")  # noqa: E731
    with opener(path) as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", required=True)
    ap.add_argument("--jd", required=True, help="path to JD text file")
    args = ap.parse_args()

    C.ARTIFACTS.mkdir(parents=True, exist_ok=True)
    raws = load_jsonl(Path(args.candidates))
    print(f"loaded {len(raws)} candidates")

    texts, meta_rows, alias_obs = [], [], {}
    for raw in raws:
        cand = Candidate(raw)
        texts.append(cand.all_text)
        for sk in cand.skills:
            r = (sk.get("name") or "").strip().lower()
            if r:
                alias_obs[r] = canon_skill(sk.get("name", ""))
        is_hp, hp_reasons = honeypot.detect(cand)
        meta_rows.append({
            "candidate_id": cand.id,
            "title": cand.title,
            "years_experience": cand.years_experience,
            "industry": cand.industry,
            "location": cand.location,
            "n_skills": len(cand.skills),
            "is_honeypot": is_hp,
            "honeypot_reasons": "; ".join(hp_reasons),
        })

    meta = pd.DataFrame(meta_rows)
    meta.to_parquet(C.CAND_META, index=False)
    print(f"honeypots detected: {int(meta['is_honeypot'].sum())}")

    jd_text = Path(args.jd).read_text(encoding="utf-8")
    print("encoding candidate texts (this is the slow part)...")
    vecs = encode_texts(texts)
    np.save(C.CAND_VECS, vecs)
    np.save(C.JD_VEC, encode_one(jd_text))
    C.SKILL_ALIAS.write_text(json.dumps(alias_obs, indent=2))
    print("precompute complete:", C.ARTIFACTS)


if __name__ == "__main__":
    main()
