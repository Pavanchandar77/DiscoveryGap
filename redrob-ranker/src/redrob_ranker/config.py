"""Central configuration: every tunable weight, threshold, and domain map lives here.

Rationale: with no live leaderboard and only 3 submissions, we tune against our own
self-labeled eval set (eval/). Keeping all knobs in one documented place makes that
loop fast and keeps rank.py readable. DO NOT scatter magic numbers across modules.
"""
from __future__ import annotations
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = ROOT / "artifacts"
DATA = ROOT / "data"

CAND_VECS = ARTIFACTS / "cand_vecs.npy"        # (N, d) float32, L2-normalized
CAND_META = ARTIFACTS / "cand_meta.parquet"    # parsed/normalized per-candidate features
JD_VEC = ARTIFACTS / "jd_vec.npy"              # (d,) float32, L2-normalized
SKILL_ALIAS = ARTIFACTS / "skill_alias.json"   # raw skill -> canonical skill

# ---------------------------------------------------------------------------
# Embedding model (PRECOMPUTE only — never loaded during the 5-min ranking step)
# ---------------------------------------------------------------------------
EMBED_MODEL = "BAAI/bge-small-en-v1.5"   # small, CPU-friendly, strong retrieval. e5-small-v2 also fine.
EMBED_DIM = 384
EMBED_BATCH = 256

# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
TOP_K = 100                  # HARD: exactly 100 rows out
SCORE_DECIMALS = 4           # score precision in CSV
SUBMISSION_HEADER = ["candidate_id", "rank", "score", "reasoning"]

# ---------------------------------------------------------------------------
# Bucket weights for the FIT composite (tune on self-eval). Sum need not be 1.
# ---------------------------------------------------------------------------
W_CAPABILITY = 0.55
W_GROWTH = 0.20
W_ADAPTABILITY = 0.25

# Within-capability sub-weights
W_CAP_SKILL = 0.45      # normalized skill overlap with JD requirements
W_CAP_SEMANTIC = 0.35   # cosine(JD, candidate text)
W_CAP_EVIDENCE = 0.20   # assessment scores / endorsements / proficiency*duration

# ---------------------------------------------------------------------------
# Title gate (multiplicative VETO). The decisive anti-stuffer mechanism.
# A non-technical title cannot be lifted to the top by a stuffed skill list.
# ---------------------------------------------------------------------------
TITLE_FLOOR = 0.15          # worst-case multiplier for an off-role title
TITLE_FULL = 1.0            # on-role title

# Titles that ARE plausibly the target role (normalized, lowercased substrings).
TECH_FIT_TITLES = [
    "ai engineer", "machine learning engineer", "ml engineer", "applied scientist",
    "research engineer", "data scientist", "software engineer", "backend engineer",
    "search engineer", "nlp engineer", "ml scientist", "staff engineer", "principal engineer",
    "data engineer", "platform engineer", "founding engineer",
    "recommendation", "ai specialist", "relevance engineer",  # genuine fit titles the list missed
]
# Titles that are the classic stuffer trap (AI skills on a non-tech role).
TRAP_TITLES = [
    "marketing manager", "hr manager", "accountant", "sales executive", "content writer",
    "graphic designer", "civil engineer", "mechanical engineer", "operations manager",
    "project manager", "business analyst", "customer support",
]
# Business Analyst / Project Manager are ambiguous: only allowed if description shows
# genuine ML/IR system-building (handled in features.py, not a flat ban).

# Title seniority levels for career-momentum scoring.
TITLE_LEVELS = {
    "intern": 0, "junior": 1, "associate": 1, "": 2,
    "engineer": 2, "analyst": 2, "developer": 2,
    "senior": 3, "lead": 4, "staff": 4, "principal": 5,
    "manager": 4, "head": 5, "director": 5, "vp": 6, "cto": 7,
}

