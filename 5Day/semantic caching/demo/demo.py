"""Semantic caching demo — run this live to show participants the effect.

Asks Claude the same handful of questions twice: once with no caching at
all, once routed through a SemanticCache. The question list deliberately
mixes exact repeats, reworded paraphrases, and one genuinely different
question (a different country's capital) so participants see both:

  - paraphrases correctly served from cache (the whole point)
  - the unrelated question correctly falling through to a real Claude call
    (so it's obvious the cache isn't just saying "yes" to everything)

Run:
    python demo.py
    python demo.py --threshold 0.75   # loosen/tighten the match threshold
"""

import argparse
import os
import time

import anthropic
from dotenv import load_dotenv

from semantic_cache import SemanticCache

load_dotenv()

MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-5")

# (question, label) — label is just for the printed output, not used by the cache.
QUESTIONS = [
    ("What is the capital of France?", "original"),
    ("How do I reset my account password?", "original"),
    ("Explain what a REST API is, in one sentence.", "original"),
    ("What is the capital of France?", "EXACT REPEAT of Q1"),
    ("Which city is the capital of France?", "PARAPHRASE of Q1"),
    ("I forgot my password - how do I change it?", "PARAPHRASE of Q2"),
    ("Can you briefly explain what a REST API is?", "PARAPHRASE of Q3"),
    ("What is the capital of Germany?", "DIFFERENT question - should NOT hit"),
]


def get_client() -> anthropic.Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("Set ANTHROPIC_API_KEY in your environment or .env file.")
    return anthropic.Anthropic(api_key=api_key)


def ask_claude(client: anthropic.Anthropic, question: str) -> str:
    response = client.messages.create(
        model=MODEL,
        max_tokens=150,
        messages=[{"role": "user", "content": question}],
    )
    return "".join(block.text for block in response.content if block.type == "text").strip()


def run_without_cache(client: anthropic.Anthropic) -> tuple[int, float]:
    print("\n" + "=" * 70)
    print("PASS 1 - WITHOUT semantic caching (every question hits Claude)")
    print("=" * 70)
    calls = 0
    start = time.perf_counter()
    for question, label in QUESTIONS:
        q_start = time.perf_counter()
        answer = ask_claude(client, question)
        q_elapsed = time.perf_counter() - q_start
        calls += 1
        print(f"\n[{label}] {question!r}")
        print(f"  -> Claude call ({q_elapsed:.2f}s): {answer[:100]}")
    elapsed = time.perf_counter() - start
    print(f"\nTotal: {calls} Claude calls, {elapsed:.2f}s")
    return calls, elapsed


def run_with_cache(client: anthropic.Anthropic, threshold: float) -> tuple[int, float]:
    print("\n" + "=" * 70)
    print(f"PASS 2 - WITH semantic caching (similarity threshold = {threshold})")
    print("=" * 70)
    cache = SemanticCache(similarity_threshold=threshold)
    calls = 0
    start = time.perf_counter()
    for question, label in QUESTIONS:
        q_start = time.perf_counter()
        hit = cache.lookup(question)
        if hit is not None:
            answer, similarity = hit
            q_elapsed = time.perf_counter() - q_start
            print(f"\n[{label}] {question!r}")
            print(f"  -> CACHE HIT (similarity={similarity:.3f}, {q_elapsed*1000:.1f}ms, $0): {answer[:100]}")
        else:
            answer = ask_claude(client, question)
            cache.store(question, answer)
            q_elapsed = time.perf_counter() - q_start
            calls += 1
            print(f"\n[{label}] {question!r}")
            print(f"  -> CACHE MISS -> Claude call ({q_elapsed:.2f}s): {answer[:100]}")
    elapsed = time.perf_counter() - start
    print(f"\nTotal: {calls} Claude calls, {elapsed:.2f}s, {len(cache)} entries cached")
    return calls, elapsed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.85,
        help="Cosine similarity above which two questions count as 'the same' (default: 0.85)",
    )
    args = parser.parse_args()

    client = get_client()

    baseline_calls, baseline_time = run_without_cache(client)
    cached_calls, cached_time = run_with_cache(client, args.threshold)

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"{'':20}{'Claude calls':>15}{'Wall time':>15}")
    print(f"{'Without cache':20}{baseline_calls:>15}{baseline_time:>14.2f}s")
    print(f"{'With cache':20}{cached_calls:>15}{cached_time:>14.2f}s")
    saved_calls = baseline_calls - cached_calls
    print(f"\n{saved_calls}/{baseline_calls} Claude calls avoided by reusing semantically")
    print("matching answers instead of re-asking the model.")


if __name__ == "__main__":
    main()
