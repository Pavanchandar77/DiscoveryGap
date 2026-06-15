"""Typed access helpers over a raw candidate dict (matches candidate_schema.json).

We keep this thin: raw dicts are loaded from JSONL; this wraps them with safe
accessors and computed convenience properties used across modules.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any


def _parse_date(s: str | None) -> date | None:
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


@dataclass
class Candidate:
    raw: dict[str, Any]

    # ---- identity ----
    @property
    def id(self) -> str:
        return self.raw["candidate_id"]

    @property
    def profile(self) -> dict:
        return self.raw.get("profile", {})

    @property
    def title(self) -> str:
        return (self.profile.get("current_title") or "").strip()

    @property
    def headline(self) -> str:
        return self.profile.get("headline", "") or ""

    @property
    def summary(self) -> str:
        return self.profile.get("summary", "") or ""

    @property
    def years_experience(self) -> float:
        return float(self.profile.get("years_of_experience") or 0.0)

    @property
    def industry(self) -> str:
        return (self.profile.get("current_industry") or "").strip()

    @property
    def location(self) -> str:
        return (self.profile.get("location") or "").strip()

    @property
    def country(self) -> str:
        return (self.profile.get("country") or "").strip()

    # ---- collections ----
    @property
    def history(self) -> list[dict]:
        return self.raw.get("career_history", []) or []

    @property
    def education(self) -> list[dict]:
        return self.raw.get("education", []) or []

    @property
    def skills(self) -> list[dict]:
        return self.raw.get("skills", []) or []

    @property
    def certifications(self) -> list[dict]:
        return self.raw.get("certifications", []) or []

    @property
    def signals(self) -> dict:
        return self.raw.get("redrob_signals", {}) or {}

    # ---- convenience ----
    @property
    def companies(self) -> list[str]:
        return [(h.get("company") or "").strip() for h in self.history]

    @property
    def all_text(self) -> str:
        """Concatenated text used for embedding + plain-language detection."""
        parts = [self.headline, self.summary]
        parts += [h.get("description", "") or "" for h in self.history]
        parts += [h.get("title", "") or "" for h in self.history]
        return " \n ".join(p for p in parts if p)

    def signal(self, key: str, default=None):
        return self.signals.get(key, default)

    @property
    def last_active(self) -> date | None:
        return _parse_date(self.signals.get("last_active_date"))

    @property
    def total_history_months(self) -> int:
        return sum(int(h.get("duration_months") or 0) for h in self.history)

    @property
    def avg_tenure_months(self) -> float:
        durs = [int(h.get("duration_months") or 0) for h in self.history]
        return (sum(durs) / len(durs)) if durs else 0.0
