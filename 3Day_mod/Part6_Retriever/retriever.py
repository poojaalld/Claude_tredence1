"""
Retriever for the Banking KB RAG Assistant.

Wraps Part 4's embed_query() and Part 5's index search (FAISS or pgvector,
whichever VECTOR_STORE in shared/config.py selects) behind one retrieve()
function. Part 7's Claude RAG pipeline calls this to fetch grounding context
for a user's question; both backends are normalized to the same result
schema so Part 7 doesn't need to know which one is active.

Usage:
    python retriever.py "What is the RTO for the core banking service?"
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent  # .../3Day_mod
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "Part4_Embedding_Generation"))
sys.path.insert(0, str(PROJECT_ROOT / "Part5_Vector_Indexing"))

from embedder import embed_query
from faiss_index import load_faiss_index, load_faiss_metadata, search_faiss
from pgvector_index import search_pgvector
from shared import config

# FAISS index/metadata are loaded from disk once per process and cached here
# -- retrieve() may be called many times per request (Part 8's API server),
# and reloading a ~150-vector index each time would be wasteful.
_faiss_index = None
_faiss_metadata: list[dict] | None = None


def _get_faiss_state():
    global _faiss_index, _faiss_metadata
    if _faiss_index is None:
        _faiss_index = load_faiss_index()
        _faiss_metadata = load_faiss_metadata()
    return _faiss_index, _faiss_metadata


def _retrieve_faiss(query_vector: list[float], top_k: int) -> list[dict]:
    index, metadata = _get_faiss_state()
    hits = search_faiss(index, query_vector, top_k)
    return [{**metadata[idx], "score": score} for idx, score in hits]


def _retrieve_pgvector(query_vector: list[float], top_k: int) -> list[dict]:
    rows = search_pgvector(query_vector, top_k)
    # pgvector's table stores chunk text in a "content" column (Part 5); FAISS's
    # metadata sidecar calls the same field "text" (Part 2-4). Normalize to
    # "text" here so callers never need to branch on the active backend.
    results = []
    for row in rows:
        result = {key: value for key, value in row.items() if key != "content"}
        result["text"] = row["content"]
        results.append(result)
    return results


def retrieve(query: str, top_k: int | None = None) -> list[dict]:
    """Return up to top_k chunks most relevant to `query`, ranked by
    descending similarity score. Each result has: chunk_id, source_file,
    doc_type, heading, heading_path, level, chunk_index, token_count, text,
    score (cosine similarity, higher is better) -- regardless of backend.
    """
    top_k = top_k or config.TOP_K
    query_vector = embed_query(query)

    if config.VECTOR_STORE == "faiss":
        return _retrieve_faiss(query_vector, top_k)
    if config.VECTOR_STORE == "pgvector":
        return _retrieve_pgvector(query_vector, top_k)
    raise ValueError(f"Unknown VECTOR_STORE: {config.VECTOR_STORE!r}")


def warm_up() -> None:
    """Eagerly load the FAISS index/metadata (when that's the active backend)
    so Part 8's API server fails fast at startup on a missing/corrupt index
    instead of on a user's first request, and so that first request doesn't
    pay the disk-read cost. No-op for pgvector, which has no local file to
    preload -- connection errors there surface naturally on first query."""
    if config.VECTOR_STORE == "faiss":
        _get_faiss_state()


def format_context(results: list[dict]) -> str:
    """Render retrieved chunks as a numbered, citation-friendly context
    block for Part 7's prompt construction."""
    blocks = [
        f"[{i}] Source: {r['source_file']} | Section: {r['heading_path']}\n{r['text']}"
        for i, r in enumerate(results, start=1)
    ]
    return "\n\n".join(blocks)


def main() -> None:
    query = " ".join(sys.argv[1:]) or "What is the RTO for the core banking service?"
    results = retrieve(query)

    print(f"Query: {query}\n")
    for i, r in enumerate(results, start=1):
        print(f"[{i}] score={r['score']:.3f}  {r['source_file']} | {r['heading_path']}")
        print(f"    {r['text'][:150]}...")

    print("\n--- formatted context for Claude ---\n")
    print(format_context(results))


if __name__ == "__main__":
    main()
