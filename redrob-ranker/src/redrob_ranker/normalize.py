"""Normalization: the unglamorous layer where a lot of accuracy is won.

- skill aliasing: map raw skill strings to canonical forms
- title leveling: map a title to a seniority integer
- title-role classification: is this title plausibly the JD role, a trap, or ambiguous
"""
from __future__ import annotations
import re
from . import config as C
from .schema import Candidate


def canon_skill(raw: str) -> str:
    """Map a raw skill name to its canonical form (lowercased)."""
    s = (raw or "").strip().lower()
    s = re.sub(r"\s+", " ", s)
    return C.SKILL_ALIAS_SEED.get(s, s)


def canon_skills(cand: Candidate) -> list[str]:
    return [canon_skill(sk.get("name", "")) for sk in cand.skills]


def title_level(title: str) -> int:
    """Highest matching seniority token in the title; default mid-level (2)."""
    t = (title or "").lower()
    best = None
    for token, lvl in C.TITLE_LEVELS.items():
        if token and token in t:
            best = lvl if best is None else max(best, lvl)
    return best if best is not None else 2


def classify_title(title: str) -> str:
    """Return 'fit' | 'trap' | 'ambiguous' for the title-gate logic.

    'ambiguous' titles (Business Analyst, Project Manager) require description
    evidence in features.py before they earn a high gate.
    """
    t = (title or "").lower()
    for good in C.TECH_FIT_TITLES:
        if good in t:
            return "fit"
    if "business analyst" in t or "project manager" in t:
        return "ambiguous"
    for trap in C.TRAP_TITLES:
        if trap in t:
            return "trap"
    return "ambiguous"


def career_title_levels(cand: Candidate) -> list[int]:
    """Seniority level over time, oldest->newest, for momentum scoring."""
    hist = sorted(
        cand.history,
        key=lambda h: (h.get("start_date") or ""),
    )
    return [title_level(h.get("title", "")) for h in hist]


def is_consulting_company(name: str) -> bool:
    n = (name or "").lower()
    return any(f in n for f in C.CONSULTING_FIRMS)


def has_product_company(cand: Candidate) -> bool:
    """True if any role was at a product company (industry or non-consulting signal)."""
    for h in cand.history:
        ind = (h.get("industry") or "").lower()
        comp = (h.get("company") or "").lower()
        if any(p in ind for p in C.PRODUCT_INDUSTRIES) and not is_consulting_company(comp):
            return True
    return False
