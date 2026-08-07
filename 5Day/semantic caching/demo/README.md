# Demo — Semantic Caching in Action

A runnable script that proves semantic caching works, live, in front of a
room. It asks Claude the same small set of questions twice:

1. **Without caching** — every question, including exact repeats, hits
   Claude.
2. **With caching** — questions are checked against a `SemanticCache`
   first; a semantically close match is served instantly with **zero**
   Claude calls.

## Files

| File | Purpose |
|---|---|
| `semantic_cache.py` | The reusable `SemanticCache` class — embeds questions with a local sentence-transformer model and matches by cosine similarity |
| `demo.py` | Runs both passes back-to-back and prints a comparison |

## What the question set is designed to show

`demo.py` asks eight questions: three originals, an **exact repeat**, three
**paraphrases** worded completely differently from the original, and one
**genuinely different** question (a different country's capital). That last
one is the important control — it should still be a cache miss, proving the
cache is matching on meaning within a threshold, not just saying "hit" to
everything.

## Run it

```bash
cd "5Day/semantic caching"
python -m venv .venv && source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r ../requirements.txt
cp ../.env.example ../.env   # paste your ANTHROPIC_API_KEY in
cd demo
python demo.py
```

First run downloads the local embedding model (`all-MiniLM-L6-v2`, ~80MB)
from Hugging Face — needs internet once, then runs fully offline for
embeddings on every run after.

Optional: tighten or loosen the match threshold to show the boundary live:

```bash
python demo.py --threshold 0.95   # stricter — some paraphrases may now miss
python demo.py --threshold 0.60   # looser — risk of false hits
```

## What to point out live

- **Latency**: cache hits print in single-digit milliseconds vs. seconds for
  a real Claude call.
- **Call count**: the summary table shows exactly how many of the 8 Claude
  calls were avoided.
- **The paraphrases still hit.** None of them share more than a couple of
  words with the original — the match is on *meaning*, computed from the
  embedding vectors, not string overlap.
- **The Germany question still misses.** This is what makes it a cache and
  not a guesser — a plausible-but-different question is correctly routed to
  a real Claude call instead of returning France's capital.

## How it works

`SemanticCache` (in `semantic_cache.py`) stores every answered question as
an embedding vector alongside its answer. On a new question it:

1. Embeds the new question with the same model (`SentenceTransformer`,
   local, no API call).
2. Computes cosine similarity against every stored embedding.
3. If the best match is above `similarity_threshold` (default `0.85`),
   returns that cached answer instead of calling Claude.
4. Otherwise, calls Claude, then stores the new (question, answer) pair for
   future lookups.

This is intentionally a linear scan over an in-memory list — the point is to
teach the *concept* clearly. A production semantic cache (e.g. GPTCache,
Redis with a vector index) swaps the storage/search step for an ANN index,
but the matching logic is the same idea shown here.
