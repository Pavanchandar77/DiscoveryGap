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
st.caption("Fit = how relevant · Conviction = how certain · Talent Mispricing Index (TMI) = how much a "
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
n = len(cards)
tmis = [c["tmi"] for c in cards if c["tmi"] is not None]
eff = (sum(1 for c in cards if c["ats_rank"] and c["ats_rank"] <= n) / n) if n else 0.0

# --- Screen 1: Talent Market Intelligence (hero dashboard) ---
st.header("Talent Market Intelligence")
m1, m2, m3, m4 = st.columns(4)
m1.metric("ATS Market Efficiency", f"{eff:.0%}", f"-{1-eff:.0%} mispriced", delta_color="inverse")
m2.metric("Hidden Gems Found", len(gems))
m3.metric("Avg Mispricing (TMI)", f"{int(np.mean(tmis)):+d}" if tmis else "—")
m4.metric("Highest TMI", f"{max(tmis):+d}" if tmis else "—")

# --- Screen 2: the single biggest ATS failure ---
hero = max(cards[:20], key=lambda c: (c["tmi"] if c["tmi"] is not None else -1)) if cards else None
if hero:
    st.subheader("Why traditional hiring fails — exhibit A")
    f1, f2, f3 = st.columns(3)
    f1.metric("ATS Rank", f"#{hero['ats_rank']}")
    f2.metric("Our Rank", f"#{hero['our_rank']}")
    f3.metric("Talent Mispricing Index", f"{hero['tmi']:+d}")
    st.markdown(f"**{hero['title']}** — " + "  ".join(f"✓ {d}" for d in hero["trust_drivers"]))
    if hero["concerns"]:
        st.caption("  ".join(f"⚠ {x}" for x in hero["concerns"]))

# --- Hidden gems ---
if gems:
    st.subheader("💎 Hidden Gems — high conviction, buried by keyword search")
    for g in gems[:3]:
        st.markdown(f"**#{g['our_rank']} {g['title']}** — Fit **{g['fit']}**, Conviction "
                    f"**{g['conviction']}%**, **TMI {g['tmi']:+d}** (undervalued by {g['tmi']} "
                    f"positions vs ATS rank {g['ats_rank']}) · Evidence Density "
                    f"{g['evidence_density']}% ({g['verified_skills']}/{g['claimed_skills']})")
        st.markdown("  ".join(f"✓ {d}" for d in g["trust_drivers"]))
        if g["concerns"]:
            st.caption("  ".join(f"⚠ {x}" for x in g["concerns"]))

# --- Quadrant chart ---
st.subheader("The bet map — Fit × Conviction (bubble = how badly the ATS mispriced them)")
df = pd.DataFrame(cards)
df["tmi_size"] = df["tmi"].clip(lower=0)        # bubble size = undervaluation (non-negative)
try:
    import altair as alt
    pts = alt.Chart(df).mark_circle(opacity=0.75).encode(
        x=alt.X("fit:Q", title="Fit (relevance)"),
        y=alt.Y("conviction:Q", title="Conviction (certainty)"),
        color=alt.Color("quadrant:N", legend=alt.Legend(title="Quadrant")),
        size=alt.Size("tmi_size:Q", title="Talent Mispricing Index"),
        tooltip=["our_rank", "title", "fit", "conviction", "tmi", "evidence_density", "quadrant"],
    )
    rules = (alt.Chart(pd.DataFrame({"y": [60]})).mark_rule(strokeDash=[4, 4]).encode(y="y:Q"))
    st.altair_chart((pts + rules).interactive(), use_container_width=True)
except Exception:
    st.scatter_chart(df, x="fit", y="conviction", color="quadrant")

# --- Full table + per-candidate explanation ---
st.subheader("Ranked candidates")
st.dataframe(
    df[["our_rank", "candidate_id", "title", "fit", "conviction", "tmi",
        "evidence_density", "quadrant"]].rename(columns={"tmi": "TMI", "evidence_density": "evidence%"}),
    use_container_width=True, hide_index=True,
)
with st.expander("Why we trust each candidate (Trust Drivers & Concerns)"):
    for c in cards[:25]:
        st.markdown(f"**#{c['our_rank']} {c['title']}** · Fit {c['fit']} · "
                    f"Conviction {c['conviction']}% · TMI {c['tmi']:+d} · Stability: **{c.get('stability', 'Stable')}**")
        st.markdown("  ".join(f"✓ {d}" for d in c["trust_drivers"]) or "_—_")
        if c["concerns"]:
            st.caption("  ".join(f"⚠ {x}" for x in c["concerns"]))
        if c.get("counterfactual"):
            st.caption(f"💡 {c['counterfactual']}")

# --- Valid 4-column submission ---
buf = io.StringIO(); w = csv.writer(buf); w.writerow(C.SUBMISSION_HEADER)
for c in cards[:C.TOP_K]:
    w.writerow([c["candidate_id"], c["our_rank"], f"{c['fit']/100:.4f}", c["reasoning"]])
st.download_button("⬇ Download submission.csv", buf.getvalue(),
                   file_name="submission.csv", mime="text/csv")
