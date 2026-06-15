# CLAUDE.md — Build Spec for the Redrob Intelligent Candidate Ranker

This file is the authoritative brief. Read it fully before writing or changing code.
It encodes hard constraints from the official challenge. Violating any **HARD RULE**
gets the submission auto-rejected or disqualified.

---

## 0. What we are building

A ranking system for the INDIA.RUNS Track 1 "Intelligent Candidate Discovery & Ranking
Challenge" (Redrob AI). It reads a 100,000-candidate pool and one fixed job description,
and emits a CSV of the **top 100** candidates, best-fit first, with per-row reasoning.

The dataset is **deliberately trap-engineered**. A naive embedding-similarity ranker
loses here — it walks into keyword-stuffer traps and honeypots and gets disqualified.
The winning system *detects traps* and reasons about the gap between what a profile
*says* and what it *means*.

This is NOT a model-training problem. **There are no labels.** The ground truth is hidden
and revealed only after submissions close. So we cannot train a learning-to-rank model.
We build a **transparent, gated feature ensemble** whose quality comes from the signals
it extracts, not from a fitted model. Our thesis: **signals > models**.

---

## 1. HARD RULES (violating these = rejection / disqualification)

1. **Output = exactly 100 data rows** + 1 header row. Not 99, not 101.
2. **Header must be exactly:** `candidate_id,rank,score,reasoning`
3. **Ranks 1..100 each appear exactly once.** `candidate_id`s unique. All must exist in the pool.
4. **`score` is non-increasing with rank** (score[rank=1] >= score[rank=2] >= ...). Ties allowed.
5. **Tie-break:** equal scores -> `candidate_id` ascending.
6. **CSV only, UTF-8.** Filename = registered participant/team ID, `.csv` extension.
7. **The ranking step (`rank.py`) must run in <= 5 min wall-clock, <= 16 GB RAM, CPU-only, NO network.**
   - No hosted LLM API calls (OpenAI/Anthropic/Cohere/Gemini) *during ranking*.
   - No GPU during ranking.
   - <= 5 GB intermediate disk.
8. **Embeddings/models are PRECOMPUTED offline** (allowed to exceed 5 min) and loaded as
   cached artifacts by `rank.py`. The ranking step does arithmetic + sort over cached features.
9. **Honeypot rate in top-100 must be <= 10%** or the submission is disqualified at Stage 3.
   We target **0 honeypots in top-100**.
10. **Reasoning must not hallucinate.** Every claim in a reasoning string must correspond to a
    real field in that candidate's profile. Generate reasoning *from extracted features only*.
11. **Always run `python scripts/validate_submission.py <file>.csv` before declaring done.**
    The official validator is vendored at `scripts/validate_submission.py`. It must pass clean.

---

## 2. The job we are ranking for (encode these as rules)

Role: **Senior AI Engineer — Founding Team** at Redrob (Series A, AI-native talent platform).
The JD is unusually explicit. Treat the following as computable scoring logic:

### Positive signals (raise score)
- Production embeddings/retrieval/ranking experience (sentence-transformers, BGE, E5, vector DBs:
  Pinecone/Weaviate/Qdrant/Milvus/FAISS/OpenSearch/Elasticsearch).
- Strong Python; evaluation-framework experience (NDCG/MRR/MAP, A/B testing).
- Shipped an end-to-end ranking/search/recommendation system **at a product company, at scale**.
- **Plain-language transfer:** a profile that *describes* building such systems even without the
  buzzwords is a FIT. Detect this from `career_history[].description` and `profile.summary`, not
  just the `skills[]` list.
- "Product over research" tilt; 6-8 yrs total, ~4-5 in applied ML at product companies.
- Location Pune/Noida/Hyderabad/Mumbai/Delhi-NCR, or willing_to_relocate. Sub-30-day notice.
- Active on platform / reachable (behavioral signals — see §3).

### The decisive trap: title-vs-skills contradiction
- A candidate whose `skills[]` is stuffed with AI keywords **but whose title/career is
  Marketing Manager / Accountant / Sales / Civil Engineer / etc.** is **NOT a fit**, no matter how
  perfect the skill list looks. The sample_submission.csv deliberately ranks these people #1-#10
  to show the trap. **A weighted average fails here.** The title/career-context signal must be able
  to *veto / heavily gate* a high skill-match score. Use a multiplicative gate, not a sum.

### Hard disqualifiers (from the JD — encode literally as strong negative gates)
- **Consulting-only career:** entire history at TCS/Infosys/Wipro/Accenture/Cognizant/Capgemini
  with no product-company experience. (If they have prior product-company experience, OK.)
- **Pure research, no production:** academic/research-only roles, never deployed.
- **CV/speech/robotics-primary without NLP/IR exposure.** (Watch: GANs, Image Classification, TTS,
  Speech Recognition heavy, no retrieval/ranking/NLP.)
