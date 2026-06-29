"""Confidence scoring — how much we TRUST a candidate's score (distinct from the score).

The score says "how good a fit"; confidence says "how sure are we". A high score backed by
assessment-corroborated skills, a complete/verified profile, and a clean, consistent record is
high-confidence. The same score resting on unverified claims and a sparse profile is
low-confidence. A ranker that knows when it might be wrong is rare and pitch-worthy.

Returns (confidence in [0,1], factor breakdown). Confidence does NOT change the ranking — it is
reported alongside it.
"""
from __future__ import annotations
from .schema import Candidate


def _clip01(x: float) -> float:
    return max(0.0, min(1.0, x))


def confidence(cand: Candidate, scored: dict) -> tuple[float, dict]:
    cap = scored["info"]["capability"]
    auth = scored["info"]["authenticity"]

    corroboration = cap.get("corroboration", 0.45)        # assessment-backed claim strength
    bluffs = cap.get("bluffs", 0)

    # Evidence presence: do we even have enough data to judge confidently?
    assess = cand.signals.get("skill_assessment_scores", {}) or {}
    n_desc = sum(1 for h in cand.history if (h.get("description") or "").strip())
    evidence_presence = _clip01(0.4 * min(1.0, len(assess) / 4.0)
                                + 0.3 * min(1.0, n_desc / 2.0)
                                + 0.3 * min(1.0, len(cand.skills) / 6.0))

    completeness = _clip01((cand.signals.get("profile_completeness_score") or 50) / 100.0)
    verified = (int(bool(cand.signals.get("verified_email")))
                + int(bool(cand.signals.get("verified_phone")))
                + int(bool(cand.signals.get("linkedin_connected")))) / 3.0

    # Consistency: clean record (not a honeypot), few disqualifier flags, no bluffing.
    clean = 0.0 if scored["is_honeypot"] else 1.0
    dq_flags = len(auth.get("dq_reasons", []))
    consistency = _clip01(clean * (1.0 - 0.2 * min(dq_flags, 3)) * (1.0 - 0.2 * min(bluffs, 3)))

    conf = (0.28 * corroboration + 0.22 * evidence_presence + 0.18 * consistency
            + 0.18 * completeness + 0.14 * verified)
    return _clip01(conf), {
        "corroboration": round(corroboration, 2), "evidence_presence": round(evidence_presence, 2),
        "consistency": round(consistency, 2), "completeness": round(completeness, 2),
        "verified": round(verified, 2),
    }


def rank_stability_label(score: float, buckets: dict, title_gate: float) -> str:
    """Assess how stable this candidate's ranking is under weight perturbations.
    
    Computes the score under 3 perturbed weight configurations (±15%). If the
    coefficient of variation is small, the rank is stable; otherwise fragile.
    Returns 'Stable', 'Moderate', or 'Fragile'.
    """
    cap = buckets.get("capability", 0.5)
    grw = buckets.get("growth", 0.5)
    adp = buckets.get("adaptability", 0.5)
    
    # 3 perturbation vectors: emphasize each bucket in turn
    perturbations = [
        (0.65, 0.15, 0.20),  # capability-heavy
        (0.45, 0.35, 0.20),  # growth-heavy
        (0.45, 0.15, 0.40),  # adaptability-heavy
    ]
    
    scores = []
    for w_c, w_g, w_a in perturbations:
        base = w_c * cap + w_g * grw + w_a * adp
        scores.append(base * title_gate)
    
    mean_s = sum(scores) / len(scores)
    if mean_s == 0:
        return "Fragile"
    variance = sum((s - mean_s) ** 2 for s in scores) / len(scores)
    cv = (variance ** 0.5) / mean_s  # coefficient of variation
    
    if cv < 0.05:
        return "Stable"
    elif cv < 0.12:
        return "Moderate"
    else:
        return "Fragile"
