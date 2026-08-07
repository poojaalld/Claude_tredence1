"""A cache that matches questions by meaning, not exact text.

A normal cache only helps when the exact same string comes in twice. An LLM
app rarely sees that — the same underlying question shows up reworded,
reordered, or translated. SemanticCache embeds every question into a vector
and serves a stored answer whenever a new question's embedding is close
enough (cosine similarity) to one it has already answered.
"""

from dataclasses import dataclass

import numpy as np
from sentence_transformers import SentenceTransformer


@dataclass
class CacheEntry:
    question: str
    answer: str
    embedding: np.ndarray


class SemanticCache:
    def __init__(self, similarity_threshold: float = 0.85, model_name: str = "all-MiniLM-L6-v2"):
        self.similarity_threshold = similarity_threshold
        self._model = SentenceTransformer(model_name)
        self._entries: list[CacheEntry] = []

    def _embed(self, text: str) -> np.ndarray:
        return self._model.encode(text, normalize_embeddings=True)

    def lookup(self, question: str) -> tuple[str, float] | None:
        """Return (cached_answer, similarity) for the closest hit above the
        threshold, else None. Embeddings are pre-normalized, so cosine
        similarity is just a dot product."""
        if not self._entries:
            return None
        query_vec = self._embed(question)
        sims = [float(np.dot(query_vec, e.embedding)) for e in self._entries]
        best_idx = int(np.argmax(sims))
        best_sim = sims[best_idx]
        if best_sim >= self.similarity_threshold:
            return self._entries[best_idx].answer, best_sim
        return None

    def store(self, question: str, answer: str) -> None:
        self._entries.append(CacheEntry(question, answer, self._embed(question)))

    def __len__(self) -> int:
        return len(self._entries)
