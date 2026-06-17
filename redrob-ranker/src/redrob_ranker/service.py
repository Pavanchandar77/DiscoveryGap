"""Service layer: candidates in -> Talent Market Intelligence dashboard out.

The single source of truth that the API, the Streamlit sandbox, and the CLI all call, so the
JSON contract never drifts. Embeds the uploaded candidates inline with the configured backend
(default: deterministic hashing, no model/network), ranks them, and assembles the dashboard
payload the frontend renders.
"""
from __future__ import annotations
import numpy as np
from .schema import Candidate
from .embed import encode_texts, encode_query, cosine_to_jd, pool_normalize
from .score import score_candidate
from . import reasoning, presentation, config as C
from .normalize import canon_skills, classify_title


def _is_stuffer(c: Candidate) -> bool:
    return classify_title(c.title) == "trap" and len(set(canon_skills(c)) & set(C.JD_CORE_SKILLS)) >= 4


def rank_and_dashboard(raws: list[dict], jd_text: str, top_k: int = 100) -> dict:
    cands = [Candidate(r) for r in raws]
    sem_raw = cosine_to_jd(encode_texts([c.all_text for c in cands]), encode_query(jd_text))
    id_sem = {c.id: float(s) for c, s in zip(cands, pool_normalize(sem_raw))}
    order = sorted(range(len(cands)), key=lambda i: -sem_raw[i])     # ATS-style similarity order
    ats_rank = {cands[i].id: r for r, i in enumerate(order, 1)}

    scored = []
    for c in cands:
        s = score_candidate(c, id_sem.get(c.id, 0.0))
        if s["is_honeypot"]:
            continue
        s["rscore"] = round(s["score"], C.SCORE_DECIMALS)
        scored.append((c, s))
    scored.sort(key=lambda cs: (-cs[1]["rscore"], cs[0].id))
    top = scored[:top_k]

    cutoff = max(5, len(cands) // 3)
    cards = []
    for i, (c, s) in enumerate(top, 1):
        card = presentation.card(c, s, i, ats_rank.get(c.id), ats_cutoff=cutoff)
        card["reasoning"] = reasoning.make(c, s, i)
        cards.append(card)

    by_id = {c.id: c for c in cands}
    our_ids = [c.id for c, _ in top]
    ats_ids = [cands[i].id for i in order]
    eff = presentation.market_efficiency(our_ids, ats_ids[:len(our_ids)])
    tmis = [c["tmi"] for c in cards if c["tmi"] is not None]
    gems = [c for c in cards if c["quadrant"] == "Hidden Gem"]
    hero = max(cards[:20], key=lambda c: (c["tmi"] if c["tmi"] is not None else -1)) if cards else None

    return {
        "n_candidates": len(cands),
        "market_efficiency_pct": round(100 * eff), "mispriced_pct": round(100 * (1 - eff)),
        "hidden_gems": len(gems),
        "avg_tmi": round(float(np.mean(tmis))) if tmis else 0,
        "highest_tmi": int(max(tmis)) if tmis else 0,
        "hero": hero, "cards": cards,
        "ats_top10": [by_id[i].title for i in ats_ids[:10]],
        "our_top10": [c["title"] for c in cards[:10]],
        "stuffers_in_ats_top": sum(_is_stuffer(by_id[i]) for i in ats_ids[:len(our_ids)]),
        "stuffers_in_our_top": sum(_is_stuffer(by_id[c["candidate_id"]]) for c in cards),
    }
