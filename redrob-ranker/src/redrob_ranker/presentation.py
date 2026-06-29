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


def market_efficiency(our_top_ids: list[str], ats_top_ids: list[str]) -> float:
    """Of the candidates we identify as strong, what fraction did the ATS also surface?
    Low efficiency = the market is mispricing most of the top talent. Returns [0,1]."""
    if not our_top_ids:
        return 0.0
    return len(set(our_top_ids) & set(ats_top_ids)) / len(our_top_ids)


def evidence_density(cand: Candidate) -> tuple[int, int, float]:
    """How much of the resume is actually supported. A claimed skill counts as 'verified' if it
    has a passing assessment score, real endorsements, or genuine proficiency×duration. Returns
    (verified, claimed, density). Intuitive: 14/18 = 78% supported vs 3/25 = 12% (keyword stuffer)."""
    assess = {str(k).lower(): v for k, v in (cand.signals.get("skill_assessment_scores", {}) or {}).items()}
    claimed = len(cand.skills)
    verified = 0
    for s in cand.skills:
        nm = (s.get("name") or "").lower()
        a = assess.get(nm)
        endorsed = int(s.get("endorsements") or 0) >= 5
        experienced = s.get("proficiency") in ("advanced", "expert") and int(s.get("duration_months") or 0) >= 12
        if (a is not None and a >= 50) or endorsed or experienced:
            verified += 1
    return verified, claimed, (verified / claimed if claimed else 0.0)


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
    from .counterfactual import counterfactual as cf
    fit = scored["rscore"] if "rscore" in scored else scored["score"]
    conviction = scored.get("confidence", 0.0)
    # Talent Mispricing Index: how many ranking positions the ATS undervalues them by.
    tmi = (ats_rank - our_rank) if ats_rank is not None else None
    verified, claimed, density = evidence_density(cand)
    cf_text = cf(cand, scored, our_rank)
    return {
        "candidate_id": cand.id, "title": cand.title,
        "fit": round(100 * fit), "conviction": round(100 * conviction),
        "tmi": tmi, "our_rank": our_rank, "ats_rank": ats_rank,
        "evidence_density": round(100 * density), "verified_skills": verified, "claimed_skills": claimed,
        "quadrant": quadrant(conviction, ats_rank, in_top=in_top, ats_cutoff=ats_cutoff),
        "trust_drivers": trust_drivers(cand, scored),
        "concerns": concerns(cand, scored),
        "counterfactual": cf_text,
        "stability": scored.get("stability", "Stable"),
    }
