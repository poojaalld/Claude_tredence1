"""
Sanity checks for Part 4's saved embeddings output.

These validate the artifacts already written by generate_embeddings.py --
they do NOT call the embedding API, so running this test suite is free and
repeatable. Run generate_embeddings.py at least once first.

Usage:
    pytest test_embeddings_output.py
"""
import json
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared import config


def _require_output():
    if not config.EMBEDDINGS_PATH.exists() or not config.EMBEDDINGS_METADATA_PATH.exists():
        raise FileNotFoundError(
            "embeddings.npy / embeddings_metadata.jsonl not found -- "
            "run generate_embeddings.py first"
        )


def _load_metadata() -> list[dict]:
    with config.EMBEDDINGS_METADATA_PATH.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def test_embeddings_and_metadata_row_counts_match():
    _require_output()
    embeddings = np.load(config.EMBEDDINGS_PATH)
    metadata = _load_metadata()
    assert embeddings.shape[0] == len(metadata)


def test_embeddings_match_chunk_count():
    _require_output()
    with config.CHUNKS_PATH.open(encoding="utf-8") as f:
        chunks = [json.loads(line) for line in f if line.strip()]
    embeddings = np.load(config.EMBEDDINGS_PATH)
    assert embeddings.shape[0] == len(chunks)


def test_metadata_rows_are_aligned_with_chunk_ids():
    _require_output()
    with config.CHUNKS_PATH.open(encoding="utf-8") as f:
        chunk_ids = [json.loads(line)["chunk_id"] for line in f if line.strip()]
    metadata_ids = [row["chunk_id"] for row in _load_metadata()]
    assert metadata_ids == chunk_ids


def test_vectors_are_finite_and_non_zero():
    _require_output()
    embeddings = np.load(config.EMBEDDINGS_PATH)
    assert np.isfinite(embeddings).all()
    assert not np.any(np.all(embeddings == 0, axis=1))


def test_all_vectors_share_one_dimension():
    _require_output()
    embeddings = np.load(config.EMBEDDINGS_PATH)
    assert embeddings.ndim == 2
    assert embeddings.shape[1] > 0
