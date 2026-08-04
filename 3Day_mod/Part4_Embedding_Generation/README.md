# Part 4: Embedding Generation (Voyage AI / OpenAI)

**Status:** Implemented.

## What it does

Reads `shared/storage/chunks.jsonl` (Part 3's output) and embeds every
chunk's `text` with whichever provider is configured in `shared/config.py`
(`EMBEDDING_PROVIDER`: `"openai"` or `"voyage"`). Switching providers is a
one-line env var change -- no code changes needed, since both providers sit
behind the same `embed_texts()` interface.

**This environment currently runs on Voyage AI** (`voyage-3`, 1024
dimensions). The `OPENAI_API_KEY` in `shared/.env` has no billing/credits
attached, so `text-embedding-3-small` calls fail with
`insufficient_quota` -- that's an OpenAI account issue, not something fixable
in code. Set `EMBEDDING_PROVIDER=openai` in `shared/.env` once billing is set
up on that account to switch back; everything else works unchanged.

## Files

| File | Purpose |
|---|---|
| `embedder.py` | Provider-agnostic embedding client (`embed_texts`, `embed_query`). Reused as-is by Part 6's retriever, so a query and the chunks it's compared against always go through the same provider/model and land in the same vector space. |
| `generate_embeddings.py` | Batch-embeds every chunk in `chunks.jsonl` and writes the output. Run directly. |
| `test_embeddings_output.py` | Sanity checks against the *saved output* (no API calls, so it's free to re-run): vector/metadata counts match the chunk count, metadata stays row-aligned with `chunks.jsonl`, all vectors are finite/non-zero/same dimension. |

## Rate-limit-aware batching

Both OpenAI and Voyage AI cap free/no-payment-method accounts hard --
Voyage in particular rejects a whole request outright above 10K tokens/min
or past 3 requests/min. A fixed "N chunks per request" batch size isn't
safe once chunk lengths vary, so `generate_embeddings.py` batches by **token
budget** instead (`MAX_TOKENS_PER_BATCH = 3000`, using the same `tiktoken`
count Part 3 already computed per chunk) and paces requests
(`SECONDS_BETWEEN_BATCHES = 21`) to stay under a 3-requests/minute cap.
`embedder.py` additionally retries transient failures with exponential
backoff (starting at 10s, since anything shorter won't clear a 3-RPM window).

## Output

- `shared/storage/embeddings.npy` -- a `(num_chunks, dimension)` float32 array.
- `shared/storage/embeddings_metadata.jsonl` -- the same chunk records as
  `chunks.jsonl`, written out again alongside the vectors so row *i* of
  `embeddings.npy` and line *i* here are always guaranteed to describe the
  same chunk, even if `chunks.jsonl` gets regenerated with a different chunk
  order later.

Current run: **147 vectors, dimension 1024** (Voyage `voyage-3`), one per
chunk from Part 3, embedded in 6 batches.

## Usage

```bash
# From 3Day_mod/, with the Part 1 venv active
python Part4_Embedding_Generation/generate_embeddings.py
```

Run the (free, no-API-call) sanity tests:

```bash
pytest Part4_Embedding_Generation/test_embeddings_output.py -v
```

## Next step

Proceed to [Part 5: FAISS and pgvector Indexing](../Part5_Vector_Indexing/README.md),
which will load `embeddings.npy` + `embeddings_metadata.jsonl` into a
searchable index.