# ---------------------------------------------------------------------------
# JD skill requirements (canonical skills; matched after aliasing)
# ---------------------------------------------------------------------------
JD_CORE_SKILLS = [
    "embeddings", "retrieval", "ranking", "vector search", "semantic search",
    "information retrieval", "recommendation systems", "python", "nlp",
    "learning to rank", "evaluation metrics",
]
JD_NICE_SKILLS = [
    "llm fine-tuning", "lora", "qlora", "peft", "xgboost", "distributed systems",
    "sentence transformers", "bge", "e5", "faiss", "qdrant", "pinecone", "milvus",
    "weaviate", "opensearch", "elasticsearch", "a/b testing", "ndcg", "mrr", "map",
]
# Skills that, when dominant WITHOUT IR/NLP, signal the CV/speech/robotics disqualifier.
CV_SPEECH_SKILLS = [
    "image classification", "gans", "tts", "speech recognition", "computer vision",
    "object detection", "image segmentation", "ocr", "asr", "robotics",
]
IR_NLP_SKILLS = [
    "nlp", "retrieval", "information retrieval", "ranking", "search", "embeddings",
    "semantic search", "recommendation systems", "llm", "transformers",
]

# ---------------------------------------------------------------------------
# Skill alias seed (extend in precompute by lowercasing + this map).
# Maps many raw forms to a canonical skill string used everywhere.
# ---------------------------------------------------------------------------
SKILL_ALIAS_SEED = {
    "k8s": "kubernetes", "kubernetes": "kubernetes",
    "fine-tuning llms": "llm fine-tuning", "fine tuning": "llm fine-tuning",
    "llm fine-tuning": "llm fine-tuning", "peft": "peft", "lora": "lora", "qlora": "qlora",
    "sentence-transformers": "sentence transformers", "sentence transformers": "sentence transformers",
    "vector db": "vector search", "vector database": "vector search",
    "faiss": "faiss", "qdrant": "qdrant", "pinecone": "pinecone", "milvus": "milvus",
    "weaviate": "weaviate", "opensearch": "opensearch", "elasticsearch": "elasticsearch",
    "recsys": "recommendation systems", "recommender systems": "recommendation systems",
    "recommendation systems": "recommendation systems",
    "information retrieval": "information retrieval", "ir": "information retrieval",
    "learning to rank": "learning to rank", "ltr": "learning to rank",
    "natural language processing": "nlp", "nlp": "nlp",
    "gcp": "gcp", "aws": "aws", "azure": "azure",
}

# ---------------------------------------------------------------------------
# Transferability adjacency: canonical skill -> set of credited adjacent skills.
# Lets a keyword-poor-but-adjacent candidate get partial credit (the "hidden gem" lift).
# ---------------------------------------------------------------------------
TRANSFER_MAP = {
    "aws": ["gcp", "azure"], "gcp": ["aws", "azure"], "azure": ["aws", "gcp"],
    "vector search": ["faiss", "qdrant", "pinecone", "milvus", "weaviate", "elasticsearch", "opensearch"],
    "ranking": ["learning to rank", "recommendation systems", "information retrieval"],
    "recommendation systems": ["ranking", "information retrieval", "retrieval"],
    "retrieval": ["information retrieval", "semantic search", "vector search", "embeddings"],
    "embeddings": ["sentence transformers", "semantic search", "retrieval"],
    "nlp": ["transformers", "llm fine-tuning", "information retrieval"],
}
TRANSFER_CREDIT = 0.6   # fraction of a direct match awarded for an adjacent skill

# ---------------------------------------------------------------------------
# Consulting-only disqualifier
# ---------------------------------------------------------------------------
CONSULTING_FIRMS = [
    "tcs", "tata consultancy", "infosys", "wipro", "accenture", "cognizant",
    "capgemini", "hcl", "tech mahindra", "mindtree",  # mindtree = product-adjacent but services-heavy
]
PRODUCT_INDUSTRIES = ["software", "fintech", "e-commerce", "edtech", "food delivery"]

