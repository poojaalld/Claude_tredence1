"""
Provider-agnostic embedding client for the Banking KB RAG Assistant.

Wraps the OpenAI and Voyage AI embedding APIs behind a single interface,
selected by EMBEDDING_PROVIDER in shared/config.py. Part 4's
generate_embeddings.py uses this to embed chunks in bulk; Part 6's retriever
will reuse embed_query() to embed a user's question at request time -- both
must go through the same provider/model so query and chunk vectors live in
the same space.
"""
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent  # .../3Day_mod
sys.path.insert(0, str(PROJECT_ROOT))

from shared import config

MAX_RETRIES = 5
INITIAL_BACKOFF_SECONDS = 10  # long enough to clear a 3-requests-per-minute rate limit


def _retry(fn, *args, **kwargs):
    """Retry a flaky embedding API call with exponential backoff -- covers
    transient rate-limit / network errors from either provider's SDK."""
    last_exc: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001 -- re-raised once retries are exhausted
            last_exc = exc
            wait = INITIAL_BACKOFF_SECONDS * (2**attempt)
            print(f"    embedding call failed ({exc!r}); retrying in {wait}s "
                  f"[{attempt + 1}/{MAX_RETRIES}]")
            time.sleep(wait)
    raise last_exc


def _embed_openai(texts: list[str]) -> list[list[float]]:
    from openai import OpenAI

    client = OpenAI(api_key=config.OPENAI_API_KEY)
    response = _retry(client.embeddings.create, model=config.OPENAI_EMBEDDING_MODEL, input=texts)
    return [item.embedding for item in response.data]


def _embed_voyage(texts: list[str], input_type: str) -> list[list[float]]:
    import voyageai

    client = voyageai.Client(api_key=config.VOYAGE_API_KEY)
    response = _retry(
        client.embed, texts=texts, model=config.VOYAGE_EMBEDDING_MODEL, input_type=input_type
    )
    return response.embeddings


def embed_texts(texts: list[str], input_type: str = "document") -> list[list[float]]:
    """Embed a batch of texts with the configured provider.

    input_type: "document" for chunks being indexed, "query" for a user's
    search query. Voyage AI uses asymmetric embeddings and distinguishes the
    two; OpenAI ignores this and embeds both the same way.
    """
    if not texts:
        return []
    config.require_embedding_key()
    if config.EMBEDDING_PROVIDER == "openai":
        return _embed_openai(texts)
    if config.EMBEDDING_PROVIDER == "voyage":
        return _embed_voyage(texts, input_type)
    raise ValueError(f"Unknown EMBEDDING_PROVIDER: {config.EMBEDDING_PROVIDER!r}")


def embed_query(query: str) -> list[float]:
    return embed_texts([query], input_type="query")[0]


def current_model_name() -> str:
    if config.EMBEDDING_PROVIDER == "openai":
        return config.OPENAI_EMBEDDING_MODEL
    if config.EMBEDDING_PROVIDER == "voyage":
        return config.VOYAGE_EMBEDDING_MODEL
    raise ValueError(f"Unknown EMBEDDING_PROVIDER: {config.EMBEDDING_PROVIDER!r}")
