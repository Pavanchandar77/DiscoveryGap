#!/usr/bin/env bash
# One command to ship the precomputed artifacts via Git LFS, so a fresh `git clone`
# carries them and `python rank.py ...` runs offline first-try (no re-precompute).
#
# Run AFTER generating the real full-pool artifacts:
#   REDROB_EMBED_BACKEND=bge python scripts/precompute.py --candidates <full>.jsonl --jd data/job_description.txt
#   bash scripts/ship_artifacts.sh && git push
set -euo pipefail
cd "$(dirname "$0")/.."

command -v git-lfs >/dev/null 2>&1 || { echo "git-lfs not found. Install: https://git-lfs.com"; exit 1; }
for f in artifacts/cand_vecs.npy artifacts/jd_vec.npy artifacts/cand_meta.parquet; do
  [ -f "$f" ] || { echo "missing $f — run precompute.py first"; exit 1; }
done

git lfs install
git add .gitattributes
git add -f artifacts/cand_vecs.npy artifacts/jd_vec.npy artifacts/cand_meta.parquet   # -f: past .gitignore
git commit -m "Ship precomputed BGE artifacts via Git LFS for offline rank.py reproduction"
echo "Committed. Verify with 'git lfs ls-files' then: git push"
