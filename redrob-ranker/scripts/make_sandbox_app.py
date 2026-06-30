#!/usr/bin/env python3
"""Talent Conviction Engine — sandbox (REQUIRED 'sandbox link').

Runs on CPU with the deterministic offline embedding backend.
Designed to boot instantly on HuggingFace Spaces.
"""
import sys, json, io, csv, time, textwrap
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
from redrob_ranker.service import rank_and_dashboard                # noqa: E402

st.set_page_config(page_title="Talent Conviction Engine", layout="wide")

def clean_html(html: str) -> str:
    return "\n".join(line.strip() for line in html.splitlines() if line.strip())

# Custom CSS for premium styling — matching React .tsx screens
st.markdown(clean_html("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');

/* ── Global Font ── */
html, body, [class*="css"], .stMarkdown, p, div, span, label,
h1, h2, h3, h4, h5, h6 {
    font-family: 'Outfit', sans-serif !important;
}

/* ── Fullscreen Background & Canvas Iframe ── */
.stApp {
    background-color: #020202 !important;
    background-image: radial-gradient(ellipse 120% 100% at 50% -10%, rgba(34,211,238,0.06) 0%, transparent 60%) !important;
}

iframe {
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    width: 100vw !important;
    height: 100vh !important;
    z-index: -1 !important;
    pointer-events: none !important;
    border: none !important;
}

[data-testid="stAppViewContainer"] {
    background: transparent !important;
}

/* Hide default Streamlit header */
[data-testid="stHeader"] {
    background-color: transparent !important;
}

/* ── FILE UPLOADER CARD ── */
[data-testid="stFileUploader"] {
    max-width: 750px !important;
    margin: 40px auto 30px auto !important;
    padding: 0 !important;
}

[data-testid="stFileUploadDropzone"] {
    background: rgba(7, 7, 9, 0.8) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 40px !important;
    padding: 12px 12px 12px 32px !important;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5) !important;
    backdrop-filter: blur(24px) !important;
    -webkit-backdrop-filter: blur(24px) !important;
    display: flex !important;
    flex-direction: row !important;
    align-items: center !important;
    justify-content: space-between !important;
    gap: 20px !important;
    min-height: 80px !important;
}

[data-testid="stFileUploadDropzone"]:hover {
    border-color: rgba(34, 211, 238, 0.3) !important;
    background: rgba(10, 13, 18, 0.9) !important;
}

/* Style the text wrapper to contain Title and Subtitle */
[data-testid="stUploadDropzoneText"] {
    display: block !important;
    text-align: left !important;
    font-size: 0 !important;
    line-height: 0 !important;
    flex: 1 !important;
}

[data-testid="stUploadDropzoneText"]::before {
    content: "Activate Discovery Engine" !important;
    display: block !important;
    font-size: 1.15rem !important;
    font-weight: 600 !important;
    color: #ffffff !important;
    line-height: 1.4 !important;
    font-family: 'Outfit', sans-serif !important;
}

[data-testid="stUploadDropzoneText"]::after {
    content: "Upload candidates.jsonl (≤100) to reveal hidden density." !important;
    display: block !important;
    font-size: 0.85rem !important;
    font-weight: 300 !important;
    color: #64748b !important;
    line-height: 1.4 !important;
    margin-top: 4px !important;
    font-family: 'Outfit', sans-serif !important;
}

/* Hide Streamlit icon/SVG next to the dropzone text */
[data-testid="stFileUploadDropzone"] svg {
    display: none !important;
}

/* Hide any small file limit text */
[data-testid="stFileUploadDropzone"] small {
    display: none !important;
}

/* Browse Files button — clean white pill */
[data-testid="stFileUploadDropzone"] button {
    background-color: #ffffff !important;
    color: #000000 !important;
    border-radius: 9999px !important;
    padding: 14px 32px !important;
    border: none !important;
    font-weight: 600 !important;
    font-size: 0 !important;
    line-height: 0 !important;
    box-shadow: 0 4px 20px rgba(255, 255, 255, 0.1) !important;
    transition: all 0.3s ease !important;
    cursor: pointer !important;
    min-height: unset !important;
    height: auto !important;
    flex-shrink: 0 !important;
}

[data-testid="stFileUploadDropzone"] button:hover {
    background-color: #f1f5f9 !important;
    transform: scale(1.03) !important;
    box-shadow: 0 6px 30px rgba(255, 255, 255, 0.2) !important;
}

/* Hide all child elements inside the browse button to prevent duplicate text overlaps */
[data-testid="stFileUploadDropzone"] button * {
    display: none !important;
}

[data-testid="stFileUploadDropzone"] button::after {
    content: "Select File" !important;
    display: block !important;
    font-size: 0.875rem !important;
    color: #000000 !important;
    font-weight: 600 !important;
    line-height: 1.4 !important;
}

/* ── ACTION BUTTONS (Simulation / Download) ── */
div[data-testid="stButton"] button,
div[data-testid="stDownloadButton"] button {
    background-color: rgba(12, 13, 18, 0.9) !important;
    color: #cbd5e1 !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 9999px !important;
    padding: 12px 24px !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
    transition: all 0.3s ease !important;
    display: block !important;
    margin: 0 auto !important;
    backdrop-filter: blur(8px) !important;
}

div[data-testid="stButton"] button:hover,
div[data-testid="stDownloadButton"] button:hover {
    background-color: #161822 !important;
    color: #ffffff !important;
    border-color: rgba(255, 255, 255, 0.25) !important;
}

/* Glassmorphism containers */
div.stAlert, div.stExpander, div[data-testid="stDataFrame"] {
    background: rgba(30, 41, 59, 0.2) !important;
    border: 1px solid rgba(255, 255, 255, 0.05) !important;
    border-radius: 12px !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15) !important;
}

