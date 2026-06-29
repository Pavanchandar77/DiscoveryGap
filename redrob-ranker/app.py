#!/usr/bin/env python3
"""Talent Conviction Engine — sandbox (REQUIRED 'sandbox link').

Runs on CPU with the deterministic offline embedding backend.
Designed to boot instantly on HuggingFace Spaces.
"""
import sys, json, io, csv
from pathlib import Path
import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
from redrob_ranker import config as C                              # noqa: E402
from redrob_ranker.schema import Candidate                          # noqa: E402
from redrob_ranker.embed import encode_texts, encode_query, cosine_to_jd, pool_normalize  # noqa: E402
from redrob_ranker.score import score_candidate                     # noqa: E402
from redrob_ranker import reasoning, presentation                   # noqa: E402

st.set_page_config(page_title="Talent Conviction Engine", layout="wide")

# Custom CSS for premium styling
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');

/* Global Font Override */
html, body, [class*="css"], .stMarkdown, p, div, span, label, h1, h2, h3, h4, h5, h6 {
    font-family: 'Outfit', sans-serif !important;
}

/* Background gradient styling */
[data-testid="stAppViewContainer"] {
    background-color: #08090d !important;
    background-image: 
        radial-gradient(circle at 10% 20%, rgba(99, 102, 241, 0.12) 0%, transparent 40%),
        radial-gradient(circle at 90% 80%, rgba(192, 132, 252, 0.08) 0%, transparent 40%) !important;
}

/* Metric card styling */
div[data-testid="metric-container"] {
    background: rgba(30, 41, 59, 0.3) !important;
    border: 1px solid rgba(255, 255, 255, 0.06) !important;
    border-radius: 16px !important;
    padding: 24px 28px !important;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.25) !important;
    backdrop-filter: blur(10px) !important;
    -webkit-backdrop-filter: blur(10px) !important;
    transition: transform 0.3s ease, border-color 0.3s ease !important;
}

div[data-testid="metric-container"]:hover {
    transform: translateY(-2px) !important;
    border-color: rgba(167, 139, 250, 0.3) !important;
}

