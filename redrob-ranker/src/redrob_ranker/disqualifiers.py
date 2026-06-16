"""JD disqualifiers — encode the JD's explicit "explicitly do NOT want" list.

Returns a penalty multiplier in [0, 1] and human-readable reasons. Hard disqualifiers
push the multiplier near 0 (effectively removing them from the top); soft ones nudge it down.
"""
from __future__ import annotations
from . import config as C
from .schema import Candidate
from .normalize import canon_skills, is_consulting_company, has_product_company


def _skill_names(cand: Candidate) -> list[tuple[str, int]]:
    return [((s.get("name") or "").lower(), int(s.get("duration_months") or 0)) for s in cand.skills]


def assess(cand: Candidate) -> tuple[float, list[str]]:
    mult = 1.0
    reasons: list[str] = []
    skills = set(canon_skills(cand))
    named = _skill_names(cand)

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

    # SOFT: research-only background (approximated via industry) with no production.
    if cand.industry.lower() in {"academia", "research", "university"}:
        if not has_product_company(cand):
            mult *= 0.40
            reasons.append("research-only background, no production deployment evident")

    # SOFT (JD): LangChain-only "AI experience" with no pre-LLM ML production depth.
    has_wrapper = any(any(t in nm for t in C.LLM_WRAPPER_SKILLS) for nm, _ in named)
    if has_wrapper:
        has_depth = any(any(t in nm for t in C.PRELLM_DEPTH_SKILLS) and d >= C.PRELLM_DEPTH_MONTHS
                        for nm, d in named)
        wrapper_durs = [d for nm, d in named if any(t in nm for t in C.LLM_WRAPPER_SKILLS)]
        wrapper_recent = wrapper_durs and max(wrapper_durs) < C.LLM_WRAPPER_RECENT_MONTHS
        if not has_depth and wrapper_recent:
            mult *= C.LANGCHAIN_ONLY_MULT
            reasons.append("LLM-wrapper (LangChain/LLM) AI experience without pre-LLM ML depth")

    # SOFT (JD): 'Architect'/tech-lead with no hands-on production code in 18+ months.
    t = cand.title.lower()
    if any(a in t for a in C.ARCHITECT_TITLES):
        cur = [h for h in cand.history if h.get("is_current")] or cand.history[:1]
        cur_dur = max((int(h.get("duration_months") or 0) for h in cur), default=0)
        cur_desc = " ".join((h.get("description") or "") for h in cur).lower()
        if cur_dur >= C.ARCHITECT_STALE_MONTHS and not any(v in cur_desc for v in C.HANDSON_VERBS):
            mult *= C.ARCHITECT_NOCODE_MULT
            reasons.append("architect/lead with no hands-on coding evident in recent role")

    # NOTE: the JD's "closed-source 5+ yrs with no external validation" is intentionally NOT a
    # penalty here. In this pool ~65% have github_activity_score == -1 and only ~5% have any
    # OSS/talks text, so absence is the norm, not a signal (CLAUDE.md §3) — penalizing it nuked
    # ~32% of the pool including genuine fits. External validation is instead rewarded as a small
    # POSITIVE in features.capability (evidence), which aligns with the data without false negatives.

    return (mult, reasons)
