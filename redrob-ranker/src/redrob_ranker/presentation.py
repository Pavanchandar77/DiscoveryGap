"""Presentation layer for the Talent Conviction Engine.

Recruiters don't hire scores — they make bets. So we report three numbers per candidate that
a traditional ATS never shows, plus a two-sided human explanation:

  Fit (0-100)        how relevant they are            (the gated score)
  Conviction (0-100) how certain we are               (the confidence model)
  Discovery Gap      how much a keyword/similarity ATS underrates them (ats_rank - our_rank)

  Trust Drivers (✓)  why we trust this candidate
  Concerns (⚠)       where we're unsure

Everything is built from real extracted fields — no hallucination.
"""
from __future__ import annotations
from .schema import Candidate


def _best_assessment(cand: Candidate, names: set[str]) -> tuple[str, float] | None:
    assess = cand.signals.get("skill_assessment_scores", {}) or {}
    best = None
    for k, v in assess.items():
        if k.lower() in names and (best is None or v > best[1]):
            best = (k, float(v))
    return best


def trust_drivers(cand: Candidate, scored: dict) -> list[str]:
    info = scored["info"]; cap = info["capability"]; grw = info["growth"]; adp = info["adaptability"]
    jd_named = {s.lower() for s in (cap.get("core_hit") or []) + (cap.get("nice_hit") or [])}
    drivers: list[str] = []

    ba = _best_assessment(cand, jd_named) or _best_assessment(cand, {k.lower() for k in
         (cand.signals.get("skill_assessment_scores", {}) or {})})
    if ba and ba[1] >= 60:
        drivers.append(f"Assessment {ba[0]} {ba[1]:.0f}/100")
    if cap.get("prod_scale", 0) >= 0.6:
        drivers.append("Product-company ML experience at scale")
    if grw.get("trajectory", 0) >= 0.5:
        drivers.append("Trajectory toward search/recommendation/ranking roles")
    pl = adp.get("plainlang_hits") or []
    if pl:
        drivers.append(f"Describes building: {', '.join(pl[:2])}")
    if 5.0 <= cand.years_experience <= 9.0:
        drivers.append(f"{cand.years_experience:.0f}y experience — in the 5-9 band")
    rr = float(cand.signals.get("recruiter_response_rate") or 0)
    if rr >= 0.4:
        drivers.append(f"Responsive ({rr:.0%} recruiter response)")
    return drivers[:4]


def concerns(cand: Candidate, scored: dict) -> list[str]:
    info = scored["info"]; cap = info["capability"]; auth = info["authenticity"]
    out: list[str] = []
    out += [r for r in (auth.get("dq_reasons") or [])][:2]
    out += [r for r in (auth.get("avail_reasons") or [])][:1]
    nd = cand.signals.get("notice_period_days")
    if nd and nd > 30:
        out.append(f"{nd}-day notice")
    if cap.get("bluffs", 0) > 0:
        out.append(f"{cap['bluffs']} claimed skill(s) not backed by assessment")
    if not cap.get("core_hit") and not (info["adaptability"].get("plainlang_hits")):
        out.append("Limited explicit retrieval/ranking evidence")
    if not (5.0 <= cand.years_experience <= 9.0):
        out.append(f"{cand.years_experience:.0f}y — outside the 5-9 band")
    # de-dup, cap
    seen, uniq = set(), []
    for c in out:
        if c not in seen:
            seen.add(c); uniq.append(c)
    return uniq[:3]


def quadrant(conviction: float, ats_rank: int | None, in_top: bool,
             conv_mid: float = 0.6, ats_cutoff: int = 100) -> str:
    """The bet quadrant. The Hidden-Gem vs Obvious-Fit split is whether a keyword/similarity
    ATS *also* found them (ats_rank within its top-100) — fit scores are compressed by the
    multiplicative gates, so 'did ATS miss them' is the meaningful, truthful axis."""
    hi_conv = conviction >= conv_mid
    ats_missed = ats_rank is None or ats_rank > ats_cutoff
    if hi_conv and ats_missed:
        return "Hidden Gem"          # we're confident; ATS buried them
    if hi_conv and not ats_missed:
        return "Obvious Fit"          # we're confident; ATS found them too
    if in_top:
        return "Promising but Uncertain"
    return "Ignore"


def card(cand: Candidate, scored: dict, our_rank: int, ats_rank: int | None,
         ats_cutoff: int = 100, in_top: bool = True) -> dict:
    fit = scored["rscore"] if "rscore" in scored else scored["score"]
    conviction = scored.get("confidence", 0.0)
    gap = (ats_rank - our_rank) if ats_rank is not None else None
    return {
        "candidate_id": cand.id, "title": cand.title,
        "fit": round(100 * fit), "conviction": round(100 * conviction),
        "discovery_gap": gap, "our_rank": our_rank, "ats_rank": ats_rank,
        "quadrant": quadrant(conviction, ats_rank, in_top=in_top, ats_cutoff=ats_cutoff),
        "trust_drivers": trust_drivers(cand, scored),
        "concerns": concerns(cand, scored),
    }
