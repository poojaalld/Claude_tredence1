# Enterprise Banking RAG Assistant

A Retrieval-Augmented Generation (RAG) assistant that answers questions from an
internal banking knowledge base (16 `.docx` documents covering architecture,
requirements, security, deployment, incidents and more for the "Enterprise
Digital Banking Platform").

## Architecture

```
                       Part 2            Part 3            Part 4
  Data/*.docx  ->  Document Loader -> Semantic Chunker -> Embedder
                                                              |
                       Part 6            Part 5               v
  User question ->  Retriever     <-  FAISS / pgvector  <-  Vectors
                          |
                          v
              Part 7: Claude RAG pipeline (answer synthesis)
                          |
              Part 8: FastAPI backend (HTTP API)
                          |
              Part 9: Streamlit frontend (chat UI)
```

## Repository layout

```
opencode/
├── Data/                          # Internal banking knowledge base (.docx) -- input to Part 2
├── shared/
│   ├── config.py                  # Central settings used by every part
│   ├── .env.example               # Template -- copy to shared/.env and fill in keys
│   ├── storage/                   # Generated artifacts (parsed docs, chunks, embeddings, index)
│   └── logs/                      # Application logs
├── Part1_Environment_Setup/       # Env setup + project skeleton  <- you are here
├── Part2_Document_Loader/         # Load and parse .docx documents
├── Part3_Semantic_Chunking/       # Split documents into semantic chunks
├── Part4_Embedding_Generation/    # OpenAI / Voyage embeddings
├── Part5_Vector_Indexing/         # FAISS + pgvector indexes
├── Part6_Retriever/               # Similarity search over the index
├── Part7_Claude_RAG_Pipeline/     # Claude answers with retrieved context
├── Part8_FastAPI_Backend/         # FastAPI service wrapping the pipeline
├── Part9_Streamlit_Frontend/      # Streamlit chat UI
├── .gitignore
└── README.md
```

## Quick start

```bash
# 1. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows

# 2. Install dependencies (Parts 1-9)
pip install -r Part1_Environment_Setup/requirements.txt

# 3. Configure secrets
copy shared\.env.example shared\.env   # Windows
# then fill in ANTHROPIC_API_KEY and OPENAI_API_KEY (or VOYAGE_API_KEY)

# 4. Verify the environment
python Part1_Environment_Setup\verify_setup.py
```

Then proceed through the parts in order, testing each one before moving on.
