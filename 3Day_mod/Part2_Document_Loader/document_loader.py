"""
Document loader for the Banking KB RAG Assistant.

Loads every .docx file in Data/, walks paragraphs and tables in the order
they appear in the document, and produces a normalized document with a
heading-based section tree. Output is written to
shared/storage/parsed_documents.jsonl, ready for semantic chunking in Part 3.

Usage:
    python document_loader.py
"""
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

import docx
from docx.table import Table
from docx.text.paragraph import Paragraph

PROJECT_ROOT = Path(__file__).resolve().parent.parent  # .../3Day_mod
sys.path.insert(0, str(PROJECT_ROOT))

from shared import config

# The knowledge base does not use Word's built-in Heading styles -- every
# paragraph is styled "Normal" or "List Bullet". Section headings are instead
# distinguished purely by bold formatting (verified across the whole corpus:
# every fully-bold "Normal" paragraph is <= 74 chars, well short of prose).
MAX_HEADING_LENGTH = 150
NUMBERED_HEADING_RE = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+\S")


@dataclass
class Section:
    heading: str
    level: int
    text: str = ""


@dataclass
class LoadedDocument:
    source_file: str
    doc_type: str
    title: str
    sections: list[Section]
    full_text: str


def is_heading(paragraph: Paragraph) -> bool:
    """A heading is a fully-bold, non-bulleted, reasonably short paragraph."""
    text = paragraph.text.strip()
    if not text or paragraph.style.name == "List Bullet":
        return False
    runs_with_text = [r for r in paragraph.runs if r.text.strip()]
    if not runs_with_text or not all(r.bold for r in runs_with_text):
        return False
    return len(text) <= MAX_HEADING_LENGTH


def heading_level(text: str) -> int:
    """Numbered headings ("1.2.3 Foo") nest by dot count; unnumbered
    banner-style headings ("Document Control Information") are top-level."""
    match = NUMBERED_HEADING_RE.match(text.strip())
    if match:
        return match.group(1).count(".") + 1
    return 1


def table_to_text(table: Table) -> str:
    """Render a table as plain text: "Key: Value" per row for 2-column
    tables (the common case here -- metadata/spec tables), pipe-separated
    otherwise."""
    lines = []
    for row in table.rows:
        cells = [cell.text.strip() for cell in row.cells]
        if len(cells) == 2:
            key = cells[0].rstrip(":").strip()
            lines.append(f"{key}: {cells[1]}")
        else:
            lines.append(" | ".join(cells))
    return "\n".join(lines)


def load_docx(path: Path) -> LoadedDocument:
    document = docx.Document(str(path))

    title = ""
    sections: list[Section] = []
    current: Optional[Section] = None

    def start_section(heading_text: str) -> None:
        nonlocal current
        current = Section(heading=heading_text, level=heading_level(heading_text))
        sections.append(current)

    def append_text(text: str) -> None:
        nonlocal current
        if current is None:
            start_section("Preamble")
        current.text = f"{current.text}\n{text}".strip() if current.text else text

    for block in document.iter_inner_content():
        if isinstance(block, Paragraph):
            text = block.text.strip()
            if not text:
                continue
            if not title:
                title = text
                continue
            if is_heading(block):
                start_section(text)
            else:
                append_text(text)
        elif isinstance(block, Table):
            append_text(table_to_text(block))

    full_text = "\n\n".join(
        f"{section.heading}\n{section.text}".strip() for section in sections
    )

    return LoadedDocument(
        source_file=path.name,
        doc_type=path.stem,
        title=title,
        sections=sections,
        full_text=full_text,
    )


def load_all_documents(data_dir: Path = config.DATA_DIR) -> list[LoadedDocument]:
    paths = sorted(data_dir.glob("*.docx"))
    if not paths:
        raise FileNotFoundError(f"No .docx files found in {data_dir}")
    return [load_docx(path) for path in paths]


def save_documents(
    documents: list[LoadedDocument], output_path: Path = config.PARSED_DOCS_PATH
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for document in documents:
            f.write(json.dumps(asdict(document), ensure_ascii=False) + "\n")


def main() -> None:
    documents = load_all_documents()
    save_documents(documents)

    print(f"Loaded {len(documents)} document(s) -> {config.PARSED_DOCS_PATH}")
    for document in documents:
        print(
            f"  - {document.source_file}: title='{document.title}', "
            f"{len(document.sections)} sections, {len(document.full_text)} chars"
        )


if __name__ == "__main__":
    main()
