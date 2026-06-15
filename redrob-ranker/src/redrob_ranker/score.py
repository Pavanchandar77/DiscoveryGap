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


def title_gate(cand: Candidate, adaptability_info: dict) -> float:
    """Multiplicative veto in [TITLE_FLOOR, 1.0]."""
    klass = classify_title(cand.title)
    if klass == "fit":
        return C.TITLE_FULL
    if klass == "trap":
        return C.TITLE_FLOOR
    # ambiguous (Business Analyst / Project Manager): earn the gate via real evidence
    plainlang = len(adaptability_info.get("plainlang_hits", []))
    transfer = adaptability_info.get("transfer", 0.0)
    if plainlang >= 2 or transfer >= 0.4:
        return 0.75
    return 0.40


def score_candidate(cand: Candidate, semantic: float) -> dict:
    cap, cap_info = features.capability(cand, semantic)
    grw, grw_info = features.growth(cand)
    adp, adp_info = features.adaptability(cand)
    auth, auth_info, is_hp = features.authenticity(cand)

    base = (C.W_CAPABILITY * cap + C.W_GROWTH * grw + C.W_ADAPTABILITY * adp)
    tg = title_gate(cand, adp_info)

    if is_hp:
        final = 0.0
    else:
        final = base * tg * auth

    return {
        "candidate_id": cand.id,
        "score": final,
        "is_honeypot": is_hp,
        "buckets": {"capability": cap, "growth": grw, "adaptability": adp, "authenticity": auth},
        "title_gate": tg,
        "info": {"capability": cap_info, "growth": grw_info,
                 "adaptability": adp_info, "authenticity": auth_info},
    }
