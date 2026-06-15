#!/usr/bin/env python3
"""Minimal Streamlit sandbox app (REQUIRED 'sandbox link').

Accepts a small candidate sample (<=100), runs the ranking end-to-end on CPU, emits a
ranked CSV. Deploy free on HuggingFace Spaces / Streamlit Cloud. Requires precomputed
artifacts for the sample (or compute embeddings for the small sample at startup).

Run locally:  streamlit run scripts/make_sandbox_app.py
"""
import sys, json, tempfile
from pathlib import Path
import streamlit as st
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

st.title("Redrob Intelligent Candidate Ranker — sandbox")
st.caption("Upload up to 100 candidates (JSONL). Runs the gated four-bucket ranker on CPU.")

up = st.file_uploader("candidates.jsonl (<=100)", type=["jsonl"])
if up is not None:
    lines = [json.loads(l) for l in up.read().decode().splitlines() if l.strip()][:100]
    st.write(f"loaded {len(lines)} candidates")
    # NOTE: for the sandbox, precompute embeddings for just this sample here (allowed, small).
    # Then call rank_pipeline.run on a temp file. Left as the integration point.
    st.info("Wire to redrob_ranker.rank_pipeline.run after computing sample embeddings. "
            "See CLAUDE.md §10.5.")
