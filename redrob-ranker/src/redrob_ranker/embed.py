"""Embeddings.

OFFLINE (precompute.py): encode candidate text + the JD into vectors, cached to disk.
ONLINE (rank.py): NEVER loads a model — only numpy cosine over the precomputed vectors.

Two backends, selected by config.EMBED_BACKEND:

- "hashing" (DEFAULT, fully self-contained): a deterministic numpy-only feature-hashing
  encoder over the career text. No model download, no network, byte-reproducible on any
  machine. This is what makes the submission automatic — judges (and we) never depend on
  HuggingFace being reachable.
- "bge": BAAI/bge-small-en-v1.5 via sentence-transformers. Higher semantic fidelity, but
  requires a one-time model download from HuggingFace at PRECOMPUTE time only.
- "auto": use BGE if it loads (network available), else transparently fall back to hashing.

Either way the ONLINE step is identical: rank.py loads cached vectors and does numpy dot
products. The chosen backend is baked into the cached artifacts; the judged path is the same.
"""
from __future__ import annotations
import re
import zlib
from pathlib import Path
import numpy as np
from . import config as C

_TOKEN_RE = re.compile(r"[a-z0-9+#./_-]+")

# BGE retrieval works best with an instruction on the QUERY side (the JD); passages
# (candidate text) are encoded raw. This materially improves discrimination.
BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


def pool_normalize(sem: np.ndarray) -> np.ndarray:
    """Map a pool of JD-cosines to [0,1] via robust min-max (2nd–98th pctile clip).

    Raw cosines sit in a narrow high band (e.g. BGE 0.66–0.82), so unnormalized they act
    as a near-constant offset and never discriminate. Rescaling across the pool turns the
    *relative* semantic ordering into a usable signal. The semantic term stays gated by the
    title veto / authenticity / preference multipliers, so trap-resistance is unaffected.
    """
    sem = np.asarray(sem, dtype="float64")
    if sem.size == 0:
        return sem.astype("float32")
    lo, hi = np.percentile(sem, 2), np.percentile(sem, 98)
    if hi - lo < 1e-9:
        return np.zeros_like(sem, dtype="float32")
    return np.clip((sem - lo) / (hi - lo), 0.0, 1.0).astype("float32")


def _tokens(text: str) -> list[str]:
    """Word tokens plus char trigrams (subword robustness for skills/tech terms)."""
    toks: list[str] = []
    for w in _TOKEN_RE.findall((text or "").lower()):
        toks.append("w:" + w)
        if len(w) >= 4:
            for i in range(len(w) - 2):
                toks.append("c:" + w[i:i + 3])
    return toks


def _encode_hashing(texts: list[str], dim: int) -> np.ndarray:
    """Deterministic signed feature hashing -> (N, dim) float32, L2-normalized.

    Uses zlib.crc32 (stable across processes/runs, unlike Python's salted hash) and a
    per-token sign to reduce collision bias — the standard feature-hashing trick. Cosine
    over these vectors measures shared JD/career vocabulary, which rewards exactly the
    plain-language fits the JD cares about (candidates whose narrative says "built a
    ranking/recommendation system") without any learned model.
    """
    out = np.zeros((len(texts), dim), dtype="float32")
    for r, t in enumerate(texts):
        acc: dict[int, float] = {}
        for tok in _tokens(t):
            b = tok.encode()
            idx = zlib.crc32(b) % dim
            sign = 1.0 if (zlib.crc32(b"s:" + b) & 1) else -1.0
            acc[idx] = acc.get(idx, 0.0) + sign
        if acc:
            i = np.fromiter(acc.keys(), dtype=np.int64)
            v = np.fromiter(acc.values(), dtype=np.float32)
            out[r, i] = v
            n = float(np.linalg.norm(out[r]))
            if n > 0:
                out[r] /= n
    return out


def _encode_bge(texts: list[str]) -> np.ndarray:
    # Prefer a vendored local model dir so this works fully offline (no HuggingFace reach-out).
    local = getattr(C, "EMBED_MODEL_LOCAL", None)
    if local is not None and Path(local).exists():
        import os
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
        model_ref = str(local)
        print(f"embed backend: bge (local: {local})")
    else:
        model_ref = C.EMBED_MODEL  # hub id — needs a one-time network download
    from sentence_transformers import SentenceTransformer  # heavy import, offline-only
    import torch
    device = "cuda" if torch.cuda.is_available() else "cpu"   # offline precompute only; rank.py is CPU
    print(f"embed device: {device}")
    model = SentenceTransformer(model_ref, device=device)
    vecs = model.encode(
        texts, batch_size=C.EMBED_BATCH, normalize_embeddings=True,
        show_progress_bar=True, convert_to_numpy=True,
    )
    return vecs.astype("float32")


def encode_texts(texts: list[str]) -> np.ndarray:
    """OFFLINE ONLY. Returns (N, d) float32 L2-normalized embeddings using the configured backend."""
    backend = getattr(C, "EMBED_BACKEND", "hashing")
    if backend == "bge":
        print("embed backend: bge (BAAI/bge-small-en-v1.5)")
        return _encode_bge(texts)
    if backend == "auto":
        try:
            vecs = _encode_bge(texts)
            print("embed backend: bge (auto)")
            return vecs
        except Exception as e:  # network/model unavailable -> reproducible fallback
            print(f"embed backend: hashing (auto fell back; BGE unavailable: {type(e).__name__})")
            return _encode_hashing(texts, C.EMBED_DIM)
    print(f"embed backend: hashing (dim={C.EMBED_DIM}, self-contained, no network)")
    return _encode_hashing(texts, C.EMBED_DIM)


def encode_one(text: str) -> np.ndarray:
    """OFFLINE ONLY. Encode a single string (used for the JD)."""
    return encode_texts([text])[0]


def encode_query(text: str) -> np.ndarray:
    """OFFLINE ONLY. Encode the JD as a retrieval QUERY. For BGE this prepends the
    recommended instruction prefix; for the lexical backend it is identical to encode_one."""
    backend = getattr(C, "EMBED_BACKEND", "hashing")
    if backend in ("bge", "auto"):
        return encode_texts([BGE_QUERY_PREFIX + text])[0]
    return encode_one(text)


def cosine_to_jd(cand_vecs: np.ndarray, jd_vec: np.ndarray) -> np.ndarray:
    """ONLINE. Both inputs assumed L2-normalized => cosine = dot product. (N,) in [-1,1]."""
    return cand_vecs @ jd_vec
