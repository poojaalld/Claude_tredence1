# Part 5: FAISS and pgvector Indexing

**Status:** Implemented (both backends).

## What it does

Loads `shared/storage/embeddings.npy` + `embeddings_metadata.jsonl` (Part 4's
output) into a searchable vector index. The backend is selected by
`VECTOR_STORE` in `shared/config.py` (`"faiss"` default, or `"pgvector"`) --
switching is a one-line env var change, same as the embedding provider in
Part 4.

| File | Purpose |
|---|---|
| `faiss_index.py` | Builds a local FAISS `IndexFlatIP` index. `build_faiss_index()`, `load_faiss_index()`, `search_faiss()`. |
| `pgvector_index.py` | Creates/upserts a pgvector-backed Postgres table. `build_pgvector_index()`, `search_pgvector()`. |
| `build_index.py` | Dispatches to whichever backend `VECTOR_STORE` names. Run directly. |
| `test_faiss_index.py` | Sanity checks against the FAISS index (no API calls). |

### FAISS (default)

Vectors are L2-normalized and indexed with `IndexFlatIP`, so inner-product
search is equivalent to cosine-similarity search -- the standard setup for
text-embedding retrieval, and consistent with how pgvector's `<=>` operator
is used below (so both backends rank identically for the same query).

Output: `shared/storage/faiss.index` + `shared/storage/faiss_metadata.jsonl`
(the embeddings metadata copied alongside the index, so the pair is
self-contained and versioned together -- row *i* of the index always matches
line *i* of this file regardless of what happens to
`embeddings_metadata.jsonl` later).

### pgvector

Creates the `vector` extension and a `banking_kb_chunks` table (`chunk_id`
primary key, chunk metadata columns, `content`, and a `VECTOR(dimension)`
column) with an IVFFlat cosine-distance index, then upserts every chunk
(`ON CONFLICT (chunk_id) DO UPDATE` -- safe to re-run). Requires
`DATABASE_URL` in `shared/.env` and a Postgres server with the pgvector
extension available (e.g. the `pgvector/pgvector` Docker image).

## Verification

Both backends were run end-to-end against the real 147-chunk corpus and
produced **identical top-3 rankings** for the same test queries, confirming
the two implementations are consistent:

```
QUERY: How does the system handle authentication and OAuth?
  0.469  Security_Guidelines.docx | 2. Authentication & Entitlements Governance > 2.1 Perimeter Authentication (mTLS & OAuth 2.0 / OIDC)
  0.456  ADRs.docx | ADR-005: OAuth 2.0 / OIDC + mTLS Zero-Trust Security Gateway
  0.438  OpenAPI.docx | 2. Production OpenAPI 3.0.3 Specification (YAML)
```

- **FAISS**: `pytest test_faiss_index.py` -- all 4 checks pass (index size
  matches embeddings, an indexed vector's nearest match is itself with
  similarity > 0.99, `top_k` is respected, scores sort descending).
- **pgvector**: verified against a throwaway `pgvector/pgvector:pg16` Docker
  container (not part of this project -- started, indexed, queried, and torn
  down purely to validate the code). Confirmed: table + IVFFlat index
  created, all 147 rows upserted, `search_pgvector()` returned results
  identical to FAISS, and re-running the indexer stayed idempotent (still
  147 rows, no duplicates) via the `ON CONFLICT` upsert.

This project's actual `shared/.env` keeps `VECTOR_STORE=faiss` and no
`DATABASE_URL` -- pgvector is there as a documented, tested alternative for
anyone who wants a real Postgres-backed deployment instead of a local index
file.

## Usage

```bash
# From 3Day_mod/, with the Part 1 venv active
python Part5_Vector_Indexing/build_index.py
```

To use pgvector instead: set `VECTOR_STORE=pgvector` and `DATABASE_URL` in
`shared/.env` (pointing at a Postgres server with the `vector` extension
available), then run the same command.

Run the FAISS sanity tests:

```bash
pytest Part5_Vector_Indexing/test_faiss_index.py -v
```

## Next step

Proceed to [Part 6: Retriever](../Part6_Retriever/README.md), which wraps
whichever backend is configured behind one `retrieve(query, top_k)`
function -- embedding the query via Part 4's `embed_query()` and searching
via `search_faiss()` or `search_pgvector()` depending on `VECTOR_STORE`.
