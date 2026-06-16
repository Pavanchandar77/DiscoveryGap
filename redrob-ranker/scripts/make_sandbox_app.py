#!/usr/bin/env python3
"""Minimal Streamlit sandbox app (REQUIRED 'sandbox link').

Accepts a small candidate sample (<=100 JSONL records), computes embeddings for just
that sample on the fly (allowed — it's small), runs the SAME gated four-bucket ranker
that rank.py uses, and emits a ranked, downloadable CSV with reasoning.

Deploy free on HuggingFace Spaces / Streamlit Cloud (CPU). The embedding model is
downloaded once from HuggingFace at startup; this is the offline-equivalent precompute,
not the scored 5-minute ranking step.

Run locally:  streamlit run scripts/make_sandbox_app.py
"""
import sys, json
from pathlib import Path

import numpy as np
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from redrob_ranker import config as C            # noqa: E402
from redrob_ranker.schema import Candidate        # noqa: E402
from redrob_ranker.embed import encode_texts, encode_query, cosine_to_jd, pool_normalize  # noqa: E402
from redrob_ranker.rank_pipeline import rank_records, write_csv          # noqa: E402

st.set_page_config(page_title="Redrob Intelligent Candidate Ranker", layout="wide")
st.title("Redrob Intelligent Candidate Ranker — sandbox")
st.caption("Upload up to 100 candidates (JSONL). Runs the trap-resistant, gated "
           "four-bucket ranker on CPU and returns a ranked CSV with per-row reasoning.")


@st.cache_data(show_spinner=False)
def _jd_text() -> str:
    p = C.DATA / "job_description.txt"
    return p.read_text(encoding="utf-8") if p.exists() else (
        "Senior AI Engineer — embeddings, retrieval, ranking, evaluation frameworks, "
        "production ML at a product company.")


@st.cache_resource(show_spinner="Loading embedding model (first run only)…")
def _jd_vec() -> np.ndarray:
    return encode_query(_jd_text())


up = st.file_uploader("candidates.jsonl (<=100)", type=["jsonl"])
if up is not None:
    raws = [json.loads(l) for l in up.read().decode("utf-8").splitlines() if l.strip()][:100]
    st.write(f"Loaded **{len(raws)}** candidates.")

    with st.spinner("Embedding the sample and scoring…"):
        texts = [Candidate(r).all_text for r in raws]
        cand_vecs = encode_texts(texts)                      # (n, d), L2-normalized
        sem = pool_normalize(cosine_to_jd(cand_vecs, _jd_vec()))   # (n,) rescaled across the sample
        id_to_sem = {Candidate(r).id: float(s) for r, s in zip(raws, sem)}
        rows = rank_records(raws, id_to_sem, top_k=min(C.TOP_K, len(raws)))

    st.success(f"Ranked {len(rows)} candidates (honeypots and hard-disqualified excluded).")

    import csv, io
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(C.SUBMISSION_HEADER)
    w.writerows(rows)
    st.download_button("Download submission.csv", buf.getvalue(),
                       file_name="submission.csv", mime="text/csv")

    st.dataframe(
        [{"rank": r[1], "candidate_id": r[0], "score": r[2], "reasoning": r[3]} for r in rows],
        use_container_width=True, hide_index=True,
    )
else:
    st.info("Upload a JSONL sample to begin. Each line is one candidate record matching "
            "the challenge schema (profile, career_history, education, skills, redrob_signals).")
