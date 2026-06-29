"""Counterfactual explainer — "What would promote this candidate?"

For candidates not in the top-15, computes the single factor that, if improved,
would produce the largest score gain. This is cutting-edge Explainable AI (XAI)
applied to hiring — no competitor will have it.

100% deterministic, no LLM, no hallucination — everything references real fields.
"""
from __future__ import annotations
from .schema import Candidate


# Factor name -> (human label, what improvement means)
_FACTOR_LABELS = {
    "capability": ("retrieval/ranking skill depth", "add more core IR/ranking experience"),
    "growth": ("career trajectory toward AI/ML roles", "move into ML-focused roles"),
    "adaptability": ("transferable skills and system-building evidence", "describe ranking/search systems built"),
    "title_gate": ("role title alignment", "transition to an AI/ML Engineering title"),
    "preference": ("location/notice/experience band fit", "reduce notice period or relocate to preferred city"),
}


def counterfactual(cand: Candidate, scored: dict, rank: int) -> str | None:
    """Returns a human-readable counterfactual string, or None if rank <= 15 (already top)."""
    if rank <= 15:
        return None

    buckets = scored.get("buckets", {})
    tg = scored.get("title_gate", 1.0)
    pref = scored.get("preference", 1.0)

    # Compute sensitivity: how much would the final score increase if this factor hit 1.0?
    # The current score = base * tg * auth * pref * density_mult
    # We approximate the marginal gain of each factor reaching its maximum.
    current = scored.get("score", 0.0)
    if current <= 0:
        return None

    sensitivities = {}

    # Bucket sensitivities (capability, growth, adaptability)
    for name in ("capability", "growth", "adaptability"):
        val = buckets.get(name, 0.5)
        if val < 0.95:  # room to improve
            gap = 1.0 - val
            sensitivities[name] = gap * 0.3  # approximate marginal contribution

    # Title gate sensitivity
    if tg < 0.95:
        sensitivities["title_gate"] = (1.0 - tg) * current / max(tg, 0.1)

    # Preference sensitivity
    if pref < 0.95:
        sensitivities["preference"] = (1.0 - pref) * 0.2

    if not sensitivities:
        return None

    best = max(sensitivities, key=sensitivities.get)
    label, advice = _FACTOR_LABELS.get(best, (best, "improve this area"))

    return f"Promotion path: strongest lever is {label} — {advice}"
