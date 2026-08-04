"""
Sanity checks for the Part 8 FastAPI backend.

test_query_* tests call the live embedding and Anthropic APIs (through
answer_question()), so they have a small real cost. Requires Part 5's index
to already be built and ANTHROPIC_API_KEY to be set.

Usage:
    pytest test_main.py
"""
import sys
from pathlib import Path

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from main import app

client = TestClient(app)


def test_health_returns_ok_and_config():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["vector_store"] in ("faiss", "pgvector")
    assert body["claude_model"]


def test_query_rejects_empty_query():
    response = client.post("/query", json={"query": ""})
    assert response.status_code == 422


def test_query_rejects_non_positive_top_k():
    response = client.post("/query", json={"query": "test", "top_k": 0})
    assert response.status_code == 422


def test_query_returns_answer_with_sources():
    response = client.post(
        "/query",
        json={"query": "What are the disaster recovery RTO and RPO targets?", "top_k": 3},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["query"]
    assert body["answer"].strip()
    assert len(body["sources"]) == 3
    for i, source in enumerate(body["sources"], start=1):
        assert source["number"] == i
        assert source["source_file"].endswith(".docx")
