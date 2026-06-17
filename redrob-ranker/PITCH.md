# Talent Conviction Engine — Pitch

> **We don't just rank candidates. We measure talent mispricing — and surface the people the
> market is systematically undervaluing.**

Most teams built a *better ATS*. We built **talent market intelligence**: a system that
quantifies the information asymmetry between what a résumé *says* (keywords, titles) and what it
*means* (evidence, trajectory, authenticity, availability), and prices it.

---

## Open with the question (15 seconds)

> *Financial markets can systematically misprice assets. We asked: can hiring systems
> systematically misprice **people**?*

Then the dashboard — the whole thesis in one screen:

```
              TALENT MARKET INTELLIGENCE   (full 100,000-candidate pool)
   ATS Market Efficiency      43%   (57% of top talent mispriced)
   Hidden Gems Found          56
   Average Mispricing (TMI)   +1,034
   Highest Mispricing (TMI)   +23,366
```

`python scripts/market_dashboard.py --submission submission.csv --json eval/dashboard.json`
emits this plus a frontend-ready payload (hero, cards, ATS-vs-us, stuffer counts).

---

## Open with a failure (the killer demo)

**Slide 1 — Traditional ATS rank #1788.**
An "AI Engineer." A similarity ranker buries them ~1,800 deep, well out of anyone's review.

**Slide 2 — Our rank #4. Talent Mispricing Index +1,784.**
*Undervalued by 1,784 ranking positions.*

**Slide 3 — Why the ATS failed.** Their text doesn't keyword-match the JD, **but**:
- ✓ Built production recommendation systems + feature pipelines (career text, not keywords)
- ✓ Career trajectory heading straight at search/ranking roles
- ✓ Product-company ML experience at scale
- ✓ Assessment-corroborated skills

The panel now *feels* the problem: keyword search can't see real talent.

---

## The three numbers no ATS shows

| Metric | Question it answers |
|---|---|
| **Fit** | How relevant are they? (gated four-bucket score) |
| **Conviction** | How *certain* are we? (evidence quality, corroboration, consistency) |
| **Talent Mispricing Index** | How much is the ATS underpricing them? (`ats_rank − our_rank`) |

Supporting signals: **Evidence Density** (verified ÷ claimed skills — "how much of the résumé is
real"), Career Trajectory, Transferability, Availability, Authenticity. Every pick comes with
two-sided **Trust Drivers (✓) and Concerns (⚠)** — we show uncertainty, not just confidence.

---

## The bet map (hero visual)

Fit × Conviction, bubble size = mispricing. Four quadrants:

- **Hidden Gems** (high conviction, ATS buried them) ← our differentiator
- **Obvious Fits** (everyone finds them)
- **Promising but Uncertain** (route to manual review)
- **Ignore**

On the full 100K pool, **56 of the top 100 are Hidden Gems** the ATS buried — and the most underpriced is mispriced by +23,366 positions.

---

## Why trust it (the part that survives a grilling)

- **Trap-resistant by design.** The dataset is engineered with honeypots and keyword-stuffers
  that auto-disqualify naive rankers. Ours: **0 honeypots, 0 stuffers** in the danger zones; a
  naive embedding baseline pulls in 9 stuffers + 3 honeypots (full pool).
- **We validated against independent human judgment** (not just our own labels): ranking order
  tracks it, **zero strong fits missed**, controls rate ~0.
- **Reproducible & deterministic.** CPU-only, network-free ranking, offline embeddings,
  one-command Docker repro. Knows when it might be wrong (Conviction) and says so.

---

## Demo flow — Problem → Failure → Insight → Solution → Evidence

A judge should grasp the whole idea in under 20 seconds, without reading a technical doc.

| Time | Screen | Shows |
|---|---|---|
| 0:15 | **Hero dashboard** | Market Efficiency 43%, 56 Hidden Gems, Avg TMI +1,034 → "these guys find overlooked talent" |
| 0:30 | **The ATS failure** | ATS #1788 → Our #4 → **TMI +1,784**, then "Why ATS missed them" |
| 1:00 | **Conviction card** | Fit / Conviction / TMI / Evidence Density + Trust Drivers ✓ and Concerns ⚠ |
| 0:30 | **The bet map** | every candidate in the Fit×Conviction quadrant; Hidden Gems pop |
| 0:30 | **ATS vs us** | across the top-100 the ATS pulls in **9 keyword-stuffers + 3 honeypots**; ours has **0** — and buries 56 hidden gems we surface |

**Do NOT put on screen** (implementation details — only if a judge asks): Qdrant, FAISS, BGE,
embeddings, cosine similarity, sentence-transformers, Docker, XGBoost. Lead with the *mental
model*, not the stack.

## Hero statement

> We don't just rank candidates. We identify talent that the market is systematically
> undervaluing — and we can prove, candidate by candidate, exactly why traditional hiring
> missed them.

*(All numbers above are from the full 100,000-candidate pool. Regenerate any time with
`python scripts/market_dashboard.py --submission submission.csv` and `scripts/discovery_gap.py`.)*
