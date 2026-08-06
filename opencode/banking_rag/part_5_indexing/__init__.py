"""
Part 5: Vector Indexing Module
FAISS and PostgreSQL pgvector indexing for embeddings
"""

from .vector_indexing import (
    IndexMetadata,
    BaseVectorIndex,
    FAISSVectorIndex,
    PostgresVectorIndex,
    VectorIndexFactory,
    IndexManager,
)

__all__ = [
    "IndexMetadata",
    "BaseVectorIndex",
    "FAISSVectorIndex",
    "PostgresVectorIndex",
    "VectorIndexFactory",
    "IndexManager",
]
