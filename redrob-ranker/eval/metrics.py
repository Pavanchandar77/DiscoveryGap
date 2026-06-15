"""Ranking metrics + trap-specific proxies.

The official composite is 0.50*NDCG@10 + 0.30*NDCG@50 + 0.15*MAP + 0.05*P@10.
We replicate it against our SELF-LABELED relevance (eval/build_labels.py) so we can
tune without the hidden truth. We also track the two metrics that protect us:
honeypot_rate@100 (must be 0) and stuffer_rate@10.
"""
from __future__ import annotations
import numpy as np


def dcg(rels: list[float]) -> float:
    return sum(r / np.log2(i + 2) for i, r in enumerate(rels))


def ndcg_at_k(ranked_rels: list[float], k: int) -> float:
    top = ranked_rels[:k]
    ideal = sorted(ranked_rels, reverse=True)[:k]
    idcg = dcg(ideal)
    return (dcg(top) / idcg) if idcg > 0 else 0.0


def map_score(ranked_rels: list[float], rel_threshold: float = 1.0) -> float:
    hits, precisions = 0, []
    for i, r in enumerate(ranked_rels, start=1):
        if r >= rel_threshold:
            hits += 1
            precisions.append(hits / i)
    return float(np.mean(precisions)) if precisions else 0.0


def precision_at_k(ranked_rels: list[float], k: int, rel_threshold: float = 3.0) -> float:
    top = ranked_rels[:k]
    return sum(1 for r in top if r >= rel_threshold) / k if k else 0.0


def composite(ranked_rels: list[float]) -> dict:
    return {
        "NDCG@10": ndcg_at_k(ranked_rels, 10),
        "NDCG@50": ndcg_at_k(ranked_rels, 50),
        "MAP": map_score(ranked_rels),
        "P@10": precision_at_k(ranked_rels, 10, 3.0),
        "P@5": precision_at_k(ranked_rels, 5, 3.0),
        "composite": (0.50 * ndcg_at_k(ranked_rels, 10) +
                      0.30 * ndcg_at_k(ranked_rels, 50) +
                      0.15 * map_score(ranked_rels) +
                      0.05 * precision_at_k(ranked_rels, 10, 3.0)),
    }


def trap_proxies(ranked_ids: list[str], honeypot_ids: set[str], stuffer_ids: set[str]) -> dict:
    top100 = ranked_ids[:100]
    top10 = ranked_ids[:10]
    return {
        "honeypot_rate@100": sum(1 for i in top100 if i in honeypot_ids) / max(1, len(top100)),
        "stuffer_rate@10": sum(1 for i in top10 if i in stuffer_ids) / max(1, len(top10)),
    }
