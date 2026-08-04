"""
Sanity checks for the Part 6 retriever.

These call the live embedding API (a handful of short queries -- trivial
cost) since the whole point of the retriever is the embed-then-search
round trip. Requires Part 5's index to already be built.

Usage:
    pytest test_retriever.py
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from retriever import format_context, retrieve
from shared import config

REQUIRED_FIELDS = {
    "chunk_id", "source_file", "doc_type", "heading",
    "heading_path", "level", "chunk_index", "token_count", "text", "score",
}


def test_retrieve_respects_top_k():
    results = retrieve("What is the disaster recovery RTO?", top_k=3)
    assert len(results) == 3


def test_retrieve_defaults_to_configured_top_k():
    results = retrieve("What is the disaster recovery RTO?")
    assert len(results) == config.TOP_K


def test_results_have_required_fields_and_are_sorted():
    results = retrieve("What is the disaster recovery RTO?", top_k=5)
    for result in results:
        assert REQUIRED_FIELDS.issubset(result.keys())
        assert result["text"].strip()
    scores = [r["score"] for r in results]
    assert scores == sorted(scores, reverse=True)


def test_query_surfaces_the_obviously_relevant_document():
    results = retrieve("What OAuth and mTLS authentication protocols are mandated?", top_k=3)
    assert any(r["source_file"] == "Security_Guidelines.docx" for r in results)


def test_format_context_includes_source_and_text():
    results = retrieve("What is the disaster recovery RTO?", top_k=2)
    context = format_context(results)
    for result in results:
        assert result["source_file"] in context
        assert result["text"] in context
