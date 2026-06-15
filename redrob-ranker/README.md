# Redrob Intelligent Candidate Ranker — INDIA.RUNS Track 1

An evidence-aware, **trap-resistant** ranking system for the Intelligent Candidate
Discovery & Ranking Challenge. It ranks the top 100 candidates from a 100K pool for one
fixed Senior AI Engineer JD, with per-row reasoning.

The dataset is deliberately trap-engineered (keyword stuffers, ~80 honeypots, behavioral
twins, plain-language hidden gems). A naive embedding ranker walks into the traps and gets
disqualified at the honeypot gate. This system **detects the traps** and reasons about the
gap between what a profile *says* and what it *means*.

> **Read `CLAUDE.md` first.** It is the authoritative build spec with all hard rules.

## Approach in one line
A transparent, **gated** four-bucket ensemble — Capability, Growth, Adaptability,
Authenticity & Availability — where a title veto and a behavioral multiplier prevent
keyword-stuffers and stale candidates from reaching the top, and pure-logic gates remove
honeypots and JD-disqualified profiles. No trained model (there are no labels); the edge is
in the **signals**, not the algorithm.

## Reproduce

```bash
pip install -r requirements.txt

# 1) OFFLINE precompute (slow part — embeddings; may exceed 5 min, allowed)
python scripts/precompute.py --candidates ./data/candidates.jsonl --jd ./data/job_description.txt

# 2) ONLINE ranking step (THE scored step: <=5 min, CPU, no network)
python rank.py --candidates ./data/candidates.jsonl --out ./submission.csv

# 3) Validate (MUST pass before submitting)
python scripts/validate_submission.py submission.csv
```

## Self-evaluation (no live leaderboard — validate locally)

```bash
python eval/build_labels.py --candidates ./data/candidates.jsonl   # self-labeled relevance
python eval/run_eval.py --submission submission.csv                # proxy metrics + trap rates
python scripts/discovery_gap.py --submission submission.csv        # baseline-vs-ours pitch artifact
```

Watch two numbers: `honeypot_rate@100` must be **0.0** (>0.10 disqualifies), and
`stuffer_rate@10` should be low.

## Layout
- `rank.py` — single ranking entrypoint (network-guarded, CPU-only).
- `src/redrob_ranker/` — config, schema, normalize, honeypot, disqualifiers, signals,
  embed, features (4 buckets), score (gated combine), reasoning, baseline, orchestration.
- `scripts/` — precompute, vendored validator, discovery-gap demo, sandbox app.
- `eval/` — self-labels, metrics, runner.
- `tests/` — smoke tests.

## Constraints honored (see `CLAUDE.md` §1)
Exactly 100 rows; header `candidate_id,rank,score,reasoning`; non-increasing score;
candidate_id tie-break; CSV/UTF-8; ranking step ≤5 min CPU no-network (guard in `rank.py`);
embeddings precomputed offline; honeypots floored; reasoning generated from real fields only.

## Status
Skeleton runs end-to-end and passes the official validator on a 120-candidate sample.
Embedding model is stubbed for offline use; bucket weights and thresholds are starting
points to tune against `eval/`. See `CLAUDE.md` §9 for the remaining build/tuning work.
