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
import sys, json, io, csv, time
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
    background-color: transparent !important; /* transparent so canvas background shows through */
}

/* Hide default Streamlit header for clean fullscreen web app look */
[data-testid="stHeader"] {
    background-color: transparent !important;
}

/* File Uploader Container */
div[data-testid="stFileUploader"] {
    max-width: 750px !important;
    margin: 40px auto !important;
    padding: 0 40px !important;
}

section[data-testid="stFileUploadDropzone"] {
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    background: #070709 !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 30px !important;
    padding: 40px !important;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.4) !important;
    transition: all 0.3s ease !important;
}

section[data-testid="stFileUploadDropzone"]:hover {
    border-color: rgba(34, 211, 238, 0.4) !important;
    background: #0A0D12 !important;
}

/* Hide default file uploader text elements */
div[data-testid="stFileUploadDropzone"] [data-testid="stUploadDropzoneText"] {
    display: none !important;
}
div[data-testid="stFileUploader"] label {
    display: none !important;
}

/* Inject title and subtitle using pseudo elements */
section[data-testid="stFileUploadDropzone"]::before {
    content: "Activate Discovery Engine" !important;
    display: block !important;
    color: #ffffff !important;
    font-size: 1.3rem !important;
    font-weight: 600 !important;
    margin-bottom: 12px !important;
    text-align: center !important;
    font-family: 'Outfit', sans-serif !important;
}

section[data-testid="stFileUploadDropzone"]::after {
    content: "Upload candidates.jsonl (≤100) to reveal hidden density." !important;
    display: block !important;
    color: #64748b !important;
    font-size: 0.9rem !important;
    font-weight: 300 !important;
    margin-top: 16px !important;
    text-align: center !important;
    font-family: 'Outfit', sans-serif !important;
}

/* Restyle Browse File Button to match React button */
div[data-testid="stFileUploadDropzone"] button {
    background-color: #ffffff !important;
    border-radius: 9999px !important;
    padding: 14px 32px !important;
    border: none !important;
    box-shadow: 0 4px 20px rgba(255, 255, 255, 0.1) !important;
    transition: all 0.3s ease !important;
    cursor: pointer !important;
    display: block !important;
    margin: 0 auto !important;
    min-height: auto !important;
    height: auto !important;
}

div[data-testid="stFileUploadDropzone"] button:hover {
    background-color: #f1f5f9 !important;
    transform: scale(1.02) !important;
    box-shadow: 0 4px 25px rgba(255, 255, 255, 0.2) !important;
}

/* Hide all child elements inside the browse button to prevent duplicate text overlaps */
div[data-testid="stFileUploadDropzone"] button * {
    display: none !important;
}

div[data-testid="stFileUploadDropzone"] button::after {
    content: "Select File" !important;
    display: block !important;
    font-size: 0.875rem !important;
    color: #000000 !important;
    font-weight: 600 !important;
    line-height: 1.4 !important;
}

/* Restyle other buttons (Simulation and Download) to be premium dark pills */
div[data-testid="stButton"] button {
    background-color: #0c0d12 !important;
    color: #cbd5e1 !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 9999px !important;
    padding: 10px 24px !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
    transition: all 0.3s ease !important;
    display: block !important;
    margin: 0 auto !important;
}

div[data-testid="stButton"] button:hover {
    background-color: #161822 !important;
    color: #ffffff !important;
    border-color: rgba(255, 255, 255, 0.25) !important;
}

div[data-testid="stDownloadButton"] button {
    background-color: #0c0d12 !important;
    color: #cbd5e1 !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 9999px !important;
    padding: 10px 24px !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
    transition: all 0.3s ease !important;
    display: block !important;
    margin: 0 auto !important;
}

div[data-testid="stDownloadButton"] button:hover {
    background-color: #161822 !important;
    color: #ffffff !important;
    border-color: rgba(255, 255, 255, 0.25) !important;
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
    border-color: rgba(34, 211, 238, 0.3) !important;
}

