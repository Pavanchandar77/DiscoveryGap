# Responsible AI — Discovery / Talent Conviction Engine

Discovery ranks candidates and **explains every ranking**. This document states how it
is built to be defensible for hiring use, where automated decision tools face real legal
scrutiny (e.g. NYC Local Law 144, EEOC adverse-impact review, the EU AI Act's "high-risk"
employment category, Illinois AIVI).

## 1. Decision support, with a human in the loop
Discovery does **not** make hiring decisions. It surfaces and ranks candidates and shows the
evidence; a human recruiter decides. There is no auto-reject and no auto-advance. This is the
intended and legally defensible posture for employment tools.

## 2. Transparent by construction — no black box
The engine is a **transparent, gated feature ensemble**, not a trained or opaque model
(see `redrob-ranker/CLAUDE.md` §5). Scores combine four interpretable buckets — Capability,
Growth, Adaptability, Authenticity & Availability — via a documented, multiplicative gate.
Every weight lives in one file (`src/redrob_ranker/config.py`).

## 3. A per-candidate audit trail
For each candidate the UI exposes (and the API returns):
- **Fit**, **Conviction**, **Evidence Density**, verified-vs-claimed skills,
- **Trust drivers** and **Concerns**,
- a plain-language **reasoning** string.

Every figure traces to a field in that candidate's own profile. Reasoning is generated **from
extracted features only — no hallucination** (`CLAUDE.md` §6, §1.10).

## 4. No protected attributes
Scoring uses skills, evidence, role-fit and platform-behavior signals. It does **not** use name,
gender, age, ethnicity, photographs, or any protected characteristic as an input.

## 5. Built to *reduce* bias, not add it
Traditional ATS keyword filters systematically bury qualified, non-traditional candidates — the
real adverse-impact risk. Discovery's "hidden gems" are exactly those overlooked-but-qualified
people. Surfacing them widens the funnel and counteracts keyword-driven bias. It also actively
detects and discounts keyword-stuffing and internally inconsistent ("honeypot") profiles.

## 6. Determinism and reproducibility
The ranking step is deterministic, CPU-only, and runs with no network and no hosted-LLM calls
(`CLAUDE.md` §1.7). The same input yields the same ranking, which makes audits repeatable.

## 7. Recommended controls before production use
- Run a periodic **adverse-impact / four-fifths analysis** on outcomes for your roles.
- Keep the recruiter override and the audit trail with each shortlist.
- Disclose use of an automated tool to candidates where required by local law, and offer a
  human-review path.
- Treat scores as a ranked starting point for human review, not a pass/fail gate.

> The same rigor that finds undervalued talent is what makes Discovery explainable and auditable.
