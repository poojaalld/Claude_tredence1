# Semantic Caching

Hands-on module on **semantic caching** for LLM apps: caching answers by
*meaning* instead of exact text, so a reworded repeat question is served
instantly instead of triggering another Claude call.

## What semantic caching is

A normal cache only helps when the exact same string comes in twice —
useless for a chatbot, since real users rarely repeat themselves word for
word ("What is the capital of France?" vs. "Which city is France's
capital?" are the same question, but a plain string-keyed cache treats them
as unrelated).

A **semantic** cache instead:

1. Converts every question into an embedding vector (a numeric
   representation of its meaning).
2. On a new question, computes similarity (cosine similarity) between its
   embedding and every previously-answered question's embedding.
3. If the closest match is similar enough (above a threshold), returns that
   stored answer — no LLM call at all.
4. Otherwise, calls the LLM as normal and stores the new (question, answer)
   pair for future matches.

The payoff: fewer API calls, lower cost, and near-instant responses for
questions the app has effectively already answered — even when the wording
never repeats exactly.

## Contents

```
semantic caching/
├── requirements.txt   Shared dependencies for both parts below
├── .env.example        Copy to .env and add your ANTHROPIC_API_KEY
├── demo/                A working demo — run it to SEE semantic caching work
└── exercise/            An incomplete chatbot — participants build the caching themselves
```

| Folder | What it's for |
|---|---|
| [`demo/`](demo/) | Complete, runnable script. Asks Claude the same questions with and without a semantic cache in front, and prints a side-by-side comparison of Claude calls and latency. Use this to show the room the effect before they build it themselves. |
| [`exercise/`](exercise/) | An intentionally incomplete `chatbot_exercise.py` with `TODO` markers, plus step-by-step `INSTRUCTIONS.md`. Participants first get a plain (uncached) chatbot working, then add a `SemanticCache` on top and compare the before/after themselves. |

## Setup (shared by both parts)

```bash
cd "5Day/semantic caching"
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env           # paste your ANTHROPIC_API_KEY in, no quotes
```

Both parts use:
- **Claude** (`anthropic` SDK) for the actual question-answering.
- **`sentence-transformers`** (`all-MiniLM-L6-v2`), running fully locally,
  for the embeddings used to compare question meaning. No second API key
  needed — this only needs internet on its very first run, to download the
  ~80MB model from Hugging Face; every run after that is offline.

## Suggested flow for a session

1. Run `demo/demo.py` live — walk through the printed output, point out
   which questions hit the cache and why the "different country" control
   question correctly doesn't.
2. Hand participants `exercise/` and `exercise/INSTRUCTIONS.md`. Have them
   complete Part 1 (no caching) first and confirm it runs.
3. Have them complete Part 2 (`SemanticCache`) and re-run to see their own
   before/after comparison.
4. Wrap up by having a few people try different `similarity_threshold`
   values and share what broke (false hits vs. missed matches).

See each subfolder's own README/instructions for full detail.