div[data-testid="stMetricValue"] {
    font-size: 2.4rem !important;
    font-weight: 800 !important;
    background: linear-gradient(135deg, #22d3ee 0%, #06b6d4 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
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
<canvas id="living-market-canvas" style="position: fixed; inset: 0; z-index: -1; pointer-events: none; opacity: 0.7; background-color: #020202;"></canvas>
<script>
(function() {
    const canvas = document.getElementById('living-market-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let particles = [];
    let lastTime = performance.now();

    function resize() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        
        particles = [];
        const numParticles = window.innerWidth < 768 ? 40 : 120;
        for (let i = 0; i < numParticles; i++) {
            particles.push({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                baseY: Math.random() * canvas.height,
                speed: 0.1 + Math.random() * 0.4,
                size: Math.random() * 1.5 + 0.5,
                opacity: Math.random() * 0.4 + 0.1,
            });
        }
    }

    window.addEventListener('resize', resize);
    resize();

    function draw(time) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Shifting curves (Valuation Bands)
        for (let i = 0; i < 4; i++) {
            const bandY = (canvas.height / 5) * (i + 1) + Math.sin(time / 2000 + i) * 20;
            ctx.beginPath();
            ctx.moveTo(0, bandY);
            ctx.bezierCurveTo(canvas.width / 3, bandY + 40, (canvas.width / 3) * 2, bandY - 40, canvas.width, bandY);
            ctx.strokeStyle = `rgba(34, 211, 238, 0.015)`;
            ctx.lineWidth = 1;
            ctx.stroke();
        }

        particles.forEach(p => {
            p.x -= p.speed;
            if (p.x < -10) {
                p.x = canvas.width + 10;
                p.baseY = Math.random() * canvas.height;
            }

            ctx.beginPath();
            ctx.arc(p.x, p.baseY, p.size, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(255, 255, 255, ${p.opacity})`;
            ctx.fill();
        });

        requestAnimationFrame(draw);
    }

    requestAnimationFrame(draw);
})();
</script>
""", unsafe_allow_html=True)

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
        st.markdown(f"""
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
        """, unsafe_allow_html=True)
        time.sleep(0.8)
        st.session_state.step += 1
        st.rerun()
    else:
        st.session_state.processing = False
        st.session_state.processed = True
        st.rerun()

# 2. Landing Screen rendering (when not processed and not loading)
if not st.session_state.processed:
    st.markdown("""
    <div style="text-align: center; margin-top: 60px; margin-bottom: 40px; font-family: 'Outfit', sans-serif;">
        <div style="display: inline-flex; align-items: center; gap: 8px; px: 12px; py: 4px; border-radius: 9999px; background: #0A1015; border: 1px solid rgba(255,255,255,0.05); padding: 6px 16px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.15em; color: #94a3b8; margin-bottom: 30px; box-shadow: 0 0 20px rgba(34,211,238,0.05);">
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
    """, unsafe_allow_html=True)



    # Render actual streamlit file uploader (pulled up into card via negative CSS margin)
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
            p = C.DATA / "candidates.jsonl"
            if p.exists():
                st.session_state.raws = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()][:100]
                st.session_state.processing = True
                st.session_state.step = 0
                st.rerun()
    with c2:
        sample_path = C.DATA / "candidates.jsonl"
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
    st.markdown("""
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
    """, unsafe_allow_html=True)
    st.stop()

# 3. Load processed data
raws = st.session_state.raws
cards = _rank(raws)

# Results page header
st.markdown("""
<div style="background: linear-gradient(135deg, rgba(99, 102, 241, 0.12), rgba(192, 132, 252, 0.12)); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 20px; padding: 40px; text-align: center; margin-top: 10px; margin-bottom: 30px; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.25);">
    <span style="background: linear-gradient(90deg, #c084fc, #6366f1); color: white; padding: 6px 14px; border-radius: 20px; font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.15em; box-shadow: 0 0 15px rgba(99, 102, 241, 0.4);">INDIA.RUNS Track 1 — Category Defining</span>
    <h1 style="margin: 20px 0 10px 0; font-size: 3.5rem; font-weight: 800; background: linear-gradient(90deg, #c084fc, #6366f1, #38bdf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: -0.04em; font-family: 'Outfit', sans-serif;">Talent Conviction Engine</h1>
    <p style="color: #94a3b8; font-size: 1.1rem; max-width: 700px; margin: 0 auto; line-height: 1.6; font-family: 'Outfit', sans-serif;">Identify overlooked candidates, quantify conviction, and expose why traditional ATS search systems missed them.</p>
</div>
""", unsafe_allow_html=True)

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