div[data-testid="stMetricValue"] {
    font-size: 2.4rem !important;
    font-weight: 800 !important;
    background: linear-gradient(135deg, #c084fc 0%, #818cf8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* File Uploader Container */
section[data-testid="stFileUploadDropzone"] {
    background: rgba(30, 41, 59, 0.15) !important;
    border: 2px dashed rgba(167, 139, 250, 0.35) !important;
    border-radius: 16px !important;
    padding: 30px !important;
    transition: all 0.3s ease !important;
}

section[data-testid="stFileUploadDropzone"]:hover {
    border-color: #a78bfa !important;
    background: rgba(30, 41, 59, 0.25) !important;
    box-shadow: 0 0 15px rgba(167, 139, 250, 0.15) !important;
}

/* Download Button styling */
div[data-testid="stDownloadButton"] button {
    background: linear-gradient(90deg, #c084fc 0%, #6366f1 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 30px !important;
    padding: 12px 36px !important;
    font-weight: 700 !important;
    font-size: 1.05rem !important;
    box-shadow: 0 4px 18px rgba(99, 102, 241, 0.35) !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    cursor: pointer !important;
}

div[data-testid="stDownloadButton"] button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(99, 102, 241, 0.5) !important;
}

/* Glassmorphism containers */
div.stAlert, div.stExpander, div[data-testid="stDataFrame"] {
    background: rgba(30, 41, 59, 0.2) !important;
    border: 1px solid rgba(255, 255, 255, 0.05) !important;
    border-radius: 12px !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15) !important;
}

/* Text Headers styling */
h1 {
    background: linear-gradient(90deg, #c084fc 0%, #6366f1 50%, #38bdf8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 800 !important;
    font-size: 3.5rem !important;
    letter-spacing: -0.05em !important;
    margin-bottom: 10px !important;
}

h2, h3 {
    font-weight: 700 !important;
    color: #f8fafc !important;
    letter-spacing: -0.02em !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style="background: linear-gradient(135deg, rgba(99, 102, 241, 0.12), rgba(192, 132, 252, 0.12)); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 20px; padding: 40px; text-align: center; margin-top: 10px; margin-bottom: 30px; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.25);">
    <span style="background: linear-gradient(90deg, #c084fc, #6366f1); color: white; padding: 6px 14px; border-radius: 20px; font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.15em; box-shadow: 0 0 15px rgba(99, 102, 241, 0.4);">INDIA.RUNS Track 1 — Category Defining</span>
    <h1 style="margin: 20px 0 10px 0; font-size: 3.5rem; font-weight: 800; background: linear-gradient(90deg, #c084fc, #6366f1, #38bdf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: -0.04em; font-family: 'Outfit', sans-serif;">Talent Conviction Engine</h1>
    <p style="color: #94a3b8; font-size: 1.1rem; max-width: 700px; margin: 0 auto; line-height: 1.6; font-family: 'Outfit', sans-serif;">Identify overlooked candidates, quantify conviction, and expose why traditional ATS search systems missed them.</p>
</div>
""", unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def _jd_text() -> str:
    p = ROOT / "data" / "job_description.txt"
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
st.markdown("<h2 style='font-family: \"Outfit\"; font-weight: 700; color: #f8fafc; margin-bottom: 20px;'>Talent Market Intelligence</h2>", unsafe_allow_html=True)
m1, m2, m3, m4 = st.columns(4)

with m1:
    st.markdown(f"""
    <div style="background: rgba(30, 41, 59, 0.35); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 18px; padding: 24px; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.25); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);">
        <div style="font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; color: #94a3b8; margin-bottom: 8px;">ATS Market Efficiency</div>
        <div style="font-size: 2.2rem; font-weight: 800; background: linear-gradient(135deg, #f43f5e 0%, #fda4af 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{eff:.0%}</div>
        <div style="font-size: 0.8rem; color: #f43f5e; margin-top: 4px; font-weight: 500;">-{1-eff:.0%} mispriced</div>
    </div>
    """, unsafe_allow_html=True)

with m2:
    st.markdown(f"""
    <div style="background: rgba(30, 41, 59, 0.35); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 18px; padding: 24px; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.25); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);">
        <div style="font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; color: #94a3b8; margin-bottom: 8px;">Hidden Gems Found</div>
        <div style="font-size: 2.2rem; font-weight: 800; background: linear-gradient(135deg, #10b981 0%, #34d399 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{len(gems)}</div>
        <div style="font-size: 0.8rem; color: #10b981; margin-top: 4px; font-weight: 500;">Overlooked top-tier candidates</div>
    </div>
    """, unsafe_allow_html=True)

with m3:
    avg_tmi_str = f"{int(np.mean(tmis)):+d}" if tmis else "—"
    st.markdown(f"""
    <div style="background: rgba(30, 41, 59, 0.35); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 18px; padding: 24px; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.25); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);">
        <div style="font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; color: #94a3b8; margin-bottom: 8px;">Avg Mispricing (TMI)</div>
        <div style="font-size: 2.2rem; font-weight: 800; background: linear-gradient(135deg, #c084fc 0%, #818cf8 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{avg_tmi_str}</div>
        <div style="font-size: 0.8rem; color: #a78bfa; margin-top: 4px; font-weight: 500;">Mean rank positions saved</div>
    </div>
    """, unsafe_allow_html=True)

with m4:
    highest_tmi_str = f"{max(tmis):+d}" if tmis else "—"
    st.markdown(f"""
    <div style="background: rgba(30, 41, 59, 0.35); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 18px; padding: 24px; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.25); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);">
        <div style="font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; color: #94a3b8; margin-bottom: 8px;">Highest TMI</div>
        <div style="font-size: 2.2rem; font-weight: 800; background: linear-gradient(135deg, #38bdf8 0%, #60a5fa 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{highest_tmi_str}</div>
        <div style="font-size: 0.8rem; color: #38bdf8; margin-top: 4px; font-weight: 500;">Max rank position saved</div>
    </div>
    """, unsafe_allow_html=True)

# --- Screen 2: the single biggest ATS failure ---
hero = max(cards[:20], key=lambda c: (c["tmi"] if c["tmi"] is not None else -1)) if cards else None
if hero:
    st.markdown("<h2 style='font-family: \"Outfit\"; font-weight: 700; color: #f8fafc; margin-top: 40px; margin-bottom: 20px;'>Why Traditional Hiring Fails — Exhibit A</h2>", unsafe_allow_html=True)
    
    td_spans = " ".join(f'<span style="background: rgba(16, 185, 129, 0.1); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.2); padding: 4px 12px; border-radius: 20px; font-size: 0.85rem; font-weight: 500; margin-right: 8px; margin-bottom: 8px; display: inline-block;">✓ {d}</span>' for d in hero["trust_drivers"])
    cn_spans = f'<div style="margin-top: 12px;">' + " ".join(f'<span style="background: rgba(239, 68, 68, 0.08); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.15); padding: 4px 12px; border-radius: 20px; font-size: 0.85rem; font-weight: 500; margin-right: 8px; margin-bottom: 8px; display: inline-block;">⚠ {x}</span>' for x in hero["concerns"]) + '</div>' if hero["concerns"] else ''
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(99, 102, 241, 0.08), rgba(192, 132, 252, 0.08)); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 18px; padding: 30px; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.25);">
        <div style="display: flex; gap: 30px; margin-bottom: 24px; flex-wrap: wrap;">
            <div style="flex: 1; min-width: 140px; background: rgba(30, 41, 59, 0.3); padding: 16px; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.04);">
                <div style="font-size: 0.75rem; font-weight: 600; text-transform: uppercase; color: #94a3b8; margin-bottom: 4px;">ATS Rank</div>
                <div style="font-size: 1.8rem; font-weight: 800; color: #f43f5e;">#{hero['ats_rank']}</div>
            </div>
            <div style="flex: 1; min-width: 140px; background: rgba(30, 41, 59, 0.3); padding: 16px; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.04);">
                <div style="font-size: 0.75rem; font-weight: 600; text-transform: uppercase; color: #94a3b8; margin-bottom: 4px;">Engine Rank</div>
                <div style="font-size: 1.8rem; font-weight: 800; color: #10b981;">#{hero['our_rank']}</div>
            </div>
            <div style="flex: 1; min-width: 140px; background: rgba(30, 41, 59, 0.3); padding: 16px; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.04);">
                <div style="font-size: 0.75rem; font-weight: 600; text-transform: uppercase; color: #94a3b8; margin-bottom: 4px;">Mispricing Index (TMI)</div>
                <div style="font-size: 1.8rem; font-weight: 800; color: #a78bfa;">{hero['tmi']:+d}</div>
            </div>
        </div>
        <h3 style="margin-bottom: 12px; font-size: 1.3rem; font-weight: 700; color: #f8fafc; font-family: 'Outfit';">{hero['title']}</h3>
        <div style="margin-bottom: 16px;">
            {td_spans}
        </div>
        {cn_spans}
    </div>
    """, unsafe_allow_html=True)

# --- Hidden gems ---
if gems:
    st.markdown("<h2 style='font-family: \"Outfit\"; font-weight: 700; color: #f8fafc; margin-top: 40px; margin-bottom: 20px;'>💎 Hidden Gems — Buried by Keyword Search</h2>", unsafe_allow_html=True)
    
    for g in gems[:3]:
        td_html = " ".join(f'<span style="background: rgba(16, 185, 129, 0.08); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.15); padding: 4px 12px; border-radius: 20px; font-size: 0.85rem; font-weight: 500; margin-right: 8px; margin-bottom: 8px; display: inline-block;">✓ {d}</span>' for d in g["trust_drivers"])
        cn_html = f'<div style="margin-top: 10px;">' + " ".join(f'<span style="background: rgba(239, 68, 68, 0.08); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.15); padding: 4px 12px; border-radius: 20px; font-size: 0.85rem; font-weight: 500; margin-right: 8px; margin-bottom: 8px; display: inline-block;">⚠ {x}</span>' for x in g["concerns"]) + '</div>' if g["concerns"] else ''
        
        st.markdown(f"""
        <div style="background: rgba(16, 185, 129, 0.03); border: 1px solid rgba(16, 185, 129, 0.15); border-radius: 16px; padding: 24px; margin-bottom: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.15); backdrop-filter: blur(10px);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; flex-wrap: wrap; gap: 10px;">
                <span style="font-size: 1.25rem; font-weight: 700; color: #f8fafc; font-family: 'Outfit';">#{g['our_rank']} {g['title']}</span>
                <span style="background: rgba(16, 185, 129, 0.15); color: #34d399; padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; border: 1px solid rgba(16, 185, 129, 0.25);">Hidden Gem</span>
            </div>
            <div style="display: flex; gap: 20px; margin-bottom: 18px; font-size: 0.9rem; color: #94a3b8; flex-wrap: wrap;">
                <div>⚡ Fit: <strong style="color: #f8fafc;">{g['fit']}%</strong></div>
                <div>🎯 Conviction: <strong style="color: #f8fafc;">{g['conviction']}%</strong></div>
                <div>📈 TMI: <strong style="color: #34d399;">{g['tmi']:+d}</strong></div>
                <div>📋 Evidence Density: <strong style="color: #f8fafc;">{g['evidence_density']}%</strong> ({g['verified_skills']}/{g['claimed_skills']})</div>
            </div>
            <div style="margin-bottom: 8px;">
                {td_html}
            </div>
            {cn_html}
        </div>
        """, unsafe_allow_html=True)

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
