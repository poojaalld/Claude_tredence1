"""
Central configuration for the Banking Knowledge Base RAG Assistant.

Every part of the pipeline (Part2..Part10) imports settings from this module
instead of re-reading environment variables or hardcoding paths, so the whole
project stays consistent as it grows.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# --- Paths -------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent   # .../3Day_mod
SHARED_DIR = PROJECT_ROOT / "shared"
DATA_DIR = PROJECT_ROOT / "Data"
STORAGE_DIR = SHARED_DIR / "storage"
LOGS_DIR = SHARED_DIR / "logs"

PARSED_DOCS_PATH = STORAGE_DIR / "parsed_documents.jsonl"
CHUNKS_PATH = STORAGE_DIR / "chunks.jsonl"
EMBEDDINGS_PATH = STORAGE_DIR / "embeddings.npy"
EMBEDDINGS_METADATA_PATH = STORAGE_DIR / "embeddings_metadata.jsonl"
FAISS_INDEX_PATH = STORAGE_DIR / "faiss.index"
FAISS_METADATA_PATH = STORAGE_DIR / "faiss_metadata.jsonl"

STORAGE_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Load environment variables from shared/.env
load_dotenv(SHARED_DIR / ".env")

# --- API keys ------------------------------------------------------------
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY", "")

# --- Model configuration ---------------------------------------------------
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-5")

EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "openai")  # "openai" or "voyage"
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
VOYAGE_EMBEDDING_MODEL = os.getenv("VOYAGE_EMBEDDING_MODEL", "voyage-3")

# --- Chunking configuration -------------------------------------------------
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))
SEMANTIC_SIMILARITY_THRESHOLD = float(os.getenv("SEMANTIC_SIMILARITY_THRESHOLD", "0.75"))

# --- Vector store configuration ---------------------------------------------
VECTOR_STORE = os.getenv("VECTOR_STORE", "faiss")  # "faiss" or "pgvector"
DATABASE_URL = os.getenv("DATABASE_URL", "")  # postgresql://user:pass@host:port/dbname

# --- Retriever configuration -------------------------------------------------
TOP_K = int(os.getenv("TOP_K", "5"))

# --- API / app configuration -------------------------------------------------
FASTAPI_HOST = os.getenv("FASTAPI_HOST", "0.0.0.0")
FASTAPI_PORT = int(os.getenv("FASTAPI_PORT", "8000"))
STREAMLIT_PORT = int(os.getenv("STREAMLIT_PORT", "8501"))

# Where Part 9's Streamlit frontend reaches Part 8's API. Deliberately
# separate from FASTAPI_HOST: that's the bind address ("0.0.0.0" -- not
# connectable from a client), this is the client-facing address (localhost
# for local dev; a service name like "http://backend:8000" in Docker Compose).
API_BASE_URL = os.getenv("API_BASE_URL", f"http://localhost:{FASTAPI_PORT}")


def require_embedding_key() -> None:
    """Raise a clear error if the key needed for EMBEDDING_PROVIDER is missing."""
    if EMBEDDING_PROVIDER == "openai" and not OPENAI_API_KEY:
        raise RuntimeError("EMBEDDING_PROVIDER=openai but OPENAI_API_KEY is not set in shared/.env")
    if EMBEDDING_PROVIDER == "voyage" and not VOYAGE_API_KEY:
        raise RuntimeError("EMBEDDING_PROVIDER=voyage but VOYAGE_API_KEY is not set in shared/.env")


def require_anthropic_key() -> None:
    """Raise a clear error if ANTHROPIC_API_KEY is missing (needed by Part 7)."""
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY is not set in shared/.env")
