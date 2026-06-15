"""Honeypot detection — PURE LOGIC, no ML.

The spec says ~80 candidates have subtly impossible profiles, forced to tier 0.
Ranking any in the top-10 signals a keyword-only system; >10% in top-100 = DISQUALIFIED.
We target 0 in top-100. We catch them with internal-consistency arithmetic.

Returns (is_honeypot: bool, reasons: list[str]). The reasons feed our self-eval audit.
"""
from __future__ import annotations
from . import config as C
from .schema import Candidate


def detect(cand: Candidate) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    yoe = cand.years_experience
    yoe_months = yoe * 12.0

    # 1. Sum of role durations far exceeds stated years of experience (beyond overlap slack).
    total = cand.total_history_months
    if total > yoe_months + C.TENURE_SLACK_MONTHS:
        reasons.append(
            f"role durations sum to {total}mo but only {yoe:.1f}yrs experience claimed"
        )

    # 2. A single skill used IMPOSSIBLY longer than the entire career. Legit profiles show a
    #    smooth noise tail of modest overage (hobby / pre-career use), so we require the overage
    #    to be BOTH large in absolute months AND a multiple of the whole career before flagging.
    for sk in cand.skills:
        dur = int(sk.get("duration_months") or 0)
        if (dur > yoe_months + C.SKILL_DUR_SLACK_MONTHS
                and dur > yoe_months * C.SKILL_DUR_RATIO):
            reasons.append(
                f"skill '{sk.get('name')}' used {dur}mo > {C.SKILL_DUR_RATIO:g}x career length {yoe_months:.0f}mo"
            )
            break

    # 3. Many "expert" skills with ~0 months of use.
    expert_zero = [
        sk for sk in cand.skills
        if sk.get("proficiency") == "expert" and int(sk.get("duration_months") or 0) <= 1
    ]
    if len(expert_zero) > C.EXPERT_ZERO_DUR_MAX:
        reasons.append(
            f"{len(expert_zero)} 'expert' skills with ~0 months used"
        )

    # 4. Tenure at a single role exceeds plausible company age (proxy: a role longer than yoe).
    for h in cand.history:
        dur = int(h.get("duration_months") or 0)
        if dur > yoe_months + C.TENURE_SLACK_MONTHS:
            reasons.append(
                f"role at {h.get('company')} lasted {dur}mo > total experience"
            )
            break

    # 5. Career started before plausible working age (start_year vs earliest education).
    edu_starts = [int(e.get("start_year") or 0) for e in cand.education if e.get("start_year")]
    job_starts = [
        (h.get("start_date") or "")[:4] for h in cand.history if (h.get("start_date") or "")
    ]
    job_years = [int(y) for y in job_starts if y.isdigit()]
    if edu_starts and job_years:
        # Working before a later degree is a normal life pattern; only an absurd gap (effectively
        # working as a child) is impossible. Guard with a generous slack to avoid false positives.
        if min(job_years) < min(edu_starts) - C.JOB_BEFORE_EDU_SLACK_YEARS:
            reasons.append(
                f"earliest job {min(job_years)} precedes earliest education {min(edu_starts)} "
                f"by >{C.JOB_BEFORE_EDU_SLACK_YEARS}yr"
            )

    # 6. Education end before start.
    for e in cand.education:
        sy, ey = e.get("start_year"), e.get("end_year")
        if sy and ey and int(ey) < int(sy):
            reasons.append(f"education end_year {ey} before start_year {sy}")
            break

    return (len(reasons) > 0, reasons)
