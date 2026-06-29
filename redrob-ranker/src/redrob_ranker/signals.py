"""Behavioral availability multiplier from the 23 redrob_signals.

The JD is explicit: a perfect-on-paper candidate who is stale and unresponsive is, for
hiring, not actually available — down-weight them. This produces a multiplier in
[STALE_FLOOR, 1.0] that scales the fit score. It NEVER excludes (that's honeypot/disqualifier).
"""
from __future__ import annotations
from datetime import datetime
from . import config as C
from .schema import Candidate

_TODAY = datetime.strptime(C.TODAY, "%Y-%m-%d").date()


def _clip01(x: float) -> float:
    return max(0.0, min(1.0, x))


def availability(cand: Candidate) -> tuple[float, list[str]]:
    s = cand.signals
    reasons: list[str] = []
    parts: dict[str, float] = {}

    # recency: 1.0 if active recently, decaying after STALE_DAYS
    la = cand.last_active
    if la is None:
        parts["recency"] = 0.4
    else:
        days = (_TODAY - la).days
        if days <= C.STALE_DAYS:
            parts["recency"] = 1.0
        else:
            # linear decay over the next ~6 months
            parts["recency"] = _clip01(1.0 - (days - C.STALE_DAYS) / 180.0)
            if parts["recency"] < 0.5:
                reasons.append(f"inactive ~{days} days")

    # response rate
    rr = float(s.get("recruiter_response_rate") or 0.0)
    parts["response"] = _clip01(rr / C.RESP_RATE_FULL)
    if rr < 0.15:
        reasons.append(f"low recruiter response rate ({rr:.2f})")

    # open to work
    parts["open_to_work"] = 1.0 if s.get("open_to_work_flag") else 0.65
    if not s.get("open_to_work_flag"):
        reasons.append("not marked open to work")

    # recruiter pull (demand signal)
    saved = float(s.get("saved_by_recruiters_30d") or 0)
    appear = float(s.get("search_appearance_30d") or 0)
    parts["recruiter_pull"] = _clip01(saved / 10.0 * 0.6 + appear / 300.0 * 0.4)

    # follow-through
    icr = float(s.get("interview_completion_rate") or 0.0)
    oar = s.get("offer_acceptance_rate")
    oar = 0.5 if (oar is None or oar < 0) else float(oar)  # -1 means no history -> neutral
    parts["follow_through"] = _clip01(0.6 * icr + 0.4 * oar)

    raw = sum(C.BEHAVIOR_WEIGHTS[k] * parts[k] for k in C.BEHAVIOR_WEIGHTS)
    # map [0,1] raw into [STALE_FLOOR, 1.0]
    mult = C.STALE_FLOOR + (1.0 - C.STALE_FLOOR) * _clip01(raw)
    return (mult, reasons)
