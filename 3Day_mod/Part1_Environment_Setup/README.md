# Part 1: Environment Setup and Project Skeleton

Sets up the Python environment, shared configuration, and the full 10-part
folder skeleton for the Banking Knowledge Base RAG Assistant. Every later
part builds on the `shared/` module and dependencies installed here.

## What this part creates

```
3Day_mod/
├── Data/                          # Internal banking knowledge base (17 .docx files) -- input for Part 2
├── shared/
│   ├── config.py                  # Central settings used by every part (paths, models, chunking, index, API keys)
│   ├── .env.example               # Template -- copy to shared/.env and fill in keys
│   ├── storage/                   # Generated artifacts (parsed docs, chunks, embeddings, FAISS index) -- gitignored
│   └── logs/                      # Application logs -- gitignored
├── Part1_Environment_Setup/       # This part
│   ├── requirements.txt           # All dependencies for the entire project (Parts 1-10)
│   ├── verify_setup.py            # Checks Python version, packages, .env, and Data/ folder
│   └── README.md
├── Part2_Document_Loader/         # Skeleton -- implemented in Part 2
├── Part3_Semantic_Chunking/       # Skeleton -- implemented in Part 3
├── Part4_Embedding_Generation/    # Skeleton -- implemented in Part 4
├── Part5_Vector_Indexing/         # Skeleton -- implemented in Part 5
├── Part6_Retriever/               # Skeleton -- implemented in Part 6
├── Part7_Claude_RAG_Pipeline/     # Skeleton -- implemented in Part 7
├── Part8_FastAPI_Backend/         # Skeleton -- implemented in Part 8
├── Part9_Streamlit_Frontend/      # Skeleton -- implemented in Part 9
├── Part10_Docker_Deployment/      # Skeleton -- implemented in Part 10
├── .gitignore
└── README.md                      # Project overview
```

## Setup steps

1. **Create and activate a virtual environment** (from `3Day_mod/`):

   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

2. **Install dependencies:**

   ```bash
   pip install -r Part1_Environment_Setup/requirements.txt
   ```

3. **Configure environment variables:**

   ```bash
   cp shared/.env.example shared/.env
   ```

   Edit `shared/.env` and fill in at least:
   - `ANTHROPIC_API_KEY` -- used later by Part 7 for answer generation
   - `OPENAI_API_KEY` (if `EMBEDDING_PROVIDER=openai`) or `VOYAGE_API_KEY` (if `EMBEDDING_PROVIDER=voyage`) -- used by Part 4
   - `DATABASE_URL` -- only required if `VECTOR_STORE=pgvector` (Part 5); not needed for the FAISS default

4. **Verify the environment:**

   ```bash
   python Part1_Environment_Setup/verify_setup.py
   ```

   This checks:
   - Python version (>= 3.10)
   - All required packages are installed
   - `shared/.env` exists and has the keys required by your configured providers
   - `Data/` exists and contains the knowledge base `.docx` files
   - `shared/storage` and `shared/logs` directories are ready

## Configuration reference (`shared/config.py`)

| Setting | Default | Used by |
|---|---|---|
| `CLAUDE_MODEL` | `claude-opus-5` | Part 7 |
| `EMBEDDING_PROVIDER` | `openai` | Part 4 |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | Part 4 |
| `VOYAGE_EMBEDDING_MODEL` | `voyage-3` | Part 4 |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | `800` / `100` | Part 3 |
| `SEMANTIC_SIMILARITY_THRESHOLD` | `0.75` | Part 3 |
| `VECTOR_STORE` | `faiss` | Part 5 |
| `TOP_K` | `5` | Part 6 |
| `FASTAPI_PORT` | `8000` | Part 8 |
| `STREAMLIT_PORT` | `8501` | Part 9 |

All values are overridable via `shared/.env` without touching code.

## Next step

Once `verify_setup.py` reports the environment is ready, proceed to
[Part 2: Document Loader](../Part2_Document_Loader/README.md).
