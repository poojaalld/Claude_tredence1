# Part 6: Retriever Implementation

**Status:** Implemented.

## What it does

`retrieve(query, top_k=None)` in `retriever.py` is the single entry point
Part 7's Claude RAG pipeline will call: it embeds the incoming query with
Part 4's `embed_query()`, searches whichever backend Part 5 built
(`search_faiss()` or `search_pgvector()`, per `VECTOR_STORE` in
`shared/config.py`), and returns the top `top_k` chunks (defaulting to
`config.TOP_K`) ranked by descending cosine similarity.

### Backend-agnostic result schema

FAISS's metadata sidecar stores chunk text under `"text"` (inherited from
Part 2-4); pgvector's table stores it under a `"content"` column (Part 5's
schema choice). `retriever.py` normalizes both to the same schema --
`chunk_id, source_file, doc_type, heading, heading_path, level,
chunk_index, token_count, text, score` -- so Part 7 never needs to know or
care which backend is active.

### FAISS index caching

The FAISS index and its metadata sidecar are loaded from disk once per
process and cached at module level (`_faiss_index` / `_faiss_metadata`).
This matters once Part 8's FastAPI server calls `retrieve()` on every
request -- without caching, a ~150-vector index would otherwise be
re-read from disk on every single query.

### `format_context()`

Also provided: `format_context(results)`, which renders retrieved chunks
into a numbered, citation-ready block (`"[1] Source: ... | Section: ..."`)
-- exactly the shape Part 7 will drop into its Claude prompt so the model
can cite sources by number.

## Files

| File | Purpose |
|---|---|
| `retriever.py` | `retrieve()`, `format_context()`. Run directly with a query string for manual inspection. |
| `test_retriever.py` | Sanity checks: `top_k` is respected (explicit and default), results carry all required fields and are sorted by score, an OAuth/mTLS query surfaces `Security_Guidelines.docx`, `format_context()` includes every result's source and text. |

## Usage

```bash
# From 3Day_mod/, with the Part 1 venv active
python Part6_Retriever/retriever.py "What multi-factor authentication and encryption standards does the platform use?"
```

Sample output (verified against the real corpus):

```
[1] score=0.502  Security_Guidelines.docx | 3. Cryptographic Standards & Key Governance
[2] score=0.499  SRS.docx | 2. System Architecture & External Interfaces > 2.2 Interface Protocols & Data Formats
[3] score=0.478  BRD.docx | 6. Regulatory, Compliance & Governance
[4] score=0.468  Security_Guidelines.docx | Next-Gen Enterprise Digital Banking Platform
[5] score=0.438  SRS.docx | 4. Non-Functional Technical Requirements (NFRs)
```

Run the sanity tests:

```bash
pytest Part6_Retriever/test_retriever.py -v
```

Note: each test calls the live embedding API, and this environment's Voyage
AI key is on the no-payment-method tier (3 requests/minute -- see
[Part 4](../Part4_Embedding_Generation/README.md)), so the 5-test suite
takes about a minute (retries pace themselves to stay under that limit).
All 5 currently pass.

## Next step

Proceed to [Part 7: Claude RAG Pipeline](../Part7_Claude_RAG_Pipeline/README.md),
which will call `retrieve()` to get grounding context, build a prompt with
`format_context()`, and generate the final answer with `CLAUDE_MODEL` from
`shared/config.py`.
