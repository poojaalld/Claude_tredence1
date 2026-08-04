"""
Semantic chunker for the Banking KB RAG Assistant.

Reads shared/storage/parsed_documents.jsonl (produced by Part 2), splits each
section's text into sentence-level units, and groups adjacent units into
chunks using two signals:
  - a hard token-count ceiling (CHUNK_SIZE), measured with tiktoken so it
    matches how the target LLM/embedding model will actually count tokens
  - a semantic-similarity boundary: adjacent units are kept in the same
    chunk only while their TF-IDF cosine similarity stays >= the configured
    SEMANTIC_SIMILARITY_THRESHOLD, so a chunk breaks at genuine topic shifts
    rather than at an arbitrary character offset

Chunks never cross a section (heading) boundary -- the document's own
heading structure is already a strong, human-authored semantic signal, and
keeping it intact lets every chunk cite an exact heading. Chunks carry a
`heading_path` breadcrumb (e.g. "1. Executive Summary > 1.1 Executive
Summary") built from Part 2's section levels, so retrieval results keep
their place in the document hierarchy even though empty parent headings
themselves produce no chunk.

Usage:
    python semantic_chunker.py
"""
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import tiktoken
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

PROJECT_ROOT = Path(__file__).resolve().parent.parent  # .../3Day_mod
sys.path.insert(0, str(PROJECT_ROOT))

from shared import config

# A chunk is only allowed to break on a similarity drop once it already holds
# at least this fraction of CHUNK_SIZE -- otherwise noisy short lines (e.g.
# table rows, short bullets) would fragment into one-unit chunks.
MIN_FRACTION_BEFORE_SEMANTIC_BREAK = 0.3

SENTENCE_SPLIT_RE = re.compile(r'(?<=[.!?])\s+(?=[A-Z0-9"‘’“”(])')

_encoding = tiktoken.get_encoding("cl100k_base")


@dataclass
class Chunk:
    chunk_id: str
    source_file: str
    doc_type: str
    heading: str
    heading_path: str
    level: int
    chunk_index: int
    token_count: int
    text: str


def count_tokens(text: str) -> int:
    return len(_encoding.encode(text))


def split_into_units(text: str) -> list[str]:
    """Split section text (already one paragraph/bullet/table-row per line,
    from Part 2) into sentence-level units."""
    units = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        units.extend(part.strip() for part in SENTENCE_SPLIT_RE.split(line) if part.strip())
    return units


def split_oversized_units(units: list[str], chunk_size: int) -> list[str]:
    """Hard-split any single unit that alone exceeds chunk_size (e.g. an
    unbroken code/config block) into fixed-size token windows, so no chunk
    can ever exceed chunk_size regardless of input."""
    result = []
    for unit in units:
        tokens = _encoding.encode(unit)
        if len(tokens) <= chunk_size:
            result.append(unit)
            continue
        for start in range(0, len(tokens), chunk_size):
            result.append(_encoding.decode(tokens[start : start + chunk_size]))
    return result


def compute_adjacent_similarities(units: list[str]) -> list[float]:
    """similarities[i] = cosine similarity between units[i] and units[i+1]."""
    if len(units) < 2:
        return []
    try:
        vectors = TfidfVectorizer(stop_words="english").fit_transform(units)
    except ValueError:
        # e.g. every unit is pure stopwords/numbers -- fall back to "always similar"
        # so chunking degrades gracefully to size-only splitting.
        return [1.0] * (len(units) - 1)
    sims = cosine_similarity(vectors[:-1], vectors[1:])
    return [sims[i, i] for i in range(len(units) - 1)]


def compute_heading_paths(sections: list[dict]) -> list[str]:
    """Breadcrumb of ancestor headings for each section, based on level."""
    paths = []
    stack: list[tuple[int, str]] = []
    for section in sections:
        while stack and stack[-1][0] >= section["level"]:
            stack.pop()
        stack.append((section["level"], section["heading"]))
        paths.append(" > ".join(heading for _, heading in stack))
    return paths


