"""The four signal buckets. Each returns a 0..1 score plus a small dict of evidence
used later by reasoning.py. No model fitting — transparent, inspectable arithmetic.
"""
from __future__ import annotations
import numpy as np
from . import config as C
from .schema import Candidate
from .normalize import canon_skills, classify_title, career_title_levels
from . import honeypot, disqualifiers, signals


# ---------------------------------------------------------------------------
# Capability
# ---------------------------------------------------------------------------
def capability(cand: Candidate, semantic: float) -> tuple[float, dict]:
    skills = set(canon_skills(cand))
    core = set(C.JD_CORE_SKILLS)
    nice = set(C.JD_NICE_SKILLS)

    core_hit = skills & core
    nice_hit = skills & nice
    skill_score = min(1.0, 0.7 * (len(core_hit) / max(1, len(core))) +
                            0.3 * (len(nice_hit) / max(1, len(nice))) * 2)

    # evidence: assessment scores corroborate claims; proficiency*duration; endorsements
    assess = cand.signals.get("skill_assessment_scores", {}) or {}
    if assess:
        ev_assess = np.mean([v for v in assess.values()]) / 100.0
    else:
        ev_assess = 0.4
    prof_w = {"beginner": 0.25, "intermediate": 0.5, "advanced": 0.8, "expert": 1.0}
    dur_evid = []
    for sk in cand.skills:
        if canon_skills_one(sk) in (core | nice):
            w = prof_w.get(sk.get("proficiency", "intermediate"), 0.5)
            d = min(1.0, int(sk.get("duration_months") or 0) / 36.0)
            dur_evid.append(w * d)
    ev_dur = float(np.mean(dur_evid)) if dur_evid else 0.3
    evidence = 0.6 * ev_assess + 0.4 * ev_dur

    sem = max(0.0, semantic)  # cosine can be slightly negative; floor at 0
    score = (C.W_CAP_SKILL * skill_score +
             C.W_CAP_SEMANTIC * sem +
             C.W_CAP_EVIDENCE * evidence)
    return min(1.0, score), {
        "core_hit": sorted(core_hit), "nice_hit": sorted(nice_hit),
        "semantic": round(sem, 3), "evidence": round(evidence, 3),
    }


def canon_skills_one(sk: dict) -> str:
    from .normalize import canon_skill
    return canon_skill(sk.get("name", ""))


# ---------------------------------------------------------------------------
# Growth
# ---------------------------------------------------------------------------
def growth(cand: Candidate) -> tuple[float, dict]:
    levels = career_title_levels(cand)
    if len(levels) >= 2:
        slope = (levels[-1] - levels[0]) / max(1, len(levels) - 1)
        momentum = min(1.0, max(0.0, 0.5 + slope * 0.25))  # rising titles -> >0.5
    else:
        momentum = 0.5
    # skill breadth as a proxy for skill momentum
    breadth = min(1.0, len(cand.skills) / 15.0)
    score = 0.65 * momentum + 0.35 * breadth
    return min(1.0, score), {"title_slope": round(momentum, 3), "breadth": round(breadth, 3)}


# ---------------------------------------------------------------------------
# Adaptability
# ---------------------------------------------------------------------------
def adaptability(cand: Candidate) -> tuple[float, dict]:
    skills = set(canon_skills(cand))
    # transfer credit: adjacent skills to JD requirements
    credit = 0.0
    needed = set(C.JD_CORE_SKILLS)
    for req in needed:
        if req in skills:
            continue
        adj = set(C.TRANSFER_MAP.get(req, []))
        if adj & skills:
            credit += C.TRANSFER_CREDIT
    transfer = min(1.0, credit / max(1, len(needed)))

    # plain-language transfer: real system-building described without buzzwords
    text = cand.all_text.lower()
    hits = [p for p in C.PLAINLANG_FIT_PHRASES if p in text]
    plainlang = min(1.0, len(hits) / 4.0)

    score = 0.5 * transfer + 0.5 * plainlang
    return min(1.0, score), {"transfer": round(transfer, 3),
                             "plainlang_hits": hits[:4]}


# ---------------------------------------------------------------------------
# Authenticity & Availability (the bucket that wins this dataset)
# ---------------------------------------------------------------------------
def authenticity(cand: Candidate) -> tuple[float, dict, bool]:
    is_hp, hp_reasons = honeypot.detect(cand)
    dq_mult, dq_reasons = disqualifiers.assess(cand)
    avail_mult, avail_reasons = signals.availability(cand)

    if is_hp:
        return 0.0, {"honeypot": True, "honeypot_reasons": hp_reasons}, True

    # authenticity multiplier folds disqualifier penalty and behavioral availability
    mult = dq_mult * avail_mult
    info = {
        "honeypot": False,
        "dq_mult": round(dq_mult, 3), "dq_reasons": dq_reasons,
        "avail_mult": round(avail_mult, 3), "avail_reasons": avail_reasons,
    }
    return min(1.0, mult), info, False
