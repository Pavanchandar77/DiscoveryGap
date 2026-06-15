#!/usr/bin/env python3
"""rank.py — THE scored ranking step. Must run <=5 min, <=16GB, CPU-only, NO network.

Loads precomputed artifacts (see scripts/precompute.py), scores all candidates with the
gated four-bucket ensemble, takes the top 100, generates reasoning, and writes the CSV.

Reproduce command (Stage-3 will run this unmodified inside a sandbox):
  python rank.py --candidates ./candidates.jsonl --out ./submission.csv
"""
from __future__ import annotations
import argparse
import socket
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))


def _disable_network():
    """Hard guard: make any socket connection raise, proving no network use during ranking."""
    def _blocked(*a, **k):
        raise RuntimeError("network disabled during ranking step (compliance guard)")
    socket.socket.connect = _blocked  # type: ignore


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", required=True)
    ap.add_argument("--out", default="submission.csv")
    ap.add_argument("--allow-network", action="store_true",
                    help="debug only; never set for a real submission run")
    args = ap.parse_args()

    if not args.allow_network:
        _disable_network()

    from redrob_ranker.rank_pipeline import run
    t0 = time.time()
    run(args.candidates, args.out)
    dt = time.time() - t0
    print(f"ranking step completed in {dt:.1f}s (budget: 300s)")
    if dt > 300:
        print("WARNING: exceeded the 5-minute budget — optimize before submitting.", file=sys.stderr)


if __name__ == "__main__":
    main()