# ---------------------------------------------------------------------------
# Plain-language transfer detector: phrases in summary/description that indicate
# real system-building even without the buzzwords. (The JD's stated "right answer".)
# ---------------------------------------------------------------------------
PLAINLANG_FIT_PHRASES = [
    "recommendation system", "search system", "ranking system", "matching system",
    "built a search", "built search", "relevance", "retrieval", "personalization",
    "scoring model", "feature pipeline", "embeddings", "semantic", "a/b test",
    "recommender", "candidate matching", "feed ranking",
]
# The decisive subset: phrases that denote actually BUILDING a ranking/search/recsys
# system (the JD's stated "right answer"), as opposed to weak supporting phrases like
# "a/b test" or "feature pipeline" that a data analyst might also use. A genuine
# plain-language fit must show at least one of these, not just the supporting ones.
SYSTEM_BUILD_PHRASES = [
    "recommendation system", "recommender", "search system", "ranking system",
    "matching system", "built a search", "built search", "candidate matching",
    "feed ranking", "personalization", "scoring model",
]

# ---------------------------------------------------------------------------
# Behavioral availability multiplier knobs (signals.py)
# ---------------------------------------------------------------------------
STALE_DAYS = 150            # last_active older than this => stale penalty kicks in
STALE_FLOOR = 0.55          # worst-case behavioral multiplier for fully unreachable
RESP_RATE_FULL = 0.5        # response rate at/above this contributes no penalty
TODAY = "2026-06-15"        # reference date for recency (matches challenge context)

# Behavioral sub-weights (combined then mapped to a multiplier in STALE_FLOOR..1.0)
BEHAVIOR_WEIGHTS = {
    "recency": 0.30,
    "response": 0.25,
    "open_to_work": 0.15,
    "recruiter_pull": 0.15,   # saved_by_recruiters_30d + search_appearance
    "follow_through": 0.15,   # interview_completion_rate, offer_acceptance_rate
}

# ---------------------------------------------------------------------------
# Location preference (soft positive)
# ---------------------------------------------------------------------------
PREFERRED_LOCATIONS = ["pune", "noida", "hyderabad", "mumbai", "delhi", "gurgaon", "bengaluru", "bangalore"]
NOTICE_PREFERRED_DAYS = 30

# ---------------------------------------------------------------------------
# Honeypot thresholds (honeypot.py) — pure logic
# ---------------------------------------------------------------------------
# This is a HARD-KILL gate (floors score, excludes from top-100), so it must be
# precision-first: a false positive silently kills a legitimate strong candidate.
# Thresholds calibrated against the real pool distributions (see scripts/honeypot_audit.py):
#   - sum(history_months) > yoe*12 is naturally ~0 for legit profiles (99th pctile = 0mo),
#     so a small overlap slack stays clean while catching genuine inconsistencies.
#   - skill duration_months vs career length is a SMOOTH NOISE TAIL for legit profiles
#     (modest overage from hobby/pre-career use is normal); only an overage that is BOTH
#     large in absolute months AND a multiple of the whole career is actually impossible.
#   - "job precedes education" is a normal life pattern (work, then a later degree) up to
#     several years; only an absurd gap (working as a child) is impossible.
TENURE_SLACK_MONTHS = 18         # sum(durations) may exceed yoe*12 by at most this (overlap slack)
SKILL_DUR_SLACK_MONTHS = 24      # a skill's duration may exceed career length by at most this (absolute)
SKILL_DUR_RATIO = 2.0            # ...AND only impossible if skill duration also exceeds career * this
EXPERT_ZERO_DUR_MAX = 2          # >2 "expert" skills with ~0 months used => suspicious
JOB_BEFORE_EDU_SLACK_YEARS = 12  # earliest job may precede earliest education by up to this (late-degree)
MIN_WORK_AGE = 18
