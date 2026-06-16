#!/usr/bin/env python3
"""Talent Conviction Engine — sandbox (REQUIRED 'sandbox link').

Not just a ranker: for every candidate it shows three numbers an ATS never does —
Fit (relevance), Conviction (certainty), Discovery Gap (how much keyword search underrates
them) — plots them on a Fit×Conviction quadrant, surfaces the Hidden Gems the ATS buried, and
explains both sides (Trust Drivers / Concerns). Emits a valid 4-column submission CSV.

Runs on CPU with the deterministic offline embedding backend (no model download, no HF), so a
HuggingFace Space boots without reaching the network. Run locally:
  streamlit run scripts/make_sandbox_app.py
"""
import sys, json, io, csv
from pathlib import Path
import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from redrob_ranker import config as C                              # noqa: E402
from redrob_ranker.schema import Candidate                          # noqa: E402
from redrob_ranker.embed import encode_texts, encode_query, cosine_to_jd, pool_normalize  # noqa: E402
from redrob_ranker.score import score_candidate                     # noqa: E402
from redrob_ranker import reasoning, presentation                   # noqa: E402

st.set_page_config(page_title="Talent Conviction Engine", layout="wide")
st.title("🎯 Talent Conviction Engine")
st.markdown("**Identify overlooked candidates, quantify confidence in every recommendation, "
            "and explain exactly why traditional hiring systems missed them.**")
st.caption("Fit = how relevant · Conviction = how certain · Discovery Gap = how much a "
           "keyword/similarity ATS underrates them.")


@st.cache_data(show_spinner=False)
def _jd_text() -> str:
    p = C.DATA / "job_description.txt"
    return p.read_text(encoding="utf-8") if p.exists() else (
        "Senior AI Engineer — embeddings, retrieval, ranking, evaluation, production ML at a "
        "product company.")


@st.cache_resource(show_spinner="Loading embedding backend (first run only)…")
def _jd_vec() -> np.ndarray:
    return encode_query(_jd_text())


def _rank(raws: list[dict]) -> list[dict]:
    """Score, exclude honeypots, sort, and build a conviction card per candidate."""
    texts = [Candidate(r).all_text for r in raws]
    sem_raw = cosine_to_jd(encode_texts(texts), _jd_vec())          # ATS-style raw similarity
    sem = pool_normalize(sem_raw)
    id_sem = {Candidate(r).id: float(s) for r, s in zip(raws, sem)}
    # ATS baseline order (pure similarity) -> ats_rank
    order = sorted(range(len(raws)), key=lambda i: -sem_raw[i])
    ats_rank = {Candidate(raws[idx]).id: rank for rank, idx in enumerate(order, 1)}

    scored = []
    for r in raws:
        c = Candidate(r); s = score_candidate(c, id_sem.get(c.id, 0.0))
        if s["is_honeypot"]:
            continue
        s["rscore"] = round(s["score"], C.SCORE_DECIMALS)
        scored.append((c, s))
    scored.sort(key=lambda cs: (-cs[1]["rscore"], cs[0].id))

    cutoff = max(5, len(raws) // 3)        # cohort-relative "ATS missed them" threshold
    cards = []
    for i, (c, s) in enumerate(scored, 1):
        card = presentation.card(c, s, i, ats_rank.get(c.id), ats_cutoff=cutoff)
        card["reasoning"] = reasoning.make(c, s, i)
        cards.append(card)
    return cards


up = st.file_uploader("Upload candidates.jsonl (≤100)", type=["jsonl"])
if up is None:
    st.info("Upload a JSONL sample (each line = one candidate: profile, career_history, "
            "education, skills, redrob_signals).")
    st.stop()

raws = [json.loads(l) for l in up.read().decode("utf-8").splitlines() if l.strip()][:100]
with st.spinner("Scoring, scoring conviction, and finding hidden gems…"):
    cards = _rank(raws)

gems = [c for c in cards if c["quadrant"] == "Hidden Gem"]
obvious = [c for c in cards if c["quadrant"] == "Obvious Fit"]
c1, c2, c3 = st.columns(3)
c1.metric("Candidates ranked", len(cards))
c2.metric("Hidden Gems (ATS missed)", len(gems))
c3.metric("Obvious Fits", len(obvious))

# --- Hero: the hidden gems ---
if gems:
    st.subheader("💎 Hidden Gems — high conviction, buried by keyword search")
    for g in gems[:3]:
        st.markdown(f"**#{g['our_rank']} {g['title']}** — Fit **{g['fit']}**, Conviction "
                    f"**{g['conviction']}%**, Discovery Gap **{g['discovery_gap']:+d}** "
                    f"(ATS rank {g['ats_rank']})")
        st.markdown("  ".join(f"✓ {d}" for d in g["trust_drivers"]))
        if g["concerns"]:
            st.caption("  ".join(f"⚠ {x}" for x in g["concerns"]))

# --- Quadrant chart ---
st.subheader("The bet map — Fit × Conviction")
df = pd.DataFrame(cards)
try:
    import altair as alt
    pts = alt.Chart(df).mark_circle(opacity=0.75).encode(
        x=alt.X("fit:Q", title="Fit (relevance)"),
        y=alt.Y("conviction:Q", title="Conviction (certainty)"),
        color=alt.Color("quadrant:N", legend=alt.Legend(title="Quadrant")),
        size=alt.Size("discovery_gap:Q", title="Discovery Gap"),
        tooltip=["our_rank", "title", "fit", "conviction", "discovery_gap", "quadrant"],
    )
    rules = (alt.Chart(pd.DataFrame({"y": [60]})).mark_rule(strokeDash=[4, 4]).encode(y="y:Q"))
    st.altair_chart((pts + rules).interactive(), use_container_width=True)
except Exception:
    st.scatter_chart(df, x="fit", y="conviction", color="quadrant")

# --- Full table + per-candidate explanation ---
st.subheader("Ranked candidates")
st.dataframe(
    df[["our_rank", "candidate_id", "title", "fit", "conviction", "discovery_gap", "quadrant"]],
    use_container_width=True, hide_index=True,
)
with st.expander("Why we trust each candidate (Trust Drivers & Concerns)"):
    for c in cards[:25]:
        st.markdown(f"**#{c['our_rank']} {c['title']}** · Fit {c['fit']} · "
                    f"Conviction {c['conviction']}% · Gap {c['discovery_gap']:+d}")
        st.markdown("  ".join(f"✓ {d}" for d in c["trust_drivers"]) or "_—_")
        if c["concerns"]:
            st.caption("  ".join(f"⚠ {x}" for x in c["concerns"]))

# --- Valid 4-column submission ---
buf = io.StringIO(); w = csv.writer(buf); w.writerow(C.SUBMISSION_HEADER)
for c in cards[:C.TOP_K]:
    w.writerow([c["candidate_id"], c["our_rank"], f"{c['fit']/100:.4f}", c["reasoning"]])
st.download_button("⬇ Download submission.csv", buf.getvalue(),
                   file_name="submission.csv", mime="text/csv")
