"""Smoke tests: pipeline imports, honeypot logic fires, validator passes on output."""
import sys, subprocess, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from redrob_ranker.schema import Candidate
from redrob_ranker import honeypot
from redrob_ranker import embed
import numpy as np


def test_offline_embedding_is_deterministic_and_normalized():
    """The hashing backend must be byte-reproducible (no network, no salted hash) so the
    judges' offline precompute reproduces ours exactly."""
    texts = ["built a ranking system at a product company", "marketing manager"]
    a = embed._encode_hashing(texts, 384)
    b = embed._encode_hashing(texts, 384)
    assert a.shape == (2, 384) and a.dtype == np.float32
    assert np.array_equal(a, b)                      # deterministic across calls
    assert np.allclose(np.linalg.norm(a, axis=1), 1.0, atol=1e-4)  # L2-normalized
    # different texts -> different vectors
    assert not np.array_equal(a[0], a[1])


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


def test_honeypot_fires_on_assessment_experience_contradiction():
    """A candidate with under 3 years experience claiming 5+ expert level skills with 90+ assessments is flagged."""
    raw = {
        "candidate_id": "CAND_0000003",
        "profile": {"current_title": "ML Engineer", "years_of_experience": 2.0, "summary": "", "headline": ""},
        "career_history": [],
        "education": [],
        "skills": [],
        "redrob_signals": {
            "skill_assessment_scores": {
                "Python": 95,
                "SQL": 92,
                "embeddings": 91,
                "retrieval": 96,
                "ranking": 90
            }
        }
    }
    is_hp, reasons = honeypot.detect(Candidate(raw))
    assert is_hp
    assert any("skills scored 90+" in r for r in reasons)


def test_bluff_detector_flags_expert_with_low_assessment():
    """Exhibiting an expert claim with low assessment triggers a bluff flag."""
    from redrob_ranker.features import capability
    raw = {
        "candidate_id": "CAND_0000004",
        "profile": {"current_title": "ML Engineer", "years_of_experience": 5.0, "summary": "", "headline": ""},
        "career_history": [],
        "education": [],
        "skills": [{"name": "embeddings", "proficiency": "expert", "duration_months": 24}],
        "redrob_signals": {"skill_assessment_scores": {"embeddings": 20}}
    }
    _, info = capability(Candidate(raw), 0.5)
    assert info["bluffs"] == 1
    assert info["core_bluffs"] == 1
    assert any("embeddings" in b for b in info["bluff_details"])


def test_counterfactual_explanation_format():
    """Counterfactual should return a valid promotion path instruction for non-top ranks."""
    from redrob_ranker.counterfactual import counterfactual
    raw = {
        "candidate_id": "CAND_0000005",
        "profile": {"current_title": "Backend Engineer", "years_of_experience": 5.0, "summary": "", "headline": ""},
        "career_history": [],
        "education": [],
        "skills": [],
        "redrob_signals": {}
    }
    scored = {
        "score": 0.35,
        "buckets": {"capability": 0.3, "growth": 0.4, "adaptability": 0.2},
        "title_gate": 0.4,
        "preference": 0.95
    }
    cf_text = counterfactual(Candidate(raw), scored, rank=20)
    assert cf_text is not None
    assert "Promotion path:" in cf_text


def test_rank_stability_categorization():
    """Rank stability label matches correct boundary thresholds."""
    from redrob_ranker.confidence import rank_stability_label
    # Under completely uniform buckets, cv should be 0 (Stable)
    label_stable = rank_stability_label(0.5, {"capability": 0.5, "growth": 0.5, "adaptability": 0.5}, 1.0)
    assert label_stable == "Stable"
    
    # Highly skewed buckets should result in Fragile or Moderate stability
    label_skewed = rank_stability_label(0.5, {"capability": 0.95, "growth": 0.05, "adaptability": 0.05}, 1.0)
    assert label_skewed in ("Fragile", "Moderate")
