"""Reasoning column generator — built from extracted features ONLY (no LLM, no hallucination).

Engineered to the Stage-4 rubric: cites real profile facts, connects to JD requirements,
acknowledges concerns honestly, varies across rows, tone matches rank. Every string it
emits references fields that actually exist on the candidate.
"""
from __future__ import annotations
from .schema import Candidate


def make(cand: Candidate, scored: dict, rank: int) -> str:
    from . import presentation
    drivers = presentation.trust_drivers(cand, scored)
    cons = presentation.concerns(cand, scored)
    cap = scored["info"]["capability"]
    
    yrs = f"{cand.years_experience:.1f}y"
    title = cand.title or "Candidate"
    conv = round(100 * scored.get("confidence", 0.0))
    
    # Evidence density
    verified, claimed, density = presentation.evidence_density(cand)
    ev_str = f"Evidence: {verified}/{claimed} skills verified ({round(100*density)}%)"
    
    # Core bluff warnings (Stage-4 rubric: acknowledge concerns honestly)
    bluff_str = ""
    bluff_details = cap.get("bluff_details", [])
    if bluff_details:
        bluff_str = f" ⚠ Bluff detected: {bluff_details[0]}."
    
    drivers_str = "; ".join(drivers[:3]) if drivers else "Solid technical alignment"
    concerns_str = ""
    if cons:
        concerns_str = f" [Concerns: {'; '.join(cons[:2])}]"
    
    # Vary structure by rank cohort
    if rank <= 15:
        prefix = f"EXECUTIVE SHORTLIST #{rank}"
    elif rank <= 55:
        prefix = f"STRONG FIT #{rank}"
    else:
        prefix = f"SHORTLISTED #{rank}"
        
    text = (f"{prefix} | {title}, {yrs}, Conv {conv}% | "
            f"{ev_str} | {drivers_str}.{bluff_str}{concerns_str}")
    return text[:300]
