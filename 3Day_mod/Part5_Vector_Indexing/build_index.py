"""
Builds the vector index configured by VECTOR_STORE in shared/config.py
("faiss" or "pgvector") from Part 4's embeddings.

Usage:
    python build_index.py
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent  # .../3Day_mod
sys.path.insert(0, str(PROJECT_ROOT))

from faiss_index import build_faiss_index
from pgvector_index import build_pgvector_index
from shared import config


def main() -> None:
    print(f"VECTOR_STORE={config.VECTOR_STORE!r}")
    if config.VECTOR_STORE == "faiss":
        build_faiss_index()
    elif config.VECTOR_STORE == "pgvector":
        build_pgvector_index()
    else:
        raise ValueError(f"Unknown VECTOR_STORE: {config.VECTOR_STORE!r} (expected 'faiss' or 'pgvector')")


if __name__ == "__main__":
    main()
