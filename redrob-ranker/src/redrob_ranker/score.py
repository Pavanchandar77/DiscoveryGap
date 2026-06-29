"""Final scoring: combine the four buckets with a GATED (not averaged) formula.

    base   = w_cap*Capability + w_grw*Growth + w_adp*Adaptability
    score  = base * title_gate * authenticity_mult
    score  = 0  if honeypot or hard disqualifier (authenticity_mult ~ 0)

The title gate is the decisive anti-stuffer mechanism: a stuffed skill list on a
Marketing-Manager title cannot reach the top because title_gate floors the product.
"""
from __future__ import annotations
from . import config as C
from .schema import Candidate
from .normalize import classify_title
from . import features
from .confidence import confidence, rank_stability_label


def title_gate(cand: Candidate, adaptability_info: dict) -> float:
    """Multiplicative veto in [TITLE_FLOOR, 1.0]."""
    klass = classify_title(cand.title)
    if klass == "fit":
        return C.TITLE_FULL
    if klass == "trap":
        return C.TITLE_FLOOR

    # Prioritize elite Data Analysts / Business Analysts / Analytics Engineers
    t = (cand.title or "").lower()
    if "analyst" in t or "analytics" in t:
        skills = {s.get("name", "").lower() for s in cand.skills}
        eval_skills = {"evaluation metrics", "a/b testing", "ndcg", "mrr", "map", "statistics"}
        has_eval = bool(skills & eval_skills)
        assess = cand.signals.get("skill_assessment_scores", {}) or {}
        python_score = assess.get("Python", 0) or assess.get("python", 0) or 0
        sql_score = assess.get("SQL", 0) or assess.get("sql", 0) or 0
        
        # If they possess verified evaluation skills and a strong Python/SQL assessment, raise the gate
        if has_eval and (python_score >= 60 or sql_score >= 60 or len(skills & {"sql", "python"}) >= 2):
            return 0.85

    # ambiguous (Business Analyst / Project Manager): earn the gate via real evidence
    plainlang = len(adaptability_info.get("plainlang_hits", []))
    transfer = adaptability_info.get("transfer", 0.0)
    if plainlang >= 2 or transfer >= 0.4:
        return 0.75
    return 0.40


def preference_multiplier(cand: Candidate) -> tuple[float, list[str]]:
    """Soft multiplier for the JD's stated preferences (experience band, location/
    relocation, notice period). Gentle by design — the JD treats these as flexible, so
    they reorder near-ties without vetoing a strong fit. Returns (mult, reasons)."""
    reasons: list[str] = []

    yoe = cand.years_experience
    if C.EXP_IDEAL_LO <= yoe <= C.EXP_IDEAL_HI:
        band = 1.0
    elif C.EXP_OK_LO <= yoe <= C.EXP_OK_HI:
        band = C.EXP_BAND_OK_MULT
    else:
        d = min(abs(yoe - C.EXP_OK_LO), abs(yoe - C.EXP_OK_HI))
        band = max(C.EXP_BAND_FLOOR, C.EXP_BAND_OK_MULT - C.EXP_BAND_DECAY * d)
        reasons.append(f"{yoe:.1f}y outside the 5-9 band")

    loc = cand.location.lower()
    in_pref = any(p in loc for p in C.PREFERRED_LOCATIONS)
    relocate = bool(cand.signals.get("willing_to_relocate"))
    if in_pref or relocate:
        locf = 1.0
    else:
        locf = C.LOC_OTHER_MULT
        reasons.append("not in a preferred location and not open to relocation")

    nd = cand.signals.get("notice_period_days")
    if nd is None:
        notf = 1.0
    elif nd <= 30:
        notf = 1.0
    elif nd <= 60:
        notf = 0.97
    elif nd <= 90:
        notf = 0.94
    else:
        notf = 0.90

    mult = max(C.PREFERENCE_FLOOR, band * locf * notf)
    return mult, reasons


def score_candidate(cand: Candidate, semantic: float) -> dict:
    cap, cap_info = features.capability(cand, semantic)
    grw, grw_info = features.growth(cand)
    adp, adp_info = features.adaptability(cand)
    auth, auth_info, is_hp = features.authenticity(cand)

    base = (C.W_CAPABILITY * cap + C.W_GROWTH * grw + C.W_ADAPTABILITY * adp)
    tg = title_gate(cand, adp_info)
    pref, pref_reasons = preference_multiplier(cand)

    if is_hp:
        final = 0.0
    else:
        # Evidence density: reward candidates whose skill claims are actually verified
        from . import presentation
        _, _, density = presentation.evidence_density(cand)
        density_mult = 0.85 + 0.15 * density  # range [0.85, 1.0]
        final = base * tg * auth * pref * density_mult

    result = {
        "candidate_id": cand.id,
        "score": final,
        "is_honeypot": is_hp,
        "buckets": {"capability": cap, "growth": grw, "adaptability": adp, "authenticity": auth},
        "title_gate": tg,
        "preference": round(pref, 3),
        "info": {"capability": cap_info, "growth": grw_info,
                 "adaptability": adp_info, "authenticity": auth_info,
                 "preference_reasons": pref_reasons},
    }
    conf, conf_factors = confidence(cand, result)   # how sure are we (separate from the score)
    result["confidence"] = round(conf, 3)
    result["info"]["confidence_factors"] = conf_factors
    result["stability"] = rank_stability_label(final, result["buckets"], tg)
    return result
