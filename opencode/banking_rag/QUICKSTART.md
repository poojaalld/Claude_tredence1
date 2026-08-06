# Quick Start Guide - Banking RAG Assistant

## Installation (5 minutes)

```bash
# 1. Navigate to project
cd banking_rag

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate      # Windows

# 3. Install dependencies
pip install -r part_1_environment/requirements.txt

# 4. Set up configuration
cp part_1_environment/.env.example .env
# Edit .env with your API keys (optional for demo)
```

## Running the System

### Option A: FastAPI Backend Only (Testing)
```bash
python -m uvicorn part_8_backend.app:app --reload --host 0.0.0.0 --port 8000
```

Visit http://localhost:8000/docs for interactive API documentation

### Option B: Streamlit Frontend (Interactive)
```bash
streamlit run part_9_frontend/app.py
```

Visit http://localhost:8501 in your browser

### Option C: Full Stack (Recommended)
```bash
# Terminal 1: Start API backend
python -m uvicorn part_8_backend.app:app --reload

# Terminal 2: Start Streamlit frontend
streamlit run part_9_frontend/app.py
```

## Using the System

### Via Streamlit UI
1. Open http://localhost:8501
2. Enter your question in the chat box
3. View the answer with confidence score and sources
4. Check "View Details" for more information
5. Browse Statistics tab for system metrics

### Via REST API
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the interest rate for savings accounts?",
    "top_k": 5,
    "max_tokens": 2048
  }'
```

### Via Python Code
```python
from part_7_rag_pipeline import RAGPipeline
from part_1_environment import log

# Initialize RAG pipeline
rag = RAGPipeline(retrieval_pipeline, embedding_gen, logger=log)

# Process query
response = rag.process_query("What is the interest rate?")

# Access response
print(response.response)           # Generated answer
print(response.sources)             # Document sources
print(f"{response.confidence:.1%}") # Confidence score
```

## Example Queries

The system comes with sample banking documents. Try these questions:

1. "What is the interest rate for savings accounts?"
2. "How much does a personal loan cost?"
3. "What are the ATM fees?"
4. "How do I apply for a mortgage?"
5. "What is your fraud protection policy?"

## Testing the System

```bash
# Run all tests
pytest part_*/test_*.py -v

# Run specific part tests
pytest part_1_environment/test_config.py -v
pytest part_2_document_loader/test_document_loader.py -v
# ... etc for all parts

# Run with coverage
pytest part_*/test_*.py --cov=part_* -v
```

## Project Structure

```
banking_rag/
├── part_1_environment/       Configuration & logging
├── part_2_document_loader/   Load documents
├── part_3_semantic_chunking/ Split documents
├── part_4_embeddings/        Generate embeddings
├── part_5_indexing/          Create vector index
├── part_6_retriever/         Retrieve similar chunks
├── part_7_rag_pipeline/      RAG orchestration
├── part_8_backend/           FastAPI REST API
├── part_9_frontend/          Streamlit UI
└── data/                      Sample documents
```

## Configuration

Edit `.env` file to customize:

```env
# API Keys (optional for demo with mock models)
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
VOYAGE_API_KEY=your_key_here

# Model Settings
EMBEDDING_MODEL=voyage-3
CHAT_MODEL=claude-3-sonnet-20240229
TEMPERATURE=0.7
MAX_TOKENS=2048

# RAG Settings
CHUNK_SIZE=1024
CHUNK_OVERLAP=200
TOP_K_RETRIEVAL=5
SIMILARITY_THRESHOLD=0.5

# Server Settings
API_HOST=0.0.0.0
API_PORT=8000
```

## Troubleshooting

### API Won't Start
```bash
# Check if port 8000 is available
lsof -i :8000          # Linux/Mac
netstat -ano | findstr :8000  # Windows

# Check Python version (need 3.13+)
python --version

# Check health endpoint
curl http://localhost:8000/health
```

### Frontend Won't Connect
1. Ensure API is running first
2. Check API URL in Streamlit sidebar
3. Look for errors in Streamlit logs
4. Try refreshing the browser

### Tests Failing
```bash
# Reinstall dependencies
pip install --upgrade -r part_1_environment/requirements.txt

# Run individual test
pytest part_1_environment/test_config.py::TestConfiguration::test_settings_initialization -v
```

## Architecture Overview

```
User Input (Chat/API)
        ↓
[FastAPI/Streamlit]
        ↓
[Configuration & Logging]
        ↓
[Query Embedding]
        ↓
[Vector Similarity Search]
        ↓
[Document Retrieval]
        ↓
[RAG Pipeline]
        ↓
[Claude AI Generation]
        ↓
[Formatted Response with Sources]
```

## Key Features

- **📄 Multi-Format Support**: Load TXT, PDF, DOCX documents
- **🔍 Semantic Search**: Intelligent chunking and retrieval
- **🤖 AI Generation**: Claude-powered responses
- **📊 Confidence Scoring**: Know how reliable answers are
- **📚 Source Attribution**: See where information comes from
- **💾 Caching**: Reuse embeddings for faster responses
- **📈 Statistics**: Track system performance
- **🔐 Error Handling**: Graceful degradation

## Performance

- Single query: ~2-5 seconds
- Document loading: ~100ms per document
- Chunking: ~10ms per 1000 characters
- Retrieval: ~10-50ms
- Generation: ~1-3 seconds

## Next Steps

1. **Customize Data**: Add your own banking documents to `data/`
2. **Fine-tune Models**: Use domain-specific embeddings
3. **Deploy**: Use Docker/Kubernetes for production
4. **Monitor**: Track usage and performance
5. **Expand**: Add more documents as needed

## Documentation

- **Complete**: See `COMPLETE_PROJECT_SUMMARY.md`
- **By Part**: Each part has its own README.md
- **API Docs**: Visit http://localhost:8000/docs
- **Code**: Docstrings in every function

## Support

- Check README files in each part
- Review test files for usage patterns
- Check logs in `logs/` directory
- Run health check: `curl http://localhost:8000/health`

## Advanced Usage

### Custom Document Loading
```python
from part_2_document_loader import BulkDocumentLoader

loader = BulkDocumentLoader()
docs = loader.load_from_directory("./my_documents")
```

### Custom Chunking Strategy
```python
from part_3_semantic_chunking import BulkChunker, ChunkingStrategy

chunker = BulkChunker(strategy=ChunkingStrategy.SEMANTIC)
chunks = chunker.chunk_documents(docs)
```

### Index Building
```python
from part_5_indexing import IndexManager

index = IndexManager(index_type="faiss", embedding_dim=1536)
index.add_embedded_chunks(embedded_chunks)
index.save_index("./my_index")
```

---

**Happy querying! 🚀**

For detailed documentation, see the COMPLETE_PROJECT_SUMMARY.md file.
