# Talent Conviction Engine — INDIA.RUNS Track 1

> **We don't just rank candidates. We identify talent that the market is systematically
> undervaluing.** A keyword/similarity ATS sees titles and buzzwords; this engine measures the
> **information asymmetry** between what a résumé *says* and what it *means* — and prices it.

An evidence-aware, **trap-resistant** engine for the Intelligent Candidate Discovery & Ranking
Challenge. It ranks the top 100 from a 100K pool for one fixed Senior AI Engineer JD, with
per-row reasoning. Every candidate gets numbers no ATS shows:

**Core metrics**
- **Fit** — how relevant they are (the gated four-bucket score)
- **Conviction** — how *certain* we are (evidence quality, corroboration, consistency)
- **Talent Mispricing Index (TMI)** — positions the ATS undervalues them by (`ats_rank − our_rank`)

**Supporting signals**
- **Evidence Density** — how much of the résumé is actually supported (verified ÷ claimed skills)
- **Career Trajectory** · **Transferability** · **Availability** · **Authenticity**

…plus two-sided **Trust Drivers (✓) / Concerns (⚠)**. See it per-candidate:
`python scripts/conviction_demo.py --submission submission.csv` (and the Streamlit sandbox).

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
by `precompute.py`. The submission uses the **`hashing`** backend (the default):

- **`hashing`** (submission default) — a deterministic, numpy-only feature-hashing encoder.
  No model, no network, **byte-reproducible anywhere**, so the judges' precompute regenerates
  our exact artifacts and submission offline (full pool: ~3 min). The top-20 it produces is
  wall-to-wall on-target (AI/ML/NLP/Recsys/Search Engineers) — the structured signals carry it.
- **`bge`** (optional upgrade) — `BAAI/bge-small-en-v1.5`, loaded **offline** from a vendored
  `models/bge-small-en-v1.5/` (`hf download BAAI/bge-small-en-v1.5 --local-dir models/bge-small-en-v1.5`),
  JD encoded with the retrieval query prefix, cosines pool-normalized. Higher semantic fidelity;
  set `REDROB_EMBED_BACKEND=bge`.

```bash
pip install -r requirements.txt

# 1) OFFLINE precompute (deterministic, no network; ~3 min on the full 100K — NOT the scored step).
#    Writes artifacts/ (cand_vecs.npy, jd_vec.npy, cand_meta.parquet).
python scripts/precompute.py \
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

## Status — run end-to-end on the full 100K
- **Official validator: passes clean.** `rank.py` ranks the full 100,000-candidate pool in
  **36.5s** (budget 300s), CPU-only, network-guarded.
- **0 honeypots / 0 stuffers** in the danger zones (`honeypot_rate@100 = 0`, `stuffer_rate@10 = 0`).
- **Top-20 is wall-to-wall on-target** — Lead/Staff/Senior AI·ML·NLP Engineers, Recommendation
  Systems Engineers, Search Engineer, Applied ML Engineers, all in the 6–8yr band.
- **Talent Market Intelligence:** Market Efficiency 43% (57% of top talent mispriced), 56 Hidden
  Gems, avg TMI +1,034, highest +23,366; biggest ATS failure: AI Engineer ATS #1788 → our #4.
- Fully reproducible: deterministic hashing backend → judges regenerate the exact submission
  offline. Self-labels are a proxy (tune by JD logic, not metric-chasing).
