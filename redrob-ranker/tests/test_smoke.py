"""Smoke tests: pipeline imports, honeypot logic fires, validator passes on output."""
import sys, subprocess, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from redrob_ranker.schema import Candidate
from redrob_ranker import honeypot


def test_honeypot_fires_on_impossible_tenure():
    raw = {
        "candidate_id": "CAND_0000001",
        "profile": {"current_title": "X", "years_of_experience": 2.0, "summary": "", "headline": ""},
        "career_history": [{"company": "Acme", "title": "Eng", "start_date": "2020-01-01",
                            "end_date": None, "duration_months": 200, "is_current": True,
                            "industry": "Software", "company_size": "51-200", "description": ""}],
        "education": [], "skills": [], "redrob_signals": {},
    }
    is_hp, reasons = honeypot.detect(Candidate(raw))
    assert is_hp and reasons


def test_clean_profile_not_honeypot():
    raw = {
        "candidate_id": "CAND_0000002",
        "profile": {"current_title": "ML Engineer", "years_of_experience": 6.0,
                    "summary": "built ranking systems", "headline": ""},
        "career_history": [{"company": "Acme", "title": "ML Engineer", "start_date": "2020-01-01",
                            "end_date": None, "duration_months": 60, "is_current": True,
                            "industry": "Software", "company_size": "51-200", "description": "ranking"}],
        "education": [], "skills": [], "redrob_signals": {},
    }
    is_hp, _ = honeypot.detect(Candidate(raw))
    assert not is_hp
