# Reproduces the SCORED ranking step (rank.py) exactly. The scored step needs only
# numpy/pandas/pyarrow — no torch, no sentence-transformers, no GPU, no network — so this
# image is tiny and builds fast. It loads the precomputed artifacts shipped in the repo
# (Git LFS) and the candidates file, and writes submission.csv.
#
#   docker build -t redrob-ranker .
#   docker run --rm -v "$PWD/data:/app/data" -v "$PWD/out:/app/out" redrob-ranker \
#       --candidates ./data/candidates.jsonl --out ./out/submission.csv
#
# (Offline precompute uses torch/sentence-transformers and is run separately; see README.)
FROM python:3.11-slim
WORKDIR /app

# Pin to the tested versions the artifacts were written with (pyarrow reads the parquet).
RUN pip install --no-cache-dir numpy==2.4.6 pandas==3.0.3 pyarrow==24.0.0

COPY . .

ENTRYPOINT ["python", "rank.py"]
CMD ["--candidates", "./data/candidates.jsonl", "--out", "./submission.csv"]
