"""
pgvector index for the Banking KB RAG Assistant.

Creates (if needed) a pgvector-enabled table in the Postgres database at
DATABASE_URL and upserts every embedding from Part 4's output, when
VECTOR_STORE=pgvector in shared/config.py. Reused by Part 6's retriever for
query-time similarity search via pgvector's <=> cosine-distance operator.

Requires the `vector` extension to be available on the target Postgres
server (e.g. the pgvector/pgvector Docker image, or `CREATE EXTENSION
vector` privileges on a managed instance).

Usage:
    python pgvector_index.py
"""
import json
import sys
from pathlib import Path

import numpy as np
from sqlalchemy import Engine, create_engine, text

PROJECT_ROOT = Path(__file__).resolve().parent.parent  # .../3Day_mod
sys.path.insert(0, str(PROJECT_ROOT))

from shared import config

TABLE_NAME = "banking_kb_chunks"


def get_engine() -> Engine:
    if not config.DATABASE_URL:
        raise RuntimeError("VECTOR_STORE=pgvector but DATABASE_URL is not set in shared/.env")
    return create_engine(config.DATABASE_URL)


def _vector_literal(vector: np.ndarray) -> str:
    """pgvector's text input format: e.g. "[0.1,0.2,0.3]"."""
    return "[" + ",".join(repr(float(x)) for x in vector) + "]"


def build_pgvector_index(
    embeddings_path: Path = config.EMBEDDINGS_PATH,
    metadata_path: Path = config.EMBEDDINGS_METADATA_PATH,
) -> None:
    if not embeddings_path.exists():
        raise FileNotFoundError(
            f"{embeddings_path} not found -- run Part 4's generate_embeddings.py first"
        )

    embeddings = np.load(embeddings_path).astype(np.float32)
    with metadata_path.open(encoding="utf-8") as f:
        metadata = [json.loads(line) for line in f if line.strip()]
    if len(metadata) != len(embeddings):
        raise ValueError("embeddings.npy and embeddings_metadata.jsonl are out of sync in row count")

    dimension = embeddings.shape[1]
    engine = get_engine()

    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.execute(
            text(
                f"""
                CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                    chunk_id TEXT PRIMARY KEY,
                    source_file TEXT NOT NULL,
                    doc_type TEXT NOT NULL,
                    heading TEXT NOT NULL,
                    heading_path TEXT NOT NULL,
                    level INTEGER NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    token_count INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    embedding VECTOR({dimension}) NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                f"""
                CREATE INDEX IF NOT EXISTS {TABLE_NAME}_embedding_idx
                ON {TABLE_NAME} USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)
                """
            )
        )

        for chunk, vector in zip(metadata, embeddings):
            conn.execute(
                text(
                    f"""
                    INSERT INTO {TABLE_NAME}
                        (chunk_id, source_file, doc_type, heading, heading_path,
                         level, chunk_index, token_count, content, embedding)
                    VALUES
                        (:chunk_id, :source_file, :doc_type, :heading, :heading_path,
                         :level, :chunk_index, :token_count, :content, CAST(:embedding AS vector))
                    ON CONFLICT (chunk_id) DO UPDATE SET
                        source_file = EXCLUDED.source_file,
                        doc_type = EXCLUDED.doc_type,
                        heading = EXCLUDED.heading,
                        heading_path = EXCLUDED.heading_path,
                        level = EXCLUDED.level,
                        chunk_index = EXCLUDED.chunk_index,
                        token_count = EXCLUDED.token_count,
                        content = EXCLUDED.content,
                        embedding = EXCLUDED.embedding
                    """
                ),
                {
                    "chunk_id": chunk["chunk_id"],
                    "source_file": chunk["source_file"],
                    "doc_type": chunk["doc_type"],
                    "heading": chunk["heading"],
                    "heading_path": chunk["heading_path"],
                    "level": chunk["level"],
                    "chunk_index": chunk["chunk_index"],
                    "token_count": chunk["token_count"],
                    "content": chunk["text"],
                    "embedding": _vector_literal(vector),
                },
            )

    host = config.DATABASE_URL.split("@")[-1]
    print(f"Upserted {len(metadata)} vectors (dimension {dimension}) into "
          f"'{TABLE_NAME}' at {host}")


def search_pgvector(query_vector: list[float], top_k: int) -> list[dict]:
    engine = get_engine()
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                f"""
                SELECT chunk_id, source_file, doc_type, heading, heading_path,
                       level, chunk_index, token_count, content,
                       1 - (embedding <=> CAST(:query_vector AS vector)) AS score
                FROM {TABLE_NAME}
                ORDER BY embedding <=> CAST(:query_vector AS vector)
                LIMIT :top_k
                """
            ),
            {"query_vector": _vector_literal(np.array(query_vector)), "top_k": top_k},
        ).mappings().all()
    return [dict(row) for row in rows]


if __name__ == "__main__":
    build_pgvector_index()
