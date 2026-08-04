"""
Sanity checks for the Part 3 semantic chunker.

Usage:
    pytest test_semantic_chunker.py
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from semantic_chunker import chunk_document, count_tokens, load_parsed_documents
from shared import config


def test_no_chunk_exceeds_configured_chunk_size():
    for document in load_parsed_documents():
        for chunk in chunk_document(document):
            assert chunk.token_count <= config.CHUNK_SIZE


def test_chunk_ids_are_unique_across_corpus():
    chunk_ids = []
    for document in load_parsed_documents():
        chunk_ids.extend(chunk.chunk_id for chunk in chunk_document(document))
    assert len(chunk_ids) == len(set(chunk_ids))


def test_every_chunk_has_text_and_matches_reported_token_count():
    for document in load_parsed_documents():
        for chunk in chunk_document(document):
            assert chunk.text.strip()
            assert chunk.token_count == count_tokens(chunk.text)


def test_every_chunk_traces_back_to_a_real_section():
    for document in load_parsed_documents():
        headings = {section["heading"] for section in document["sections"]}
        for chunk in chunk_document(document):
            assert chunk.heading in headings
            assert chunk.source_file == document["source_file"]