- **Sub-12-month LangChain-only "AI experience"** with no pre-LLM ML production depth.
- **Title-chaser:** company-hops every ~1.5 yrs optimizing titles (compute avg tenure from
  career_history durations). Soft negative.
- **"Architect"/tech-lead with no production code in 18+ months.** Soft negative.

### Behavioral availability (down-weight, do not exclude)
- A perfect-on-paper candidate who is stale (no login ~6 months) and has ~5% recruiter response
  rate is, for hiring, **not actually available**. Apply a behavioral *multiplier* (<1.0) to such
  candidates. Use `last_active_date`, `recruiter_response_rate`, `open_to_work_flag`,
  `interview_completion_rate`, `saved_by_recruiters_30d`, etc. (see §3).

---

## 3. Behavioral signals (`redrob_signals`, 23 fields)

These are richer than most challenges give. Use them as a **multiplier/modifier** on top of the
capability score, NOT as a primary ranker. Key ones:
- `recruiter_response_rate` (0..1), `last_active_date` (recency), `open_to_work_flag`
- `interview_completion_rate`, `offer_acceptance_rate` (-1 = no history)
- `saved_by_recruiters_30d`, `search_appearance_30d`, `profile_views_received_30d`
- `skill_assessment_scores` (dict skill->0..100) — **corroborates claimed skills** (evidence!)
- `github_activity_score` (-1 if none; 65% of pool is -1, so absence is NOT a strong negative)
- `notice_period_days`, `willing_to_relocate`, `preferred_work_mode`, `profile_completeness_score`
- verified_email / verified_phone / linkedin_connected (weak trust signals)

`skill_assessment_scores` is the strongest *evidence* signal: a claimed "expert" skill with a low
assessment score is a weak claim; a high score corroborates it.

---

## 4. Honeypots (~80 candidates, hidden tier 0)

Subtly *impossible* profiles. Detect with **pure logic / internal-consistency checks** — no ML:
- Tenure exceeding company plausibility (e.g., 8 yrs at a company; sum of durations > years_of_experience by a lot).
- `duration_months` in career_history summing to more than `years_of_experience * 12` (+ slack).
- "expert" proficiency on many skills with `duration_months == 0` or near-0 used.
- Skill `duration_months` exceeding the candidate's total career length.
- Education end_year after a job that requires that degree started; date ordering violations.
- Career start before a plausible working age given education.
These get a **hard kill** (score floored, excluded from top-100). Target: 0 in top-100.
Honeypot detection output also seeds our self-eval set.

---

## 5. Scoring model (transparent, gated — no trained model)

Four buckets, each 0..1, computed per candidate:

- **Capability** = skill match (with alias normalization) + semantic fit (JD vs summary/descriptions)
  + evidence (assessment scores, endorsements, proficiency×duration). Core, works on text+structured.
- **Growth** = career momentum (title-level progression over time) + skill momentum (recent skill
  acquisition, breadth growth).
- **Adaptability** = transferability (adjacent-skill credit via curated map, e.g. GCP~AWS, recsys~ranking)
  + plain-language-transfer detector (description mentions building search/ranking/recsys without buzzwords).
- **Authenticity & Availability** = honeypot-consistency (1.0 clean, 0 = honeypot) × JD-disqualifier
  penalties × behavioral availability multiplier. **This is the bucket that wins this dataset.**

Combination (gated, not a flat average):

```
base = w_cap*Capability + w_grw*Growth + w_adp*Adaptability        # weighted sum of fit
title_gate     = f(title vs JD role)        in [title_floor .. 1]  # multiplicative VETO
score = base * title_gate * authenticity_multiplier
score = 0 (hard floor) if honeypot or hard-disqualifier
```

Default weights (TUNE on self-eval, not on the hidden truth): w_cap=0.55, w_grw=0.20, w_adp=0.25.
`title_floor` ~0.15 so a Marketing-Manager-with-AI-skills can't reach the top.
All weights live in `src/redrob_ranker/config.py` — one place, documented.

---

## 6. Reasoning column (Stage-4 scored — engineer to the rubric)

Generated **from extracted features**, deterministic, no LLM, no hallucination. Stage-4 checks:
specific profile facts, JD-requirement connection, honest concern acknowledgment, no hallucinated
skills, variation across rows, tone matches rank. Build a template generator that:
- pulls real values (years, current_title, 2-3 actual matched skills, a behavioral value),
- names the candidate's actual concern (e.g., "120-day notice", "stale 5% response rate", "CV-heavy"),
- varies sentence structure by score band, so 10 sampled rows read differently.

---

## 7. Pipeline & files (what to build)

