# Deploying the sandbox to HuggingFace Spaces (free, public URL, no card)

The sandbox (`scripts/make_sandbox_app.py`) ranks an uploaded ≤100-candidate JSONL sample with
the same gated ranker as `rank.py`. It uses the **deterministic, numpy-only embedding backend**
(`config.EMBED_BACKEND="hashing"`), so the Space **boots without reaching HuggingFace for any
model** — it cannot 403 on startup. No GPU, no card, no model download.

## Steps

1. Create a new Space → **SDK: Streamlit** (CPU basic / free).

2. Put these files in the Space repo (the whole project is small; pushing it all is simplest):
   - `scripts/make_sandbox_app.py`
   - `src/redrob_ranker/` (the package)
   - `data/job_description.txt` (the app reads it; it also has a hardcoded fallback)
   - `requirements.txt` ← copy from `scripts/space_requirements.txt` (minimal; no torch)

3. Add this front matter to the Space's `README.md` so it knows the entry point:

   ```yaml
   ---
   title: Redrob Intelligent Candidate Ranker
   emoji: 🎯
   colorFrom: indigo
   colorTo: blue
   sdk: streamlit
   app_file: scripts/make_sandbox_app.py
   pinned: false
   ---
   ```

   (`app_file` pointing at `scripts/make_sandbox_app.py` keeps the repo layout intact so the
   app's `sys.path` to `src/` resolves — no restructuring needed.)

4. Push. The Space builds in ~1–2 min and serves a public URL. Paste that URL into
   `submission_metadata.yaml: sandbox_link`.

## Notes
- **Do not** add `torch` / `sentence-transformers` to the Space requirements — the demo backend
  is pure numpy. Adding them only slows the build and risks the very HF reach-out you want to avoid.
- If you want a one-click demo sample in the Space, add a small candidate JSONL **only if the
  challenge data license permits redistribution**. Otherwise users upload their own — the app
  already handles that.
- To demo with true BGE semantics instead, set `EMBED_BACKEND="bge"` in `config.py` and add
  `torch` + `sentence-transformers` to the Space requirements; the Space will then download the
  model once at boot (needs network). Not recommended for the demo — the deterministic backend
  is the robust, no-surprises choice.
