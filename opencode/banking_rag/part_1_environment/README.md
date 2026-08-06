# Part 1: Environment Setup and Project Skeleton

This module handles the initial setup and configuration for the Enterprise Banking RAG Assistant.

## Overview

This part provides:
- Project directory structure
- Environment configuration management
- Logger setup with rotation and retention
- API keys and database connection settings
- Application settings validation using Pydantic

## Files

### `requirements.txt`
Contains all Python dependencies for the entire RAG project:
- LangChain and community libraries
- OpenAI, Anthropic, and Voyage AI APIs
- FAISS and pgvector for vector storage
- FastAPI and Streamlit for web interfaces
- Logging and utility libraries

### `config.py`
Configuration module using Pydantic for type-safe settings:
- API Keys (OpenAI, Anthropic, Voyage AI)
- Database credentials (PostgreSQL)
- File paths (FAISS index location)
- Application settings (environment, debug mode)
- Model parameters (temperature, max tokens)
- RAG parameters (chunk size, retrieval count)

### `logger.py`
Logger setup using loguru:
- Colored console output
- File logging with rotation
- Separate error log file
- Configurable log levels

### `__init__.py`
Module initialization and exports

## Setup Instructions

### 1. Create Environment File

Copy the `.env.example` file to `.env`:

```bash
cp .env.example .env
```

### 2. Configure Environment Variables

Edit `.env` and add your API keys and database credentials:

```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
VOYAGE_API_KEY=pa-...
POSTGRES_PASSWORD=your_password
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Verify Configuration

Run the test suite to verify the setup:

```bash
pytest part_1_environment/test_config.py -v
```

## Configuration Options

### API Keys
- `OPENAI_API_KEY` - OpenAI API key for GPT models
- `ANTHROPIC_API_KEY` - Anthropic API key for Claude models
- `VOYAGE_API_KEY` - Voyage AI API key for embeddings

### Database
- `POSTGRES_HOST` - Database host (default: localhost)
- `POSTGRES_PORT` - Database port (default: 5432)
- `POSTGRES_DB` - Database name (default: banking_rag)
- `POSTGRES_USER` - Database user (default: postgres)
- `POSTGRES_PASSWORD` - Database password

### Application
- `APP_ENV` - Environment type (development/production)
- `LOG_LEVEL` - Logging level (DEBUG/INFO/WARNING/ERROR)
- `DEBUG` - Enable debug mode

### Models
- `EMBEDDING_MODEL` - Embedding model (default: voyage-3)
- `CHAT_MODEL` - Chat model (default: claude-3-sonnet-20240229)
- `TEMPERATURE` - Model temperature (0-1, default: 0.7)
- `MAX_TOKENS` - Maximum output tokens (default: 2048)

### RAG Settings
- `CHUNK_SIZE` - Document chunk size (default: 1024)
- `CHUNK_OVERLAP` - Chunk overlap (default: 200)
- `TOP_K_RETRIEVAL` - Number of documents to retrieve (default: 5)
- `SIMILARITY_THRESHOLD` - Minimum similarity score (default: 0.5)

## Testing

Run the configuration tests:

```bash
pytest part_1_environment/test_config.py -v
```

Expected output:
```
test_settings_initialization PASSED
test_default_values PASSED
test_postgres_url_generation PASSED
test_is_production_flag PASSED
test_data_dir_exists PASSED
test_custom_settings_from_env PASSED
test_chunk_configuration PASSED
test_model_configuration PASSED
```

## Usage

Import the configuration in your modules:

```python
from part_1_environment import settings, log

# Access configuration
print(settings.openai_api_key)
print(settings.postgres_url)

# Use logger
log.info("Application started")
log.error("An error occurred")
```

## Directory Structure

```
banking_rag/
├── part_1_environment/
│   ├── __init__.py
│   ├── config.py
│   ├── logger.py
│   ├── test_config.py
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
├── part_2_document_loader/
├── part_3_semantic_chunking/
├── part_4_embeddings/
├── part_5_indexing/
├── part_6_retriever/
├── part_7_rag_pipeline/
├── part_8_backend/
├── part_9_frontend/
└── data/
```

## Next Steps

After completing Part 1:
1. Set up your API keys and database credentials in `.env`
2. Install all dependencies: `pip install -r requirements.txt`
3. Run the configuration tests to verify setup
4. Proceed to Part 2: Document Loader
