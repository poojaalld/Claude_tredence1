# Part 2: Document Loader

**Status:** Implemented.

## What it does

Loads all 17 `.docx` files from `../Data/` (BRD, SRS, HLD, LLD, ADRs, API
specs, database schema, security guidelines, coding standards, deployment
guide, test plan, release notes, production logs, incident report, vision
document) and normalizes each into a heading-based section tree.

### Why bold-detection instead of Word heading styles

Every paragraph in the knowledge base uses only the `Normal` or
`List Bullet` Word style -- none of the documents use built-in `Heading 1/2/3`
styles. So headings are instead identified by formatting: a paragraph is
treated as a heading when every run in it is bold, it isn't a bullet, and
it's short (<= 150 chars). This was verified against the full corpus: every
fully-bold `Normal` paragraph across all 17 files is at most 74 characters,
so there's no risk of misclassifying bold body prose as a heading.

Heading **level** is inferred from numbering depth: `"1. Foo"` -> level 1,
`"1.2 Bar"` -> level 2, `"1.2.3 Baz"` -> level 3. Unnumbered banner-style
headings (e.g. `"Document Control Information"`) default to level 1.

Paragraphs and tables are walked in true document order (via
`Document.iter_inner_content()`), so a table (e.g. a revision history or a
document-control metadata table) is attached as text under the heading it
actually follows, not appended at the end. Two-column tables render as
`Key: Value` lines; wider tables render as pipe-separated rows.

## Files

| File | Purpose |
|---|---|
| `document_loader.py` | Loader implementation. Run directly to parse `Data/` and write output. |
| `test_document_loader.py` | Sanity checks: every `.docx` is loaded, every document has a title/sections/text, every section has a valid level. |

## Output

`shared/storage/parsed_documents.jsonl` -- one JSON object per line:

```json
{
  "source_file": "BRD.docx",
  "doc_type": "BRD",
  "title": "BUSINESS REQUIREMENT DOCUMENT (BRD)",
  "sections": [
    {"heading": "Document Control Information", "level": 1, "text": "Document ID: INF-BRD-FIN-2026-0094\n..."},
    {"heading": "1.1 Executive Summary", "level": 2, "text": "The Enterprise Digital Banking Platform (EDBP) initiative..."}
  ],
  "full_text": "Next-Gen Enterprise Digital Banking Platform\n...\n\nDocument Control Information\n...\n\n..."
}
```

`full_text` (heading + body for every section, joined) is what Part 3 will
consume for semantic chunking; `sections` is kept so chunk metadata can cite
the specific heading a chunk came from.

## Usage

```bash
# From 3Day_mod/, with the Part 1 venv active
python Part2_Document_Loader/document_loader.py
```

Expected output: `Loaded 17 document(s) -> .../shared/storage/parsed_documents.jsonl`
plus a per-file summary (title, section count, character count).

Run the sanity tests:

```bash
pytest Part2_Document_Loader/test_document_loader.py -v
```

## Next step

Proceed to [Part 3: Semantic Chunking](../Part3_Semantic_Chunking/README.md),
which will split each document's `full_text` (and section metadata) into
semantically coherent chunks sized by `CHUNK_SIZE` / `CHUNK_OVERLAP` /
`SEMANTIC_SIMILARITY_THRESHOLD` in `shared/config.py`.
