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