Offline (precompute, may exceed 5 min):
- `scripts/precompute.py` — parse + normalize all 100K, encode embeddings (small local model:
  BAAI/bge-small-en-v1.5 or intfloat/e5-small-v2), cache to `artifacts/`:
  `cand_vecs.npy`, `cand_meta.parquet`, `jd_vec.npy`, `skill_alias.json`.

Online (the scored ranking step, MUST meet §1.7):
- `rank.py` (repo root) — single entrypoint. Loads artifacts, computes 4 buckets, gated combine,
  hard gates, sorts, takes top 100, generates reasoning, writes CSV. CPU-only, no network.
  CLI: `python rank.py --candidates ./candidates.jsonl --out ./submission.csv`

Library (`src/redrob_ranker/`):
- `config.py`        — all weights, thresholds, paths, the JD constants, alias/transfer maps.
- `schema.py`        — dataclasses / typed access to a candidate record.
- `normalize.py`     — skill aliasing, title leveling, date parsing, tenure math.
- `embed.py`         — embedding load + encode (offline use) and vector cosine (online, numpy).
- `honeypot.py`      — pure-logic consistency checks -> is_honeypot(cand) + reason.
- `disqualifiers.py` — JD hard/soft negatives -> penalty + reason.
- `signals.py`       — behavioral multiplier from redrob_signals.
- `features.py`      — the four bucket scorers (capability/growth/adaptability/authenticity).
- `score.py`         — gated combination + title gate + final score.
- `reasoning.py`     — feature-templated reasoning string generator.
- `baseline.py`      — naive embedding-only ranker (the contrast object for the Discovery-Gap demo).
- `rank_pipeline.py` — orchestration used by rank.py.

Eval (how we validate with no leaderboard):
- `eval/build_labels.py` — assemble a self-labeled set: all honeypots (tier 0), clear stuffers
  (tier 0/1), clear strong fits (tier 3+), via the rules in §2/§4; lets us hand-correct a sample.
- `eval/metrics.py`      — NDCG@10/@50, MAP, P@10, P@5, honeypot-rate@100, stuffer-rate@10.
- `eval/run_eval.py`     — score our ranking against the self-labeled set + report proxy metrics.

Submission/demo:
- `scripts/validate_submission.py` — vendored official validator (do not edit).
- `scripts/make_sandbox_app.py`    — tiny Streamlit/Gradio app that ranks a <=100 sample
  (required "sandbox link"). CPU, <=5 min on sample.
- `scripts/discovery_gap.py`       — produce the baseline-vs-ours comparison artifact for the pitch.
- `submission_metadata.yaml`       — filled from template (team, repo, sandbox, AI-tools declaration).

---

## 8. Compute & reproducibility discipline (Stage 3 reproduces this in Docker)

- `rank.py` loads only local artifacts; assert no network. Add a guard that monkeypatches sockets
  off during ranking, or document it. Keep a `requirements.txt` pinned.
- The single reproduce command in README must work unmodified:
  `python rank.py --candidates ./candidates.jsonl --out ./submission.csv`
- Pre-computation documented: `python scripts/precompute.py` then `rank.py`.
- Keep git history real and incremental (Stage 4 checks for a single LLM dump vs genuine iteration).

---

## 9. Build order (do in this sequence)

1. `config.py`, `schema.py`, `normalize.py` — foundation + the alias/title/transfer maps.
2. `honeypot.py` + `eval/build_labels.py` — find the traps first; this de-risks the §1.9 gate and
   seeds the eval set. Run it over the real pool and eyeball the catches.
3. `signals.py`, `disqualifiers.py` — the negative/multiplier logic.
4. `embed.py` + `scripts/precompute.py` — produce cached artifacts.
5. `features.py`, `score.py` — the four buckets + gated combine.
6. `reasoning.py` — the Stage-4 generator.
7. `rank.py` + `rank_pipeline.py` — wire end-to-end, write CSV.
8. `scripts/validate_submission.py` run -> must pass. Time it (<5 min on the ranking step).
9. `eval/*` — tune weights against self-eval; watch honeypot-rate@100 -> 0 and stuffer-rate@10 down.
10. `baseline.py` + `scripts/discovery_gap.py` — the pitch artifact.
11. `scripts/make_sandbox_app.py` + `submission_metadata.yaml` + README.

## 10. Definition of done
- `validate_submission.py` passes on `submission.csv`.
- `rank.py` ranking step < 5 min, CPU, no network, <16GB.
- 0 honeypots in top-100 on our honeypot detector; stuffer-rate@10 low.
- Reasoning varies, cites real fields, names concerns, no hallucinations.
- Sandbox app runs on a 100-candidate sample and emits a valid CSV.
- README has the one reproduce command; metadata yaml filled; git history shows real iteration.
