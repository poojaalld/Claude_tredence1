"""Reference solution for chatbot_exercise.py — trainer use only.

Don't hand this to participants ahead of the exercise; it defeats the
point. Use it to check answers or to un-stick someone who's been stuck on
one step for a while.
"""

import os
import time

import anthropic
import numpy as np
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()

MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-5")

QUESTIONS = [
    ("What is the capital of France?", "original"),
    ("How many days are in a leap year?", "original"),
    ("What is the capital of France?", "EXACT REPEAT of Q1"),
    ("Which city is the capital of France?", "PARAPHRASE of Q1"),
    ("How many days does a leap year have?", "PARAPHRASE of Q2"),
    ("What is the capital of Spain?", "DIFFERENT question - should NOT hit"),
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


class SemanticCache:
    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold
        self._model = SentenceTransformer("all-MiniLM-L6-v2")
        self._entries = []  # list of (question, answer, embedding) tuples

    def store(self, question: str, answer: str) -> None:
        embedding = self._model.encode(question, normalize_embeddings=True)
        self._entries.append((question, answer, embedding))

    def lookup(self, question: str):
        if not self._entries:
            return None
        query_vec = self._model.encode(question, normalize_embeddings=True)
        best_answer, best_sim = None, -1.0
        for _, answer, embedding in self._entries:
            sim = float(np.dot(query_vec, embedding))
            if sim > best_sim:
                best_answer, best_sim = answer, sim
        if best_sim >= self.similarity_threshold:
            return best_answer, best_sim
        return None

    def __len__(self) -> int:
        return len(self._entries)


def run_without_cache(client: anthropic.Anthropic) -> tuple[int, float]:
    print("\n=== WITHOUT semantic caching ===")
    calls = 0
    start = time.perf_counter()
    for question, label in QUESTIONS:
        answer = ask_claude(client, question)
        calls += 1
        print(f"\n[{label}] {question!r}\n  -> {answer[:100]}")
    elapsed = time.perf_counter() - start
    print(f"\nTotal: {calls} Claude calls, {elapsed:.2f}s")
    return calls, elapsed


def run_with_cache(client: anthropic.Anthropic) -> tuple[int, float]:
    cache = SemanticCache(similarity_threshold=0.85)
    print("\n=== WITH semantic caching ===")
    calls = 0
    start = time.perf_counter()
    for question, label in QUESTIONS:
        hit = cache.lookup(question)
        if hit is not None:
            answer, similarity = hit
            print(f"\n[{label}] {question!r}\n  -> CACHE HIT (similarity={similarity:.3f}): {answer[:100]}")
        else:
            answer = ask_claude(client, question)
            cache.store(question, answer)
            calls += 1
            print(f"\n[{label}] {question!r}\n  -> CACHE MISS -> Claude call: {answer[:100]}")
    elapsed = time.perf_counter() - start
    print(f"\nTotal: {calls} Claude calls, {elapsed:.2f}s, {len(cache)} entries cached")
    return calls, elapsed


if __name__ == "__main__":
    client = get_client()
    run_without_cache(client)
    run_with_cache(client)
