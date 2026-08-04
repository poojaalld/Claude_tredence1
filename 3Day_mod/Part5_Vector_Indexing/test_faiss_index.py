"""
Sanity checks for the Part 5 FAISS index.

These reuse vectors already saved by Part 4 (no embedding API calls), so
running this test suite is free and repeatable. Run faiss_index.py (or
build_index.py with VECTOR_STORE=faiss) at least once first.

Usage:
    pytest test_faiss_index.py
"""
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from faiss_index import load_faiss_index, load_faiss_metadata, search_faiss
from shared import config


def test_index_size_matches_metadata_and_embeddings():
    index = load_faiss_index()
    metadata = load_faiss_metadata()
    embeddings = np.load(config.EMBEDDINGS_PATH)
    assert index.ntotal == len(metadata) == embeddings.shape[0]


def test_searching_with_an_indexed_vector_returns_itself_first():
    index = load_faiss_index()
    embeddings = np.load(config.EMBEDDINGS_PATH)

    probe_row = min(10, embeddings.shape[0] - 1)
    results = search_faiss(index, embeddings[probe_row].tolist(), top_k=1)

    assert results[0][0] == probe_row
    assert results[0][1] > 0.99  # cosine similarity to itself should be ~1.0


def test_search_respects_top_k():
    index = load_faiss_index()
    embeddings = np.load(config.EMBEDDINGS_PATH)
    results = search_faiss(index, embeddings[0].tolist(), top_k=5)
    assert len(results) == 5


def test_search_scores_are_sorted_descending():
    index = load_faiss_index()
    embeddings = np.load(config.EMBEDDINGS_PATH)
    results = search_faiss(index, embeddings[0].tolist(), top_k=10)
    scores = [score for _, score in results]
    assert scores == sorted(scores, reverse=True)
