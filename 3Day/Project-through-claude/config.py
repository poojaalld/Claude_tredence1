"""Central configuration for the Banking RAG Assistant.

Loads settings from `.env` and exposes them as a single `settings` object
used by every other module (ingest, retriever, rag_pipeline, app).
"""

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
VECTORSTORE_DIR = BASE_DIR / "vectorstore"
FAISS_INDEX_DIR = VECTORSTORE_DIR / "faiss_index"
LOGS_DIR = BASE_DIR / "logs"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", extra="ignore")

    # --- API keys ---
    anthropic_api_key: str = ""
    voyage_api_key: str = ""
    openai_api_key: str = ""

    # --- Embeddings ---
    embedding_provider: Literal["voyage", "openai"] = "voyage"
    voyage_embedding_model: str = "voyage-3"
    openai_embedding_model: str = "text-embedding-3-small"
    embedding_dim: int = 1024

    # --- Vector store ---
    vector_store: Literal["faiss", "pgvector"] = "faiss"

    # --- pgvector connection ---
    pg_host: str = "localhost"
    pg_port: int = 5432
    pg_db: str = "banking_rag"
    pg_user: str = "postgres"
    pg_password: str = ""

    # --- Chunking ---
    chunk_size: int = 800
    chunk_overlap: int = 120

    # --- Retrieval ---
    top_k: int = 5

    # --- Claude generation ---
    claude_model: str = "claude-opus-5"
    claude_max_tokens: int = 1024
    claude_temperature: float = 0.2


settings = Settings()

for _dir in (DATA_DIR, RAW_DATA_DIR, VECTORSTORE_DIR, FAISS_INDEX_DIR, LOGS_DIR):
    _dir.mkdir(parents=True, exist_ok=True)
