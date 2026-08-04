"""
End-to-end tests for the Banking KB RAG Assistant.

Unlike each part's own unit tests (Parts 2-8), which exercise that part's
code in-process, these tests hit a *running* deployment over HTTP with
httpx -- the same way Part 9's Streamlit frontend, or any other real
client, talks to it. This is what a deployment (local or via this part's
docker-compose.yml) is checked against, covering the full pipeline:
document loading -> chunking -> embedding -> indexing -> retrieval ->
Claude-generated, cited answer.

Usage:
    # Terminal 1: start the stack, e.g.
    python Part8_FastAPI_Backend/main.py
    # or: docker compose -f Part10_Docker_Deployment/docker-compose.yml up

    # Terminal 2:
    pytest Part10_Docker_Deployment/test_end_to_end.py -v
"""
import sys
from pathlib import Path

import httpx
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared import config

BASE_URL = config.API_BASE_URL


def _server_is_up() -> bool:
    try:
        return httpx.get(f"{BASE_URL}/health", timeout=3).status_code == 200
    except httpx.HTTPError:
        return False


pytestmark = pytest.mark.skipif(
    not _server_is_up(),
    reason=f"No running backend found at {BASE_URL} -- start it first (see module docstring)",
)


def test_pipeline_artifacts_exist():
    """Confirms Parts 2-5 actually ran somewhere: chunks and embeddings exist
    on whatever host produced this deployment's shared/storage."""
    assert config.CHUNKS_PATH.exists(), "Run Part 3's semantic_chunker.py"
    assert config.EMBEDDINGS_PATH.exists(), "Run Part 4's generate_embeddings.py"
    if config.VECTOR_STORE == "faiss":
        assert config.FAISS_INDEX_PATH.exists(), "Run Part 5's build_index.py"


def test_health_reports_the_configured_stack():
    response = httpx.get(f"{BASE_URL}/health", timeout=5)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["vector_store"] == config.VECTOR_STORE
    assert body["claude_model"]


def test_full_pipeline_answers_a_real_question_with_citations():
    """Document loading -> chunking -> embedding -> indexing -> retrieval ->
    Claude generation, exercised end-to-end through the deployed API."""
    response = httpx.post(
        f"{BASE_URL}/query",
        json={"query": "What are the disaster recovery RTO and RPO targets?", "top_k": 3},
        timeout=60,
    )
    assert response.status_code == 200
    body = response.json()

    assert body["answer"].strip()
    assert len(body["sources"]) == 3
    for i, source in enumerate(body["sources"], start=1):
        assert source["number"] == i
        assert source["source_file"].endswith(".docx")
    assert any(f"[{n}]" in body["answer"] for n in range(1, 4))


def test_out_of_scope_question_is_declined_not_fabricated():
    response = httpx.post(
        f"{BASE_URL}/query",
        json={"query": "What is the capital of France?"},
        timeout=60,
    )
    assert response.status_code == 200
    assert "paris" not in response.json()["answer"].lower()


def test_query_validation_rejects_bad_input():
    response = httpx.post(f"{BASE_URL}/query", json={"query": ""}, timeout=5)
    assert response.status_code == 422
