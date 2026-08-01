# Enterprise Banking RAG Assistant

A Retrieval-Augmented Generation assistant that answers questions from an
internal banking knowledge base, using Claude (Anthropic Messages API) for
generation and Voyage AI / OpenAI embeddings for retrieval.

## Status

Built incrementally, part by part:

| Part | Deliverable | Status |
|---|---|---|
| 1 | Environment setup & project skeleton | Done |
| 2 | Document loader | Pending |
| 3 | Semantic chunking | Pending |
| 4 | Embedding generation (Voyage AI / OpenAI) | Pending |
| 5 | FAISS & pgvector indexing | Pending |
| 6 | Retriever implementation | Pending |
| 7 | Claude RAG pipeline | Pending |
| 8 | FastAPI backend | Pending |
| 9 | Streamlit frontend | Pending |
| 10 | Docker, deployment & testing | Pending |

## Project layout

```
Project-through-claude/
├── config.py           # Central settings (loaded from .env)
├── ingest.py            # Document ingestion + embeddings (Parts 2-4)
├── retriever.py          # Similarity search retriever (Part 6)
├── rag_pipeline.py       # Retrieval + prompt augmentation + Claude call (Part 7)
├── app.py               # FastAPI backend (Part 8)
├── streamlit_app.py      # Streamlit frontend (Part 9), added in Part 9
├── data/
│   └── raw/              # Sample enterprise banking documents
├── vectorstore/
│   └── faiss_index/       # Local FAISS index files
├── logs/
├── tests/
├── requirements.txt
├── .env.example
└── .env                 # Real secrets, not committed
```

## Setup

1. Create/activate a virtual environment (or reuse the repo's `.venv`):

   ```bash
   python -m venv .venv
   .venv\Scripts\activate      # Windows
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables. Copy `.env.example` to `.env` and fill
   in your keys (an `.env` with working keys is already present in this
   folder for the workshop):

   ```
   ANTHROPIC_API_KEY=...
   VOYAGE_API_KEY=...
   OPENAI_API_KEY=...
   EMBEDDING_PROVIDER=voyage      # or "openai"
   VECTOR_STORE=faiss             # or "pgvector"
   ```

4. Verify configuration loads correctly:

   ```bash
   python -c "from config import settings; print(settings.model_dump())"
   ```

## Configuration reference

All settings live in [config.py](config.py) and are backed by `.env`:

- `EMBEDDING_PROVIDER`: `voyage` (preferred) or `openai`.
- `VECTOR_STORE`: `faiss` (local dev) or `pgvector` (production).
- `CHUNK_SIZE` / `CHUNK_OVERLAP`: control semantic chunking (Part 3).
- `TOP_K`: number of chunks retrieved per query (Part 6).
- `CLAUDE_MODEL`: Claude model used for generation (Part 7).

## Next steps

Part 2 will implement the document loader in `ingest.py`, reading raw
banking knowledge-base documents from `data/raw/`.
