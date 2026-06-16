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

The **scored step (`rank.py`) is always CPU-only and network-free** — it loads only the
cached artifacts and is guarded against socket use. Embeddings are produced once, offline,
by `precompute.py`. There are two embedding backends; pick per `REDROB_EMBED_BACKEND`:

- **`bge`** (submission default for quality) — `BAAI/bge-small-en-v1.5`, loaded **offline**
  from a vendored `models/bge-small-en-v1.5/` (download it once with
  `hf download BAAI/bge-small-en-v1.5 --local-dir models/bge-small-en-v1.5`). The JD is
  encoded with BGE's retrieval query prefix; cosines are pool-normalized at rank time.
- **`hashing`** (default if unset) — a deterministic, numpy-only feature-hashing encoder.
  No model, no network, byte-reproducible anywhere. Used by the sandbox and as the offline
  fallback.

```bash
pip install -r requirements.txt

# 1) OFFLINE precompute (may exceed 5 min on the full pool — NOT the scored step).
#    Writes artifacts/ (cand_vecs.npy, jd_vec.npy, cand_meta.parquet).
REDROB_EMBED_BACKEND=bge python scripts/precompute.py \
    --candidates ./data/candidates.jsonl --jd ./data/job_description.txt

# 2) ONLINE ranking step (THE scored step: <=5 min, CPU, no network — guard enforced in rank.py)
python rank.py --candidates ./data/candidates.jsonl --out ./submission.csv

# 3) Validate (MUST pass before submitting)
python scripts/validate_submission.py submission.csv
```

> **Shipping for the judges:** commit the precomputed `artifacts/` (use Git LFS for the
> full-pool `cand_vecs.npy`, ~150 MB) so Stage-3 can run `rank.py` offline without
> re-precomputing. The `hashing` backend is the zero-dependency fallback if the model or
> artifacts are unavailable.

### Reproducibility (first-try `clone` / `build` / `run`)

```bash
# Ship the precomputed artifacts via Git LFS (after the full-pool precompute):
bash scripts/ship_artifacts.sh && git push

# Reproduce the scored step in Docker (tiny image: only numpy/pandas/pyarrow, no torch/GPU/network):
docker build -t redrob-ranker .
docker run --rm -v "$PWD/data:/app/data" -v "$PWD/out:/app/out" redrob-ranker \
    --candidates ./data/candidates.jsonl --out ./out/submission.csv
```

`rank.py` imports no model and no network library (verified by import-isolation), so the image
builds in seconds and runs deterministically. BGE precompute auto-uses GPU if one is present.

## Self-evaluation (no live leaderboard — validate locally)

```bash
python eval/build_labels.py --candidates ./data/candidates.jsonl   # self-labeled relevance
python eval/run_eval.py --submission submission.csv                # proxy metrics + trap rates
python scripts/discovery_gap.py --submission submission.csv        # baseline-vs-ours pitch artifact
```

Watch two numbers: `honeypot_rate@100` must be **0.0** (>0.10 disqualifies), and
`stuffer_rate@10` should be low.

The self-labels share logic with the ranker, so their metrics are **circular**. For an
independent check, export a blind, stratified review sheet, rate fit by hand (tier 0-4),
and measure agreement:

```bash
python eval/export_review.py --candidates ./data/candidates.jsonl --submission submission.csv
# fill `human_tier (0-4)` in eval/review_sample.csv, then:
python eval/review_agreement.py    # mean tier per stratum + Spearman(rank, judgment) + disagreements
```

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
Runs end-to-end on the real pool and passes the official validator. The honeypot gate and
self-labels are calibrated against the real distributions (0 honeypots / 0 stuffers in the
danger zones); embeddings use the deterministic offline backend so the whole pipeline is
network-free and reproducible. Bucket weights remain starting points to tune against `eval/`
(self-labels are a proxy, not the hidden truth — tune by JD logic, not metric-chasing).
