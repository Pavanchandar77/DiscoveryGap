# Frontend ↔ Engine contract

The frontend (e.g. Google AI Studio) talks to the engine through **one HTTP API**. It never
needs to know how ranking works — it uploads a candidates file and renders the JSON it gets back.

```
Frontend  ──POST /rank (candidates.zip)──▶  Backend API (scripts/api.py)  ──▶  rank engine
Frontend  ◀─────────── dashboard JSON ───────────────────────────────────────────┘
```

## Run the API
```bash
pip install -r requirements.txt -r scripts/api_requirements.txt
uvicorn scripts.api:app --host 0.0.0.0 --port 8000     # from the repo root
```
CORS is open (`*`), so a frontend on any origin can call it.

## Endpoints
| Method | Path | Body | Returns |
|---|---|---|---|
| GET | `/health` | — | `{"status":"ok"}` |
| GET | `/demo` | — | the precomputed full-100K dashboard (if `eval/dashboard.json` exists) |
| POST | `/rank?top_k=100` | multipart `file` = `.zip` / `.jsonl` / `.jsonl.gz` | dashboard JSON ↓ |

`/rank` accepts the challenge **zip** directly (it finds `candidates.jsonl` inside) or a raw
`.jsonl`. `top_k` (1–100) sets how many ranked cards come back.

## Response shape (the dashboard JSON)
```jsonc
{
  "n_candidates": 100000,
  "market_efficiency_pct": 43,        // % of top talent the ATS also surfaced
  "mispriced_pct": 57,                // 100 - efficiency
  "hidden_gems": 56,                  // high-conviction candidates the ATS buried
  "avg_tmi": 1034,                    // average Talent Mispricing Index
  "highest_tmi": 23366,
  "hero": { /* one card — the biggest ATS failure in the top-20 */ },
  "cards": [ /* the ranked top_k, each: */
    {
      "candidate_id": "CAND_0000123",
      "title": "AI Engineer",
      "fit": 65,                      // 0-100 relevance
      "conviction": 88,               // 0-100 certainty
      "tmi": 1784,                    // ats_rank - our_rank (positions undervalued)
      "our_rank": 4,
      "ats_rank": 1788,
      "evidence_density": 86,         // % of claimed skills that are supported
      "verified_skills": 12,
      "claimed_skills": 14,
      "quadrant": "Hidden Gem",       // Hidden Gem | Obvious Fit | Promising but Uncertain | Ignore
      "trust_drivers": ["Assessment Information Retrieval 85/100", "Product-company ML experience at scale", "..."],
      "concerns": ["120-day notice", "..."],
      "reasoning": "….  (the submission CSV reasoning string)"
    }
  ],
  "ats_top10": ["Senior NLP Engineer", "..."],   // titles, for the ATS-vs-us screen
  "our_top10": ["Lead AI Engineer", "..."],
  "stuffers_in_ats_top": 9,            // keyword-stuffers the ATS pulled into its top-100
  "stuffers_in_our_top": 0
}
```

## Suggested screens (each reads only the fields above)
1. **Hero dashboard** → `market_efficiency_pct`, `mispriced_pct`, `hidden_gems`, `highest_tmi`
2. **ATS failure** → `hero` (`ats_rank` → `our_rank`, `tmi`, `trust_drivers`, `concerns`)
3. **Conviction cards** → `cards[]` (fit / conviction / tmi / evidence_density / quadrant)
4. **The bet map** → scatter `cards[]` on `fit` (x) × `conviction` (y), bubble = `tmi`, color = `quadrant`
5. **ATS vs us** → `ats_top10` vs `our_top10`, `stuffers_in_ats_top` vs `stuffers_in_our_top`

## Build the submission CSV from the response
The 4 hard-rule columns are `candidate_id, rank(=our_rank), score(=fit/100), reasoning` — all in
each card. (`rank.py` remains the canonical generator for the official submission.)
