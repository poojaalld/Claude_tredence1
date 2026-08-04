"""
Batch-embeds every chunk in shared/storage/chunks.jsonl (Part 3's output)
using the provider configured in shared/config.py (EMBEDDING_PROVIDER:
"openai" or "voyage"), then writes the resulting vectors plus aligned
metadata for Part 5 to index.

Usage:
    python generate_embeddings.py
"""
import json
import sys
import time
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent  # .../3Day_mod
sys.path.insert(0, str(PROJECT_ROOT))

from embedder import current_model_name, embed_texts
from shared import config

# Batches are sized by token budget, not item count: free/no-payment-method
# tiers on embedding providers (e.g. Voyage AI's default 10K TPM / 3 RPM cap)
# reject a request outright if it's too large, so a fixed item count isn't
# safe once chunks vary in length. MAX_TOKENS_PER_BATCH stays well under that
# 10K TPM ceiling to leave margin for tokenizer differences between our
# tiktoken-based estimate and the provider's own tokenizer.
MAX_TOKENS_PER_BATCH = 3000
SECONDS_BETWEEN_BATCHES = 21  # keeps under a 3-requests-per-minute cap


def load_chunks(path: Path = config.CHUNKS_PATH) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"{path} not found -- run Part 3's semantic_chunker.py first")
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def token_budgeted_batches(chunks: list[dict], max_tokens: int):
    batch: list[dict] = []
    batch_tokens = 0
    for chunk in chunks:
        tokens = chunk["token_count"]
        if batch and batch_tokens + tokens > max_tokens:
            yield batch
            batch, batch_tokens = [], 0
        batch.append(chunk)
        batch_tokens += tokens
    if batch:
        yield batch


def embed_chunks(chunks: list[dict]) -> np.ndarray:
    batches = list(token_budgeted_batches(chunks, MAX_TOKENS_PER_BATCH))
    all_vectors: list[list[float]] = []
    for batch_num, batch in enumerate(batches, start=1):
        texts = [chunk["text"] for chunk in batch]
        vectors = embed_texts(texts, input_type="document")
        all_vectors.extend(vectors)
        batch_tokens = sum(chunk["token_count"] for chunk in batch)
        print(f"  batch {batch_num}/{len(batches)}: embedded {len(batch)} chunks "
              f"(~{batch_tokens} tokens) ({len(all_vectors)}/{len(chunks)} total)")
        if batch_num < len(batches):
            time.sleep(SECONDS_BETWEEN_BATCHES)
    return np.array(all_vectors, dtype=np.float32)


def save_embeddings(
    embeddings: np.ndarray,
    chunks: list[dict],
    embeddings_path: Path = config.EMBEDDINGS_PATH,
    metadata_path: Path = config.EMBEDDINGS_METADATA_PATH,
) -> None:
    embeddings_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(embeddings_path, embeddings)

    # Written alongside the vectors (not just reusing chunks.jsonl) so row i
    # of embeddings.npy and line i here always describe the same chunk, even
    # if chunks.jsonl is later regenerated with a different chunk order.
    with metadata_path.open("w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")


def main() -> None:
    chunks = load_chunks()
    print(f"Embedding {len(chunks)} chunks with provider={config.EMBEDDING_PROVIDER!r} "
          f"model={current_model_name()!r}")

    embeddings = embed_chunks(chunks)
    save_embeddings(embeddings, chunks)

    print(f"\nSaved {embeddings.shape[0]} vectors of dimension {embeddings.shape[1]} "
          f"-> {config.EMBEDDINGS_PATH}")
    print(f"Saved aligned metadata -> {config.EMBEDDINGS_METADATA_PATH}")


if __name__ == "__main__":
    main()
