# Banking Knowledge Base RAG Assistant

A Retrieval-Augmented Generation (RAG) assistant that answers questions from an
internal banking knowledge base using Claude. The knowledge base (`Data/`)
contains 17 real-world software project artifacts for a fictional
"Enterprise Digital Banking Platform": BRD, SRS, HLD, LLD, ADRs, API specs
(OpenAPI/gRPC), database schema, security guidelines, coding standards,
deployment guide, test plan, release notes, production logs, and an incident
report.

The project is built incrementally, one part at a time. Each part lives in
its own folder with its own `README.md` and is runnable on its own once its
prerequisites (earlier parts) are complete.

## Architecture

```
Data/  ──▶  Part2 (Loader)  ──▶  Part3 (Semantic Chunking)  ──▶  Part4 (Embeddings)
                                                                        │
                                                                        ▼
Part9 (Streamlit UI)  ◀──  Part8 (FastAPI)  ◀──  Part7 (Claude RAG)  ◀──  Part6 (Retriever)  ◀── Part5 (FAISS / pgvector Index)

Part10: Docker, deployment & testing wraps everything above.
```

## Parts

| Part | Folder | Description | Status |
|------|--------|-------------|--------|
| 1 | [Part1_Environment_Setup](Part1_Environment_Setup) | Environment setup and project skeleton | ✅ Done |
| 2 | [Part2_Document_Loader](Part2_Document_Loader) | Loads `.docx` files from `Data/` into normalized documents | ✅ Done |
| 3 | [Part3_Semantic_Chunking](Part3_Semantic_Chunking) | Splits documents into semantically coherent chunks | ✅ Done |
| 4 | [Part4_Embedding_Generation](Part4_Embedding_Generation) | Generates embeddings via Voyage AI / OpenAI | ✅ Done |
| 5 | [Part5_Vector_Indexing](Part5_Vector_Indexing) | Indexes embeddings with FAISS and/or pgvector | ✅ Done |
| 6 | [Part6_Retriever](Part6_Retriever) | Retriever implementation (similarity search + reranking) | ✅ Done |
| 7 | [Part7_Claude_RAG_Pipeline](Part7_Claude_RAG_Pipeline) | Claude-based RAG answer generation pipeline | ✅ Done |
| 8 | [Part8_FastAPI_Backend](Part8_FastAPI_Backend) | FastAPI backend exposing the RAG pipeline | ✅ Done |
| 9 | [Part9_Streamlit_Frontend](Part9_Streamlit_Frontend) | Streamlit chat UI for end users | ✅ Done |
| 10 | [Part10_Docker_Deployment](Part10_Docker_Deployment) | Docker, deployment, and end-to-end testing | ✅ Done |

## Shared resources

- `Data/` — the internal banking knowledge base (source `.docx` files). Read-only input for Part 2.
- `shared/config.py` — single configuration module imported by every part (paths, model names, chunking/index parameters, API keys).
- `shared/.env.example` — template for the environment variables every part needs. Copy to `shared/.env` and fill in real keys.
- `shared/storage/` — generated artifacts (parsed docs, chunks, embeddings, FAISS index files) produced by later parts. Gitignored.
- `shared/logs/` — application logs. Gitignored.

**All 10 parts are complete.** Start with [Part1_Environment_Setup/README.md](Part1_Environment_Setup/README.md) to set up the environment, then work through [Part2_Document_Loader](Part2_Document_Loader/README.md) through [Part9_Streamlit_Frontend](Part9_Streamlit_Frontend/README.md) in order, or jump straight to [Part10_Docker_Deployment/README.md](Part10_Docker_Deployment/README.md) to run the whole stack with a single `docker compose up`.

## Quick start (run everything)

```bash
# 1. Set up credentials once (see Part1_Environment_Setup/README.md)
cp shared/.env.example shared/.env   # fill in ANTHROPIC_API_KEY + an embedding provider key

# 2. Bring up the full stack (ingests Data/ -> chunks -> embeds -> indexes -> serves)
docker compose -f Part10_Docker_Deployment/docker-compose.yml up
```

Then open `http://localhost:8501` for the chat UI, or `http://localhost:8000/docs`
for the API directly.
