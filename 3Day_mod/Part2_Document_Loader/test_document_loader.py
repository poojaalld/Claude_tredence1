"""
Sanity checks for the Part 2 document loader.

Usage:
    pytest test_document_loader.py
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from document_loader import load_all_documents
from shared import config


def test_loads_every_docx_in_data_dir():
    expected_files = {p.name for p in config.DATA_DIR.glob("*.docx")}
    documents = load_all_documents()
    assert {d.source_file for d in documents} == expected_files


def test_every_document_has_title_and_sections():
    for document in load_all_documents():
        assert document.title, f"{document.source_file} has no title"
        assert document.sections, f"{document.source_file} has no sections"
        assert document.full_text, f"{document.source_file} has no full_text"


def test_section_levels_are_positive():
    for document in load_all_documents():
        for section in document.sections:
            assert section.level >= 1
            assert section.heading
