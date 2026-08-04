# Part 3: Semantic Chunking

**Status:** Implemented.

## What it does

Reads `shared/storage/parsed_documents.jsonl` (Part 2's output) and splits
each section's text into retrieval-sized chunks using two signals together,
both configurable in `shared/config.py`:

1. **A hard token ceiling** (`CHUNK_SIZE`, default 800) -- counted with
   `tiktoken`'s `cl100k_base` encoding so it matches how an LLM/embedding
   model actually counts tokens, not characters or words.
2. **A semantic-similarity boundary** (`SEMANTIC_SIMILARITY_THRESHOLD`,
   default 0.75) -- adjacent sentence-level units are TF-IDF vectorized and
   compared with cosine similarity; a chunk only breaks on a similarity drop
   once it already holds >= 30% of `CHUNK_SIZE`, so it splits at genuine
   topic shifts rather than fragmenting on every short, lexically-different
   line (e.g. table rows, short bullets).

When a chunk does break, the next chunk carries forward trailing units worth
up to `CHUNK_OVERLAP` tokens (default 100), so retrieval doesn't lose context
right at a chunk boundary.

### Why chunks never cross a heading

Chunking operates **within each section** from Part 2 and never merges two
sections together. A document's own heading structure is already a strong,
human-authored semantic signal -- collapsing it would throw that away. The
trade-off: most sections in this corpus are short (a paragraph plus a few
bullets), so most sections produce exactly one chunk well under `CHUNK_SIZE`
(observed average: ~119 tokens/chunk). Sections with large embedded
code/config/schema blocks (SQL DDL, Kubernetes manifests, Protobuf/OpenAPI
specs, JSON log samples) are the ones that actually get split into multiple
chunks -- which is exactly the content dense enough to need it.

As a hard safety net, if a single sentence-level unit alone exceeds
`CHUNK_SIZE` (e.g. one giant unbroken code block with no sentence
punctuation), it's force-split into fixed-size token windows before
chunking, so no chunk can ever exceed `CHUNK_SIZE` regardless of input.

### Heading breadcrumbs

Some sections are just numbered parent headers with no body text of their
own (e.g. `"1. Executive Summary & Business Context"`, whose content lives
entirely under child section `"1.1 Executive Summary"`). Those parents
produce no chunk, but their heading is preserved via `heading_path` -- a
breadcrumb built from the section levels, e.g.:

```
1. Executive Summary & Business Context > 1.1 Executive Summary
```

so a retrieved chunk keeps its place in the document hierarchy for citation
even though its immediate parent heading was empty.

## Files

| File | Purpose |
|---|---|
| `semantic_chunker.py` | Chunker implementation. Run directly to chunk `parsed_documents.jsonl` and write output. |
| `test_semantic_chunker.py` | Sanity checks: no chunk exceeds `CHUNK_SIZE`, chunk IDs are unique, reported token counts are accurate, every chunk traces back to a real section. |

## Output

`shared/storage/chunks.jsonl` -- one JSON object per line:

```json
{
  "chunk_id": "BRD_04_00",
  "source_file": "BRD.docx",
  "doc_type": "BRD",
  "heading": "1.1 Executive Summary",
  "heading_path": "1. Executive Summary & Business Context > 1.1 Executive Summary",
  "level": 2,
  "chunk_index": 0,
  "token_count": 113,
  "text": "The Enterprise Digital Banking Platform (EDBP) initiative aims to replace legacy..."
}
```

Running against the current `Data/` corpus produces **147 chunks** across
17 documents, averaging ~119 tokens/chunk (max observed 278, well under the
800 ceiling); 5 sections with large embedded specs/schemas/manifests split
into multiple chunks.

## Usage

```bash
# From 3Day_mod/, with the Part 1 venv active
python Part3_Semantic_Chunking/semantic_chunker.py
```

Run the sanity tests:

```bash
pytest Part3_Semantic_Chunking/test_semantic_chunker.py -v
```

## Next step

Proceed to [Part 4: Embedding Generation](../Part4_Embedding_Generation/README.md),
which will embed each chunk's `text` via OpenAI or Voyage AI
(`EMBEDDING_PROVIDER` in `shared/config.py`).
