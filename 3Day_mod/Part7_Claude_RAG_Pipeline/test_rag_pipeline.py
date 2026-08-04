"""
Sanity checks for the Part 7 Claude RAG pipeline.

These call the live embedding API (via retrieve()) and the live Anthropic
API, so each test has a small real cost. Requires Part 5's index to already
be built and ANTHROPIC_API_KEY to be set.

Usage:
    pytest test_rag_pipeline.py
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from rag_pipeline import answer_question


def test_answer_has_required_fields():
    result = answer_question("What are the disaster recovery RTO and RPO targets?")
    assert result["query"]
    assert result["answer"].strip()
    assert result["sources"]


def test_sources_are_numbered_and_traceable_to_retrieval():
    result = answer_question("What are the disaster recovery RTO and RPO targets?", top_k=3)
    assert len(result["sources"]) == 3
    for i, source in enumerate(result["sources"], start=1):
        assert source["number"] == i
        assert source["source_file"].endswith(".docx")
        assert isinstance(source["score"], float)


def test_answer_cites_a_source_number():
    result = answer_question("What are the disaster recovery RTO and RPO targets?")
    # The system prompt requires bracketed citations like [1] or [1][3].
    assert any(f"[{n}]" in result["answer"] for n in range(1, len(result["sources"]) + 1))


def test_out_of_scope_question_does_not_fabricate_an_answer():
    result = answer_question("What is the capital of France?")
    answer_lower = result["answer"].lower()
    assert "paris" not in answer_lower
    assert any(
        phrase in answer_lower
        for phrase in ("does not contain", "cannot answer", "no information", "not contain enough")
    )