/* Text Headers */
h1 {
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

/* ── INSIGHTS DASHBOARD SCORECARD GRID ── */
.insights-grid {
    display: grid !important;
    grid-template-columns: repeat(12, 1fr) !important;
    gap: 24px !important;
    max-width: 1200px !important;
    margin: 40px auto !important;
    font-family: 'Outfit', sans-serif !important;
}
.insights-card {
    background: rgba(255, 255, 255, 0.02) !important;
    border: 1px solid rgba(255, 255, 255, 0.05) !important;
    border-radius: 24px !important;
    padding: 32px !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: space-between !important;
    min-height: 220px !important;
    position: relative !important;
    overflow: hidden !important;
    transition: transform 0.3s ease, border-color 0.3s ease !important;
}
.insights-card:hover {
    transform: translateY(-2px) !important;
    border-color: rgba(255, 255, 255, 0.1) !important;
}
.insights-card.span-8 {
    grid-column: span 8 !important;
    padding: 48px !important;
}
.insights-card.span-4 {
    grid-column: span 4 !important;
}
.insights-label {
    font-size: 10px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.15em !important;
    color: #64748b !important;
    margin-bottom: 16px !important;
}
.insights-label.cyan-text {
    color: rgba(34, 211, 238, 0.8) !important;
}
.insights-value {
    font-size: 3.5rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.04em !important;
    color: #ffffff !important;
    margin-bottom: 12px !important;
    line-height: 1 !important;
}
.insights-value.large {
    font-size: 6.5rem !important;
}
.insights-unit {
    font-size: 1.5rem !important;
    color: #64748b !important;
    margin-left: 8px !important;
    font-weight: 400 !important;
}
.insights-text {
    font-size: 0.9rem !important;
    font-weight: 300 !important;
    color: #94a3b8 !important;
    line-height: 1.6 !important;
}
.insights-card.rose-glow::before {
    content: "" !important;
    position: absolute !important;
    inset: 0 !important;
    background: radial-gradient(circle at 10% 10%, rgba(244, 63, 94, 0.05), transparent 60%) !important;
    pointer-events: none !important;
}
.insights-card.cyan-glow::before {
    content: "" !important;
    position: absolute !important;
    inset: 0 !important;
    background: radial-gradient(circle at 10% 10%, rgba(34, 211, 238, 0.05), transparent 60%) !important;
    pointer-events: none !important;
}

/* ── COMPARISON SECTION ── */
.comparison-header {
    text-align: center !important;
    margin-top: 80px !important;
    margin-bottom: 40px !important;
    font-family: 'Outfit', sans-serif !important;
}
.comparison-subtitle {
    font-size: 1.1rem !important;
    color: #94a3b8 !important;
    font-weight: 300 !important;
    margin-top: 8px !important;
}
.scoreboard-grid {
    display: grid !important;
    grid-template-columns: repeat(2, 1fr) !important;
    gap: 24px !important;
    max-width: 1200px !important;
    margin: 0 auto 40px auto !important;
    font-family: 'Outfit', sans-serif !important;
}
.score-card {
    background: rgba(255, 255, 255, 0.02) !important;
    border-radius: 24px !important;
    padding: 24px 32px !important;
    display: flex !important;
    align-items: center !important;
    gap: 24px !important;
    border: 1px solid rgba(255, 255, 255, 0.05) !important;
}
.score-card.rose-score {
    background: rgba(244, 63, 94, 0.02) !important;
    border-color: rgba(244, 63, 94, 0.1) !important;
}
.score-card.cyan-score {
    background: rgba(34, 211, 238, 0.02) !important;
    border-color: rgba(34, 211, 238, 0.1) !important;
}
.score-icon {
    font-size: 2rem !important;
}
.score-value {
    font-size: 3rem !important;
    font-weight: 700 !important;
    color: #ffffff !important;
    line-height: 1 !important;
}
.score-text {
    font-size: 0.9rem !important;
    color: #94a3b8 !important;
    margin-top: 4px !important;
    font-weight: 300 !important;
}
.comparison-lists {
    display: grid !important;
    grid-template-columns: 1fr 1fr !important;
    gap: 48px !important;
    max-width: 1200px !important;
    margin: 0 auto !important;
    position: relative !important;
    font-family: 'Outfit', sans-serif !important;
}
.comparison-lists::before {
    content: "" !important;
    position: absolute !important;
    left: 50% !important;
    top: 0 !important;
    bottom: 0 !important;
    width: 1px !important;
    background: linear-gradient(to bottom, transparent, rgba(255,255,255,0.08), transparent) !important;
    transform: translateX(-50%) !important;
}
.comparison-list {
    display: flex !important;
    flex-direction: column !important;
    gap: 16px !important;
}
.list-title {
    font-size: 10px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.15em !important;
    color: #64748b !important;
    padding-bottom: 12px !important;
    border-bottom: 1px solid rgba(255,255,255,0.05) !important;
    padding-left: 16px !important;
}
.list-title.text-cyan {
    color: rgba(34, 211, 238, 0.8) !important;
}
.list-items {
    display: flex !important;
    flex-direction: column !important;
    gap: 8px !important;
}
.list-item {
    display: flex !important;
    align-items: center !important;
    gap: 20px !important;
    padding: 16px 20px !important;
    border-radius: 16px !important;
    transition: background 0.3s ease !important;
}
.list-item:hover {
    background: rgba(255,255,255,0.02) !important;
}
.discovery-engine .list-item:hover {
    background: rgba(34, 211, 238, 0.04) !important;
}
.item-index {
    font-size: 1.4rem !important;
    font-weight: 300 !important;
    color: #475569 !important;
    width: 24px !important;
    text-align: right !important;
}
.discovery-engine .item-index {
    color: #06b6d4 !important;
    font-weight: 500 !important;
}
.item-title {
    font-size: 0.95rem !important;
    font-weight: 500 !important;
    color: #cbd5e1 !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}
.discovery-engine .item-title {
    color: #ffffff !important;
}

@media (max-width: 768px) {
    .insights-grid {
        grid-template-columns: 1fr !important;
    }
    .insights-card.span-8, .insights-card.span-4 {
        grid-column: span 12 !important;
    }
    .comparison-lists {
        grid-template-columns: 1fr !important;
        gap: 32px !important;
    }
    .comparison-lists::before {
        display: none !important;
    }
    .scoreboard-grid {
        grid-template-columns: 1fr !important;
    }
}

/* Glassmorphism containers */
div.stAlert, div.stExpander, div[data-testid="stDataFrame"] {
    background: rgba(30, 41, 59, 0.2) !important;
    border: 1px solid rgba(255, 255, 255, 0.05) !important;
    border-radius: 12px !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15) !important;
}

/* Text Headers */
h1 {
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
"""), unsafe_allow_html=True)


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


# Session State Initialization
if "processing" not in st.session_state:
    st.session_state.processing = False
if "step" not in st.session_state:
    st.session_state.step = 0
if "processed" not in st.session_state:
    st.session_state.processed = False
if "raws" not in st.session_state:
    st.session_state.raws = None

STEPS = [
  "Initializing Talent Market Feed...",
  "Scanning Inefficient Assets...",
  "Pricing Experience Signals...",
  "Detecting Value Discrepancies...",
  "Isolating High-Conviction Anomalies...",
  "Acquiring Hidden Gems..."
]

# 1. Processing Screen rendering loop
if st.session_state.processing:
    current_step = st.session_state.step
    if current_step < len(STEPS):
        st.markdown(clean_html(f"""
        <style>
        /* Hide all Streamlit elements while loading */
        [data-testid="stHeader"], [data-testid="stSidebar"], .stApp {{
            background-color: #050505 !important;
        }}
        [data-testid="stVerticalBlock"] > div:not(.loading-container) {{
            display: none !important;
        }}
        .loading-container {{
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: center !important;
            height: 80vh !important;
            width: 100% !important;
            font-family: 'Outfit', sans-serif !important;
            color: #ffffff !important;
        }}
        @keyframes fadeInOut {{
            0%, 100% {{ opacity: 0.6; filter: blur(2px); }}
            50% {{ opacity: 1; filter: blur(0px); }}
        }}
        </style>
        <div class="loading-container">
            <div style="font-size: 2.2rem; font-weight: 500; text-align: center; margin-bottom: 50px; letter-spacing: -0.02em; animation: fadeInOut 1.5s infinite; background: linear-gradient(90deg, #ffffff, #94a3b8); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                {STEPS[current_step]}
            </div>
            <div style="display: flex; gap: 12px; justify-content: center;">
                {" ".join(f'<div style="width: 6px; height: 16px; border-radius: 9999px; background: {"#22d3ee" if i == current_step else ("rgba(255,255,255,0.4)" if i < current_step else "rgba(255,255,255,0.1)")}; transform: { "scaleY(1.5)" if i == current_step else "scaleY(1)" }; transition: all 0.5s ease;"></div>' for i in range(len(STEPS)))}
            </div>
        </div>
        """), unsafe_allow_html=True)
        time.sleep(0.8)
        st.session_state.step += 1
        st.rerun()
    else:
        st.session_state.processing = False
        st.session_state.processed = True
        st.rerun()

# 2. Landing Screen rendering (when not processed and not loading)
if not st.session_state.processed:
    # Fullscreen living background canvas
    st.components.v1.html(clean_html("""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
    html, body {
        margin: 0;
        padding: 0;
        width: 100%;
        height: 100%;
        overflow: hidden;
        background-color: transparent;
    }
    </style>
    </head>
    <body>
    <canvas id="living-market-bg" style="display: block; width: 100%; height: 100%; pointer-events: none;"></canvas>
    <script>
    const canvas = document.getElementById('living-market-bg');
    const ctx = canvas.getContext('2d');
    let width = canvas.width = window.innerWidth;
    let height = canvas.height = window.innerHeight;
    window.addEventListener('resize', () => {
        width = canvas.width = window.innerWidth;
        height = canvas.height = window.innerHeight;
    });
    const particles = [];
    const particleCount = 60;
    for (let i = 0; i < particleCount; i++) {
        particles.push({
            x: Math.random() * width,
            y: Math.random() * height,
            vx: (Math.random() - 0.5) * 0.5,
            vy: (Math.random() - 0.5) * 0.5,
            radius: Math.random() * 1.5 + 0.5
        });
    }
    let phase = 0;
    function animate() {
        ctx.clearRect(0, 0, width, height);
        ctx.strokeStyle = 'rgba(34, 211, 238, 0.03)';
        ctx.lineWidth = 1;
        for (let j = 0; j < 3; j++) {
            ctx.beginPath();
            for (let x = 0; x < width; x += 10) {
                const y = height * 0.5 + Math.sin(x * 0.002 + phase + j) * 80 + Math.cos(x * 0.001 - phase) * 40;
                if (x === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
            }
            ctx.stroke();
        }
        phase += 0.002;
        ctx.fillStyle = 'rgba(255, 255, 255, 0.15)';
        for (let i = 0; i < particleCount; i++) {
            const p = particles[i];
            p.x += p.vx;
            p.y += p.vy;
            if (p.x < 0 || p.x > width) p.vx *= -1;
            if (p.y < 0 || p.y > height) p.vy *= -1;
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
            ctx.fill();
            for (let j = i + 1; j < particleCount; j++) {
                const p2 = particles[j];
                const dx = p.x - p2.x;
                const dy = p.y - p2.y;
                const dist = Math.sqrt(dx*dx + dy*dy);
                if (dist < 100) {
                    ctx.strokeStyle = `rgba(34, 211, 238, ${0.08 * (1 - dist/100)})`;
                    ctx.beginPath();
                    ctx.moveTo(p.x, p.y);
                    ctx.lineTo(p2.x, p2.y);
                    ctx.stroke();
                }
            }
        }
        requestAnimationFrame(animate);
    }
    animate();
    </script>
    </body>
    </html>
    """), height=0)

    st.markdown(clean_html("""
    <div style="text-align: center; margin-top: 60px; margin-bottom: 40px; font-family: 'Outfit', sans-serif;">
        <div style="display: inline-flex; align-items: center; gap: 8px; border-radius: 9999px; background: #0A1015; border: 1px solid rgba(255,255,255,0.05); padding: 6px 16px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.15em; color: #94a3b8; margin-bottom: 30px; box-shadow: 0 0 20px rgba(34,211,238,0.05);">
            Talent Market Intelligence
        </div>
        <h1 style="font-size: 4.5rem; font-weight: 500; color: #ffffff; letter-spacing: -0.04em; line-height: 1.1; margin: 0 0 20px 0;">
            57% of Top Talent <br/>
            <span style="color: #475569;">Is Mispriced.</span>
        </h1>
        <p style="font-size: 1.25rem; color: #94a3b8; font-weight: 300; max-width: 700px; margin: 0 auto 50px auto; line-height: 1.6;">
            Traditional ATS systems reward visibility. <br/>
            <span style="color: #cbd5e1; font-weight: 400;">Discovery finds value where everyone else looks away.</span>
        </p>
    </div>
    """), unsafe_allow_html=True)

    # Render actual streamlit file uploader
    up = st.file_uploader("Upload candidates.jsonl (≤100)", type=["jsonl"], label_visibility="collapsed")
    if up is not None:
        st.session_state.raws = [json.loads(l) for l in up.read().decode("utf-8").splitlines() if l.strip()][:100]
        st.session_state.processing = True
        st.session_state.step = 0
        st.rerun()

    # Buttons layout
    c1, c2 = st.columns(2)
    with c1:
        if st.button("⚡ Or run market simulation", use_container_width=True):
            p = ROOT / "data" / "candidates.jsonl"
            if p.exists():
                st.session_state.raws = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()][:100]
                st.session_state.processing = True
                st.session_state.step = 0
                st.rerun()
    with c2:
        sample_path = ROOT / "data" / "candidates.jsonl"
        sample_data = ""
        if sample_path.exists():
            sample_data = sample_path.read_text(encoding="utf-8")
        st.download_button(
            "📋 Download sample pool",
            data=sample_data,
            file_name="candidates.jsonl",
            mime="text/plain",
            use_container_width=True
        )

    # Proof Strip at bottom
    st.markdown(clean_html("""
    <div style="border-top: 1px solid rgba(255, 255, 255, 0.05); padding-top: 40px; margin-top: 80px; font-family: 'Outfit', sans-serif;">
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 30px; max-width: 900px; margin: 0 auto; text-align: center;">
            <div>
                <div style="font-size: 2.2rem; font-weight: 700; color: #ffffff; letter-spacing: -0.04em;">100,000+</div>
                <div style="font-size: 9px; font-weight: 600; text-transform: uppercase; color: #64748b; letter-spacing: 0.1em; margin-top: 4px;">Candidates Analyzed</div>
            </div>
            <div>
                <div style="font-size: 2.2rem; font-weight: 700; color: #22d3ee; letter-spacing: -0.04em;">57</div>
                <div style="font-size: 9px; font-weight: 600; text-transform: uppercase; color: #22d3ee; letter-spacing: 0.1em; margin-top: 4px;">Hidden Gems Found</div>
            </div>
            <div>
                <div style="font-size: 2.2rem; font-weight: 700; color: #64748b; text-decoration: line-through; letter-spacing: -0.04em;">#1788</div>
                <div style="font-size: 9px; font-weight: 600; text-transform: uppercase; color: #64748b; letter-spacing: 0.1em; margin-top: 4px;">ATS Missed Rank</div>
            </div>
            <div>
                <div style="font-size: 2.2rem; font-weight: 700; color: #ffffff; letter-spacing: -0.04em;">43%</div>
                <div style="font-size: 9px; font-weight: 600; text-transform: uppercase; color: #64748b; letter-spacing: 0.1em; margin-top: 4px;">Market Inefficiency</div>
            </div>
        </div>
    </div>
    """), unsafe_allow_html=True)
    st.stop()

# 3. Load processed data
raws = st.session_state.raws
if not raws:
    st.warning("No candidates loaded. Please upload a valid JSONL file or run the market simulation.")
    st.session_state.processed = False
    st.rerun()

dashboard = rank_and_dashboard(raws, _jd_text())
cards = dashboard["cards"]
if not cards:
    st.warning("No valid candidates found in the uploaded file (all filtered out or honeypots).")
    st.session_state.processed = False
    st.rerun()

# Results page header
st.markdown(clean_html("""
<div style="background: linear-gradient(135deg, rgba(34, 211, 238, 0.05), rgba(99, 102, 241, 0.05)); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 24px; padding: 40px; text-align: center; margin-top: 10px; margin-bottom: 40px; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.25);">
    <span style="background: rgba(34, 211, 238, 0.1); border: 1px solid rgba(34, 211, 238, 0.2); color: #22d3ee; padding: 6px 14px; border-radius: 20px; font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.15em;">INDIA.RUNS Track 1 — Category Defining</span>
    <h1 style="margin: 20px 0 10px 0; font-size: 3.5rem; font-weight: 800; background: linear-gradient(90deg, #ffffff, #94a3b8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: -0.04em; font-family: 'Outfit', sans-serif;">Talent Conviction Engine</h1>
    <p style="color: #94a3b8; font-size: 1.1rem; max-width: 700px; margin: 0 auto; line-height: 1.6; font-family: 'Outfit', sans-serif;">Identify overlooked candidates, quantify conviction, and expose why traditional ATS search systems missed them.</p>
</div>
"""), unsafe_allow_html=True)

# ── Insights Grid ──
efficiency = dashboard["market_efficiency_pct"]
mispriced = dashboard["mispriced_pct"]
hidden_gems = dashboard["hidden_gems"]
avg_tmi = dashboard["avg_tmi"]
highest_tmi = dashboard["highest_tmi"]

st.markdown(clean_html(f"""
<div class="insights-grid">
    <div class="insights-card span-8 rose-glow">
        <div>
            <div class="insights-label">Systemic Inefficiency</div>
            <div class="insights-value large">{mispriced}<span class="insights-unit">%</span></div>
        </div>
        <div class="insights-text">
            Of top candidates are completely mispriced by keyword matching algorithms. The Talent Conviction Index measures the divergence between a candidate's true semantic fit and their position in a keyword-matching query.
        </div>
    </div>
    <div class="insights-card span-4 cyan-glow">
        <div>
            <div class="insights-label cyan-text">Hidden Value</div>
            <div class="insights-value">{hidden_gems}</div>
        </div>
        <div class="insights-text">
            High-conviction profiles buried deep in the applicant pool who possess the core required skills but lacked specific keywords.
        </div>
    </div>
    <div class="insights-card span-4">
        <div>
            <div class="insights-label">Average Mispricing</div>
            <div class="insights-value">+{avg_tmi}</div>
        </div>
        <div class="insights-text">
            Average positions gained by candidates under the conviction ranking vs a traditional ATS similarity index.
        </div>
    </div>
    <div class="insights-card span-4">
        <div>
            <div class="insights-label">Market Efficiency</div>
            <div class="insights-value">{efficiency}<span class="insights-unit">%</span></div>
        </div>
        <div class="insights-text">
            The overlap percentage between the ATS top-100 and the Discovery Engine top-100. A lower score reveals a higher mispricing gap.
        </div>
    </div>
    <div class="insights-card span-4">
        <div>
            <div class="insights-label">Highest Mispricing</div>
            <div class="insights-value">+{highest_tmi}</div>
        </div>
        <div class="insights-text">
            The maximum position discrepancy detected. Represents a candidate ranked in our top 10 who was ranked near the very bottom by keyword similarity.
        </div>
    </div>
</div>
"""), unsafe_allow_html=True)

# ── Exhibit A (Hero Fail Section) ──
hero = dashboard["hero"]
if hero:
    st.markdown("<h2 style='font-family: \"Outfit\"; font-weight: 700; color: #f8fafc; margin-top: 40px; margin-bottom: 20px;'>Why Traditional Hiring Fails — Exhibit A</h2>", unsafe_allow_html=True)
    
    td_lis = "".join(f'<li style="display: flex; gap: 8px; font-size: 0.85rem; color: #cbd5e1; margin-bottom: 8px; align-items: flex-start;"><span style="width: 6px; height: 6px; background: #22d3ee; border-radius: 50%; margin-top: 6px; flex-shrink: 0;"></span>{d}</li>' for d in hero["trust_drivers"])
    cn_lis = "".join(f'<li style="display: flex; gap: 8px; font-size: 0.85rem; color: #cbd5e1; margin-bottom: 8px; align-items: flex-start;"><span style="width: 6px; height: 6px; background: #fb7185; border-radius: 50%; margin-top: 6px; flex-shrink: 0;"></span>{x}</li>' for x in hero["concerns"])
    if not cn_lis:
        cn_lis = '<li style="font-size: 0.85rem; color: #64748b; font-style: italic;">No risks detected</li>'
        
    st.markdown(clean_html(f"""
    <div style="position: relative; background: #070709; border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 20px; padding: 30px; margin-bottom: 30px; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);">
        <div style="position: absolute; top: 30px; right: 30px; text-align: right;">
            <div style="font-size: 9px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.1em;">Talent Mispricing Index</div>
            <div style="font-size: 1.8rem; font-weight: 700; color: #22d3ee; margin-top: 2px;">{hero['tmi']:+d}</div>
        </div>
        
        <div style="margin-bottom: 24px;">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                <div style="font-size: 9px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.1em;">Identified Asset</div>
                <span style="font-size: 8px; font-weight: 700; color: #22d3ee; background: rgba(34, 211, 238, 0.1); border: 1px solid rgba(34, 211, 238, 0.2); padding: 2px 8px; border-radius: 10px; text-transform: uppercase; letter-spacing: 0.05em;">{hero['quadrant']}</span>
            </div>
            <h3 style="font-size: 1.6rem; font-weight: 700; color: #ffffff; margin: 0; font-family: 'Outfit';">Candidate {hero['candidate_id'].split('_')[-1]}</h3>
            <div style="font-size: 0.95rem; color: #94a3b8; margin-top: 4px;">{hero['title']}</div>
        </div>

        <div style="display: flex; gap: 30px; margin-bottom: 24px; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 20px;">
            <div>
                <div style="font-size: 9px; text-transform: uppercase; color: #64748b; font-weight: 600; letter-spacing: 0.05em;">Fit</div>
                <div style="font-size: 1.4rem; font-weight: 600; color: #ffffff;">{hero['fit']}</div>
            </div>
            <div>
                <div style="font-size: 9px; text-transform: uppercase; color: #64748b; font-weight: 600; letter-spacing: 0.05em;">Conviction</div>
                <div style="font-size: 1.4rem; font-weight: 600; color: #ffffff;">{hero['conviction']}%</div>
            </div>
            <div>
                <div style="font-size: 9px; text-transform: uppercase; color: #64748b; font-weight: 600; letter-spacing: 0.05em;">Evidence</div>
                <div style="font-size: 1.4rem; font-weight: 600; color: #ffffff;">{hero['evidence_density']}%</div>
            </div>
        </div>

        <div style="display: flex; gap: 40px; margin-bottom: 24px;">
            <div>
                <div style="font-size: 9px; text-transform: uppercase; color: #64748b; font-weight: 600; letter-spacing: 0.05em;">Prior ATS Value</div>
                <div style="font-size: 1.8rem; font-weight: 400; color: #64748b; text-decoration: line-through;">#{hero['ats_rank']}</div>
            </div>
            <div>
                <div style="font-size: 9px; text-transform: uppercase; color: #22d3ee; font-weight: 600; letter-spacing: 0.05em;">Discovery Value</div>
                <div style="font-size: 1.8rem; font-weight: 600; color: #ffffff;">#{hero['our_rank']}</div>
            </div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; min-width: 0;">
            <div>
                <div style="font-size: 10px; text-transform: uppercase; color: rgba(34, 211, 238, 0.8); font-weight: 700; margin-bottom: 12px; letter-spacing: 0.05em;">Core Signals</div>
                <ul style="list-style-type: none; padding-left: 0; margin: 0;">
                    {td_lis}
                </ul>
            </div>
            <div>
                <div style="font-size: 10px; text-transform: uppercase; color: rgba(244, 63, 94, 0.8); font-weight: 700; margin-bottom: 12px; letter-spacing: 0.05em;">Risk Vectors</div>
                <ul style="list-style-type: none; padding-left: 0; margin: 0;">
                    {cn_lis}
                </ul>
            </div>
        </div>
    </div>
    """), unsafe_allow_html=True)

# ── Hidden Gems ──
gems = [c for c in cards if c["quadrant"] == "Hidden Gem"]
if gems:
    st.markdown("<h2 style='font-family: \"Outfit\"; font-weight: 700; color: #f8fafc; margin-top: 40px; margin-bottom: 20px;'>💎 Hidden Gems — Buried by Keyword Search</h2>", unsafe_allow_html=True)
    
    # Render gems in cards
    for g in gems[:4]:
        td_lis = "".join(f'<li style="display: flex; gap: 8px; font-size: 0.85rem; color: #cbd5e1; margin-bottom: 8px; align-items: flex-start;"><span style="width: 6px; height: 6px; background: #22d3ee; border-radius: 50%; margin-top: 6px; flex-shrink: 0;"></span>{d}</li>' for d in g["trust_drivers"])
        cn_lis = "".join(f'<li style="display: flex; gap: 8px; font-size: 0.85rem; color: #94a3b8; margin-bottom: 8px; align-items: flex-start;"><span style="width: 6px; height: 6px; background: #fb7185; border-radius: 50%; margin-top: 6px; flex-shrink: 0;"></span>{x}</li>' for x in g["concerns"])
        if not cn_lis:
            cn_lis = '<li style="font-size: 0.85rem; color: #64748b; font-style: italic;">No risks detected</li>'
            
        st.markdown(clean_html(f"""
        <div style="position: relative; background: #070709; border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 20px; padding: 30px; margin-bottom: 24px; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);">
            <div style="position: absolute; top: 30px; right: 30px; text-align: right;">
                <div style="font-size: 9px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.1em;">Talent Mispricing Index</div>
                <div style="font-size: 1.8rem; font-weight: 700; color: #22d3ee; margin-top: 2px;">{g['tmi']:+d}</div>
            </div>
            
            <div style="margin-bottom: 24px;">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                    <div style="font-size: 9px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.1em;">Identified Asset</div>
                    <span style="font-size: 8px; font-weight: 700; color: #22d3ee; background: rgba(34, 211, 238, 0.1); border: 1px solid rgba(34, 211, 238, 0.2); padding: 2px 8px; border-radius: 10px; text-transform: uppercase; letter-spacing: 0.05em;">{g['quadrant']}</span>
                </div>
                <h3 style="font-size: 1.6rem; font-weight: 700; color: #ffffff; margin: 0; font-family: 'Outfit';">Candidate {g['candidate_id'].split('_')[-1]}</h3>
                <div style="font-size: 0.95rem; color: #94a3b8; margin-top: 4px;">{g['title']}</div>
            </div>

            <div style="display: flex; gap: 30px; margin-bottom: 24px; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 20px;">
                <div>
                    <div style="font-size: 9px; text-transform: uppercase; color: #64748b; font-weight: 600; letter-spacing: 0.05em;">Fit</div>
                    <div style="font-size: 1.4rem; font-weight: 600; color: #ffffff;">{g['fit']}</div>
                </div>
                <div>
                    <div style="font-size: 9px; text-transform: uppercase; color: #64748b; font-weight: 600; letter-spacing: 0.05em;">Conviction</div>
                    <div style="font-size: 1.4rem; font-weight: 600; color: #ffffff;">{g['conviction']}%</div>
                </div>
                <div>
                    <div style="font-size: 9px; text-transform: uppercase; color: #64748b; font-weight: 600; letter-spacing: 0.05em;">Evidence</div>
                    <div style="font-size: 1.4rem; font-weight: 600; color: #ffffff;">{g['evidence_density']}%</div>
                </div>
            </div>

            <div style="display: flex; gap: 40px; margin-bottom: 24px;">
                <div>
                    <div style="font-size: 9px; text-transform: uppercase; color: #64748b; font-weight: 600; letter-spacing: 0.05em;">Prior ATS Value</div>
                    <div style="font-size: 1.8rem; font-weight: 400; color: #64748b; text-decoration: line-through;">#{g['ats_rank']}</div>
                </div>
                <div>
                    <div style="font-size: 9px; text-transform: uppercase; color: #22d3ee; font-weight: 600; letter-spacing: 0.05em;">Discovery Value</div>
                    <div style="font-size: 1.8rem; font-weight: 600; color: #ffffff;">#{g['our_rank']}</div>
                </div>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; min-width: 0;">
                <div>
                    <div style="font-size: 10px; text-transform: uppercase; color: rgba(34, 211, 238, 0.8); font-weight: 700; margin-bottom: 12px; letter-spacing: 0.05em;">Core Signals</div>
                    <ul style="list-style-type: none; padding-left: 0; margin: 0;">
                        {td_lis}
                    </ul>
                </div>
                <div>
                    <div style="font-size: 10px; text-transform: uppercase; color: rgba(244, 63, 94, 0.8); font-weight: 700; margin-bottom: 12px; letter-spacing: 0.05em;">Risk Vectors</div>
                    <ul style="list-style-type: none; padding-left: 0; margin: 0;">
                        {cn_lis}
                    </ul>
                </div>
            </div>
        </div>
        """), unsafe_allow_html=True)

# ── Comparison Lists ──
ats_items = ""
for idx, title in enumerate(dashboard["ats_top10"], 1):
    ats_items += f"""
    <div class="list-item">
        <div class="item-index">#{idx}</div>
        <div class="item-title">{title}</div>
    </div>
    """
    
our_items = ""
for idx, title in enumerate(dashboard["our_top10"], 1):
    our_items += f"""
    <div class="list-item">
        <div class="item-index">#{idx}</div>
        <div class="item-title">{title}</div>
    </div>
    """
    
st.markdown(clean_html(f"""
<div class="comparison-header">
    <h2>ATS vs Discovery</h2>
    <div class="comparison-subtitle">The legacy keyword index against the Discovery engine — same pool, two different top tens.</div>
</div>

<div class="scoreboard-grid">
    <div class="score-card rose-score">
        <div class="score-icon">⚠️</div>
        <div class="score-content">
            <div class="score-value">{dashboard["stuffers_in_ats_top"]}</div>
            <div class="score-text">Keyword stuffers in the ATS top-100</div>
        </div>
    </div>
    <div class="score-card cyan-score">
        <div class="score-icon">🛡️</div>
        <div class="score-content">
            <div class="score-value">{dashboard["stuffers_in_our_top"]}</div>
            <div class="score-text">Keyword stuffers in the Discovery top</div>
        </div>
    </div>
</div>

<div class="comparison-lists">
    <div class="comparison-list legacy-ats">
        <div class="list-title">Legacy ATS · Top 10</div>
        <div class="list-items">
            {ats_items}
        </div>
    </div>
    <div class="comparison-list discovery-engine">
        <div class="list-title text-cyan">Discovery Engine · Top 10</div>
        <div class="list-items">
            {our_items}
        </div>
    </div>
</div>
"""), unsafe_allow_html=True)

# ── Altair Quadrant Chart ──
st.markdown("<h2 style='font-family: \"Outfit\"; font-weight: 700; color: #f8fafc; margin-top: 60px; margin-bottom: 20px;'>The Bet Map — Fit × Conviction</h2>", unsafe_allow_html=True)
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

# ── Interactive Asset Discovery & Audit Panel ──
st.markdown("<h2 style='font-family: \"Outfit\"; font-weight: 700; color: #f8fafc; margin-top: 60px; margin-bottom: 20px;'>Asset Discovery & Audit</h2>", unsafe_allow_html=True)
explore_col, audit_col = st.columns([7, 5])

with explore_col:
    search_q = st.text_input("🔍 Search identified assets...", "", placeholder="Type title or candidate ID...")
    
    # Filter
    filtered = cards
    if search_q:
        filtered = [c for c in cards if search_q.lower() in c["candidate_id"].lower() or search_q.lower() in c["title"].lower()]
        
    # Render a high-end styled HTML table of the top 15 matches
    table_rows = ""
    max_tmi = max(1, *[c["tmi"] for c in cards if c["tmi"] is not None])
    for c in filtered[:15]:
        display_id = c["candidate_id"].split('_')[-1]
        shift = c["ats_rank"] - c["our_rank"]
        is_gem = shift > 100
        tmi_val = c["tmi"]
        tmi_pct = max(2, min(100, int((tmi_val / max_tmi) * 100)))
        
        table_rows += f"""
        <div style="display: grid; grid-template-columns: 2fr 1fr 1fr 2fr; gap: 12px; padding: 16px 20px; border-bottom: 1px solid rgba(255,255,255,0.05); align-items: center;">
            <div style="display: flex; align-items: center; gap: 12px; min-width: 0;">
                <div style="width: 32px; height: 32px; border-radius: 50%; background: #070709; border: 1px solid rgba(255,255,255,0.1); display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: 600; color: #ffffff; flex-shrink: 0;">
                    {display_id}
                </div>
                <div style="min-width: 0;">
                    <div style="font-size: 0.9rem; font-weight: 600; color: #ffffff; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">Candidate {display_id}</div>
                    <div style="font-size: 0.75rem; color: #64748b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{c['title']}</div>
                </div>
            </div>
            <div style="text-align: right; font-size: 0.9rem; color: #64748b; text-decoration: line-through;">#{c['ats_rank']}</div>
            <div style="text-align: right; font-size: 0.9rem; color: #ffffff; font-weight: 600;">#{c['our_rank']}</div>
            <div style="padding-left: 20px;">
                <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: #cbd5e1; margin-bottom: 4px;">
                    <span>TMI</span>
                    <span>+{tmi_val}</span>
                </div>
                <div style="width: 100%; height: 4px; background: rgba(255,255,255,0.05); border-radius: 99px; overflow: hidden;">
                    <div style="width: {tmi_pct}%; height: 100%; background: { '#22d3ee' if is_gem else '#64748b' }; border-radius: 99px;"></div>
                </div>
            </div>
        </div>
        """
        
    table_html = f"""
    <div style="background: #050505; border: 1px solid rgba(255,255,255,0.1); border-radius: 20px; overflow: hidden; font-family: 'Outfit', sans-serif;">
        <div style="display: grid; grid-template-columns: 2fr 1fr 1fr 2fr; gap: 12px; padding: 12px 20px; background: #070709; border-bottom: 1px solid rgba(255,255,255,0.08); font-size: 10px; font-weight: 600; text-transform: uppercase; tracking-spacing: 0.1em; color: #64748b;">
            <div>Identified Asset</div>
            <div style="text-align: right;">Prior ATS</div>
            <div style="text-align: right; color: #22d3ee;">True Value</div>
            <div style="padding-left: 20px;">Mispricing (TMI)</div>
        </div>
        {table_rows or '<div style="padding: 30px; text-align: center; color: #64748b;">No matching assets found</div>'}
    </div>
    """
    st.markdown(clean_html(table_html), unsafe_allow_html=True)

with audit_col:
    if filtered:
        selected_cand = st.selectbox(
            "Select Asset for Full Audit",
            filtered,
            format_func=lambda c: f"Candidate {c['candidate_id'].split('_')[-1]} (True #{c['our_rank']})"
        )
        
        if selected_cand:
            audit_td = "".join(f'<li style="display: flex; gap: 10px; font-size: 0.85rem; color: #cbd5e1; margin-bottom: 12px; align-items: flex-start;"><span style="width: 6px; height: 6px; background: #22d3ee; border-radius: 50%; margin-top: 6px; flex-shrink: 0;"></span>{d}</li>' for d in selected_cand["trust_drivers"])
            audit_cn = "".join(f'<li style="display: flex; gap: 10px; font-size: 0.85rem; color: #94a3b8; margin-bottom: 12px; align-items: flex-start;"><span style="width: 6px; height: 6px; background: #fb7185; border-radius: 50%; margin-top: 6px; flex-shrink: 0;"></span>{x}</li>' for x in selected_cand["concerns"])
            if not audit_cn:
                audit_cn = '<li style="font-size: 0.85rem; color: #64748b; font-style: italic;">No risks detected</li>'
                
            audit_html = f"""
            <div style="background: rgba(7,7,9,0.85); border: 1px solid rgba(255,255,255,0.08); border-radius: 24px; padding: 24px; font-family: 'Outfit', sans-serif; box-shadow: 0 20px 40px rgba(0,0,0,0.4); backdrop-filter: blur(16px);">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 16px;">
                    <div>
                        <div style="font-size: 8px; font-weight: 700; color: #22d3ee; background: rgba(34,211,238,0.1); border: 1px solid rgba(34,211,238,0.2); padding: 2px 8px; border-radius: 10px; text-transform: uppercase; display: inline-block; margin-bottom: 6px;">{selected_cand['quadrant']}</div>
                        <h3 style="margin: 0; font-size: 1.4rem; font-weight: 700; color: #ffffff;">Candidate {selected_cand['candidate_id'].split('_')[-1]}</h3>
                        <div style="font-size: 0.85rem; color: #94a3b8; margin-top: 2px;">{selected_cand['title']}</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 8px; font-weight: 600; color: #64748b; text-transform: uppercase;">Mispricing</div>
                        <div style="font-size: 1.6rem; font-weight: 700; color: #22d3ee;">+{selected_cand['tmi']}</div>
                    </div>
                </div>
                
                <div style="margin-bottom: 20px;">
                    <div style="font-size: 9px; text-transform: uppercase; color: #22d3ee; font-weight: 600; letter-spacing: 0.05em; margin-bottom: 8px; display: flex; align-items: center; gap: 6px;">
                        <span style="width: 2px; height: 10px; background: #22d3ee; border-radius: 2px;"></span>
                        Underlying Asset Strengths
                    </div>
                    <ul style="list-style: none; padding-left: 0; margin: 0;">
                        {audit_td or '<span style="font-size: 0.85rem; color: #64748b; font-style: italic;">No extra evidence</span>'}
                    </ul>
                </div>
                
                <div style="margin-bottom: 20px;">
                    <div style="font-size: 9px; text-transform: uppercase; color: #64748b; font-weight: 600; letter-spacing: 0.05em; margin-bottom: 8px; display: flex; align-items: center; gap: 6px;">
                        <span style="width: 2px; height: 10px; background: #64748b; border-radius: 2px;"></span>
                        Pricing Rationale
                    </div>
                    <div style="font-size: 0.85rem; color: #cbd5e1; font-weight: 300; line-height: 1.5; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.03); border-radius: 14px; padding: 16px; margin: 0;">
                        {selected_cand['reasoning'] or 'No rationale available.'}
                    </div>
                </div>
                
                <div>
                    <div style="font-size: 9px; text-transform: uppercase; color: #fb7185; font-weight: 600; letter-spacing: 0.05em; margin-bottom: 8px; display: flex; align-items: center; gap: 6px;">
                        <span style="width: 2px; height: 10px; background: #fb7185; border-radius: 2px;"></span>
                        Risk Exposure
                    </div>
                    <ul style="list-style: none; padding-left: 0; margin: 0;">
                        {audit_cn}
                    </ul>
                </div>
            </div>
            """
            st.markdown(clean_html(audit_html), unsafe_allow_html=True)
    else:
        st.info("No candidates available to audit.")

# ── Download Submission ──
buf = io.StringIO(); w = csv.writer(buf); w.writerow(C.SUBMISSION_HEADER)
for c in cards[:C.TOP_K]:
    w.writerow([c["candidate_id"], c["our_rank"], f"{c['fit']/100:.4f}", c["reasoning"]])

st.markdown("<div style='margin-top: 40px;'></div>", unsafe_allow_html=True)
st.download_button("⬇ Download submission.csv", buf.getvalue(),
                   file_name="submission.csv", mime="text/csv")
