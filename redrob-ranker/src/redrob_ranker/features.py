"""The four signal buckets. Each returns a 0..1 score plus a small dict of evidence
used later by reasoning.py. No model fitting — transparent, inspectable arithmetic.
"""
from __future__ import annotations
import numpy as np
from . import config as C
from .schema import Candidate
from .normalize import canon_skills, canon_skill, classify_title, career_title_levels, product_company_scale
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

    # --- Evidence (the JD calls skill_assessment_scores the strongest evidence signal) ---
    assess = cand.signals.get("skill_assessment_scores", {}) or {}
    assess_lower = {str(k).lower(): v for k, v in assess.items()}
    prof_w = {"beginner": 0.25, "intermediate": 0.5, "advanced": 0.8, "expert": 1.0}

    # Corroborate CLAIMED JD-relevant skills with their assessment scores; flag bluffs
    # (advanced/expert claim on a JD skill with a low assessment = an unproven claim).
    claimed_assess, dur_evid, bluffs = [], [], 0
    for sk in cand.skills:
        nm_raw = (sk.get("name") or "").lower()
        canon = canon_skill(sk.get("name", ""))
        if canon in (core | nice):
            w = prof_w.get(sk.get("proficiency", "intermediate"), 0.5)
            d = min(1.0, int(sk.get("duration_months") or 0) / 36.0)
            dur_evid.append(w * d)
            a = assess_lower.get(nm_raw)
            if a is not None:
                claimed_assess.append(a / 100.0)
                if sk.get("proficiency") in ("advanced", "expert") and a < 40:
                    bluffs += 1
    if claimed_assess:
        corroboration = float(np.mean(claimed_assess))          # assessment of the claimed JD skills
    elif assess:
        corroboration = float(np.mean(list(assess.values()))) / 100.0
    else:
        corroboration = 0.45
    ev_dur = float(np.mean(dur_evid)) if dur_evid else 0.3

    # Product-company-at-scale and external validation are positive evidence (JD).
    prod_scale = product_company_scale(cand)
    gh = float(cand.signals.get("github_activity_score", -1) or -1)
    text = cand.all_text.lower()
    validation = min(1.0, (min(0.6, gh / 20.0 * 0.6) if gh > 0 else 0.0)
                    + (0.25 if cand.certifications else 0.0)
                    + (0.15 if any(h in text for h in C.VALIDATION_TEXT_HINTS) else 0.0))

    evidence = (0.40 * corroboration + 0.25 * ev_dur +
                0.25 * prod_scale + 0.10 * validation)
    evidence *= (1.0 - 0.15 * min(bluffs, 3))   # discount unproven (bluffed) JD-skill claims

    sem = max(0.0, semantic)  # cosine can be slightly negative; floor at 0
    score = (C.W_CAP_SKILL * skill_score +
             C.W_CAP_SEMANTIC * sem +
             C.W_CAP_EVIDENCE * evidence)
    return min(1.0, score), {
        "core_hit": sorted(core_hit), "nice_hit": sorted(nice_hit),
        "semantic": round(sem, 3), "evidence": round(evidence, 3),
        "corroboration": round(corroboration, 3), "bluffs": bluffs,
        "prod_scale": round(prod_scale, 3),
    }


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