def group_units_into_chunks(
    units: list[str],
    similarities: list[float],
    chunk_size: int,
    overlap_tokens: int,
    similarity_threshold: float,
) -> list[list[int]]:
    """Return groups of unit indices, one group per chunk."""
    token_counts = [count_tokens(unit) for unit in units]

    def carry_overlap(idxs: list[int]) -> tuple[list[int], int]:
        carried: list[int] = []
        carried_tokens = 0
        for idx in reversed(idxs):
            tokens = token_counts[idx]
            if carried and carried_tokens + tokens > overlap_tokens:
                break
            carried.insert(0, idx)
            carried_tokens += tokens
        return carried, carried_tokens

    groups: list[list[int]] = []
    current: list[int] = []
    current_tokens = 0

    for i, tokens in enumerate(token_counts):
        should_break = False
        if current:
            if current_tokens + tokens > chunk_size:
                should_break = True
            elif (
                similarities[i - 1] < similarity_threshold
                and current_tokens >= chunk_size * MIN_FRACTION_BEFORE_SEMANTIC_BREAK
            ):
                should_break = True

        if should_break:
            groups.append(current)
            current, current_tokens = carry_overlap(current)

        current.append(i)
        current_tokens += tokens

    if current:
        groups.append(current)
    return groups


def chunk_document(document: dict) -> list[Chunk]:
    sections = document["sections"]
    heading_paths = compute_heading_paths(sections)

    chunks: list[Chunk] = []
    for section_idx, section in enumerate(sections):
        units = split_oversized_units(split_into_units(section["text"]), config.CHUNK_SIZE)
        if not units:
            continue  # e.g. a numbered parent heading with only subsections beneath it

        similarities = compute_adjacent_similarities(units)
        groups = group_units_into_chunks(
            units,
            similarities,
            chunk_size=config.CHUNK_SIZE,
            overlap_tokens=config.CHUNK_OVERLAP,
            similarity_threshold=config.SEMANTIC_SIMILARITY_THRESHOLD,
        )

        for chunk_idx, idxs in enumerate(groups):
            text = " ".join(units[i] for i in idxs)
            chunks.append(
                Chunk(
                    chunk_id=f"{document['doc_type']}_{section_idx:02d}_{chunk_idx:02d}",
                    source_file=document["source_file"],
                    doc_type=document["doc_type"],
                    heading=section["heading"],
                    heading_path=heading_paths[section_idx],
                    level=section["level"],
                    chunk_index=chunk_idx,
                    token_count=count_tokens(text),
                    text=text,
                )
            )
    return chunks


def load_parsed_documents(path: Path = config.PARSED_DOCS_PATH) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"{path} not found -- run Part 2's document_loader.py first")
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def save_chunks(chunks: list[Chunk], output_path: Path = config.CHUNKS_PATH) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(asdict(chunk), ensure_ascii=False) + "\n")


def main() -> None:
    documents = load_parsed_documents()

    all_chunks: list[Chunk] = []
    print(f"Chunking {len(documents)} document(s) "
          f"(chunk_size={config.CHUNK_SIZE} tokens, overlap={config.CHUNK_OVERLAP} tokens, "
          f"similarity_threshold={config.SEMANTIC_SIMILARITY_THRESHOLD}):")
    for document in documents:
        chunks = chunk_document(document)
        all_chunks.extend(chunks)
        avg_tokens = sum(c.token_count for c in chunks) / len(chunks) if chunks else 0
        print(f"  - {document['source_file']}: {len(chunks)} chunks, avg {avg_tokens:.0f} tokens/chunk")

    save_chunks(all_chunks)

    total_tokens = sum(c.token_count for c in all_chunks)
    avg_tokens = total_tokens / len(all_chunks) if all_chunks else 0
    print(f"\nWrote {len(all_chunks)} chunks -> {config.CHUNKS_PATH}")
    print(f"Average chunk size: {avg_tokens:.0f} tokens (max configured: {config.CHUNK_SIZE})")


if __name__ == "__main__":
    main()
