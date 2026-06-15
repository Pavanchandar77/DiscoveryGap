"""JD disqualifiers — encode the JD's explicit "explicitly do NOT want" list.

Returns a penalty multiplier in [0, 1] and human-readable reasons. Hard disqualifiers
push the multiplier near 0 (effectively removing them from the top); soft ones nudge it down.
"""
from __future__ import annotations
from . import config as C
from .schema import Candidate
from .normalize import canon_skills, is_consulting_company, has_product_company


def assess(cand: Candidate) -> tuple[float, list[str]]:
    mult = 1.0
    reasons: list[str] = []
    skills = set(canon_skills(cand))

    # HARD: consulting-only career (no product company anywhere).
    all_consulting = bool(cand.history) and all(
        is_consulting_company(h.get("company", "")) for h in cand.history
    )
    if all_consulting and not has_product_company(cand):
        mult *= 0.15
        reasons.append("consulting-only career, no product-company experience")

    # HARD: CV/speech/robotics-primary without IR/NLP exposure.
    cv_speech = sum(1 for s in skills if s in set(C.CV_SPEECH_SKILLS))
    ir_nlp = sum(1 for s in skills if s in set(C.IR_NLP_SKILLS))
    if cv_speech >= 3 and ir_nlp == 0:
        mult *= 0.30
        reasons.append("computer-vision/speech-heavy with no NLP/IR exposure")

    # SOFT: title-chaser — very short average tenure across several roles.
    if len(cand.history) >= 3 and cand.avg_tenure_months < 18:
        mult *= 0.80
        reasons.append(f"short average tenure ({cand.avg_tenure_months:.0f}mo) suggests title-chasing")

    # SOFT: very junior relative to the 5-9yr band AND no product company.
    if cand.years_experience < 3 and not has_product_company(cand):
        mult *= 0.85
        reasons.append("well below experience band with no product-company background")

    # NOTE: pure-research and 'architect-no-code-18mo' need richer text parsing; we approximate
    # pure-research via industry == 'Academia'/'Research' if present.
    if cand.industry.lower() in {"academia", "research", "university"}:
        if not has_product_company(cand):
            mult *= 0.40
            reasons.append("research-only background, no production deployment evident")

    return (mult, reasons)
