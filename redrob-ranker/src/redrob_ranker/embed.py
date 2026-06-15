"""Embeddings.

OFFLINE (precompute.py): load a small local model and encode candidate text + the JD.
ONLINE (rank.py): NEVER loads a model — only does numpy cosine over precomputed vectors.

Keeping the heavy import inside the offline function guarantees rank.py stays light,
network-free, and within the 5-minute CPU budget.
"""
from __future__ import annotations
import numpy as np
from . import config as C


def encode_texts(texts: list[str]) -> np.ndarray:
    """OFFLINE ONLY. Returns (N, d) float32 L2-normalized embeddings."""
    from sentence_transformers import SentenceTransformer  # heavy import, offline only
    model = SentenceTransformer(C.EMBED_MODEL, device="cpu")
    vecs = model.encode(
        texts,
        batch_size=C.EMBED_BATCH,
        normalize_embeddings=True,
        show_progress_bar=True,
        convert_to_numpy=True,
    )
    return vecs.astype("float32")


def encode_one(text: str) -> np.ndarray:
    """OFFLINE ONLY. Encode a single string (used for the JD)."""
    return encode_texts([text])[0]


def cosine_to_jd(cand_vecs: np.ndarray, jd_vec: np.ndarray) -> np.ndarray:
    """ONLINE. Both inputs assumed L2-normalized => cosine = dot product. (N,) in [-1,1]."""
    return cand_vecs @ jd_vec
