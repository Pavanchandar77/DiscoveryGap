# Talent Conviction Engine — Pitch

> **We don't just rank candidates. We measure talent mispricing — and surface the people the
> market is systematically undervaluing.**

Most teams built a *better ATS*. We built **talent market intelligence**: a system that
quantifies the information asymmetry between what a résumé *says* (keywords, titles) and what it
*means* (evidence, trajectory, authenticity, availability), and prices it.

---

## Open with a failure (the killer demo)

**Slide 1 — Traditional ATS rank #552.**
An "ML Engineer." Only **1** of the JD's keywords in their skills list. Any keyword/similarity
ranker buries them near the bottom.

**Slide 2 — Our rank #19. Conviction 87%. Talent Mispricing Index +533.**
*Undervalued by 533 ranking positions.*

**Slide 3 — Why the ATS failed.** Only 1 buzzword, **but**:
- ✓ Built production recommendation systems (career text, not keywords)
- ✓ Career trajectory heading straight at search/ranking roles
- ✓ Product-company ML experience at scale
- ✓ Assessment-corroborated skills (81/100)

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

On our validation sample, **85 of the top 100 are Hidden Gems** the ATS ranked past #100.

---

## Why trust it (the part that survives a grilling)

- **Trap-resistant by design.** The dataset is engineered with honeypots and keyword-stuffers
  that auto-disqualify naive rankers. Ours: **0 honeypots, 0 stuffers** in the danger zones; a
  naive embedding baseline pulls in 13 stuffers + 2 honeypots.
- **We validated against independent human judgment** (not just our own labels): ranking order
  tracks it, **zero strong fits missed**, controls rate ~0.
- **Reproducible & deterministic.** CPU-only, network-free ranking, offline embeddings,
  one-command Docker repro. Knows when it might be wrong (Conviction) and says so.

---

## Hero statement

> We don't just rank candidates. We identify talent that the market is systematically
> undervaluing — and we can prove, candidate by candidate, exactly why traditional hiring
> missed them.

*(Numbers above are from the validation sample; regenerate on the full 100K before the final
deck: `python scripts/conviction_demo.py` and `python scripts/discovery_gap.py`.)*
