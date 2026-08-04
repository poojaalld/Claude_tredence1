"""
FAISS vector index for the Banking KB RAG Assistant.

Builds a local FAISS index from shared/storage/embeddings.npy (Part 4's
output) when VECTOR_STORE=faiss in shared/config.py. Vectors are
L2-normalized and indexed with IndexFlatIP, so inner-product search is
equivalent to cosine similarity search -- the standard setup for text
embedding similarity. Reused by Part 6's retriever for query-time search.

Usage:
    python faiss_index.py
"""
import json
import sys
from pathlib import Path

import faiss
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent  # .../3Day_mod
sys.path.insert(0, str(PROJECT_ROOT))

from shared import config


def normalize(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0  # guard against a zero vector producing NaNs
    return vectors / norms


def build_faiss_index(
    embeddings_path: Path = config.EMBEDDINGS_PATH,
    metadata_path: Path = config.EMBEDDINGS_METADATA_PATH,
    index_path: Path = config.FAISS_INDEX_PATH,
    output_metadata_path: Path = config.FAISS_METADATA_PATH,
) -> faiss.Index:
    if not embeddings_path.exists():
        raise FileNotFoundError(
            f"{embeddings_path} not found -- run Part 4's generate_embeddings.py first"
        )

    embeddings = normalize(np.load(embeddings_path).astype(np.float32))

    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)

    index_path.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(index_path))

    # Metadata is copied (not just referenced) so faiss.index and its
    # metadata sidecar are a self-contained, versioned pair -- row i of the
    # index always matches line i of this file, regardless of what happens
    # to embeddings_metadata.jsonl afterwards.
    metadata_lines = metadata_path.read_text(encoding="utf-8")
    output_metadata_path.write_text(metadata_lines, encoding="utf-8")

    print(f"Built FAISS index: {index.ntotal} vectors, dimension {embeddings.shape[1]} -> {index_path}")
    print(f"Copied aligned metadata -> {output_metadata_path}")
    return index


def load_faiss_index(index_path: Path = config.FAISS_INDEX_PATH) -> faiss.Index:
    if not index_path.exists():
        raise FileNotFoundError(f"{index_path} not found -- run faiss_index.py (or build_index.py) first")
    return faiss.read_index(str(index_path))


def load_faiss_metadata(metadata_path: Path = config.FAISS_METADATA_PATH) -> list[dict]:
    with metadata_path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def search_faiss(index: faiss.Index, query_vector: list[float], top_k: int) -> list[tuple[int, float]]:
    """Return (row_index, cosine_similarity) pairs, best match first."""
    query = normalize(np.array([query_vector], dtype=np.float32))
    scores, indices = index.search(query, top_k)
    return [
        (int(idx), float(score))
        for idx, score in zip(indices[0], scores[0])
        if idx != -1  # FAISS pads with -1 if top_k > ntotal
    ]


if __name__ == "__main__":
    build_faiss_index()
