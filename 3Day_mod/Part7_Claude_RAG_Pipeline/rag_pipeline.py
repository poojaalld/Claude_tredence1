"""
Claude RAG pipeline for the Banking KB RAG Assistant.

Retrieves grounding context via Part 6's retriever, builds a prompt that
instructs Claude to answer strictly from that context and cite sources by
number, and calls the Anthropic API (CLAUDE_MODEL in shared/config.py) to
generate the final answer.

Usage:
    python rag_pipeline.py "What is the RTO for the core banking service?"
"""
import sys
from pathlib import Path

import anthropic

PROJECT_ROOT = Path(__file__).resolve().parent.parent  # .../3Day_mod
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "Part6_Retriever"))

from retriever import format_context, retrieve
from shared import config

MAX_ANSWER_TOKENS = 1024

SYSTEM_PROMPT = """You are an internal knowledge base assistant for a bank's Enterprise Digital \
Banking Platform engineering and business teams. Answer the user's question using ONLY the \
numbered source excerpts given in the context -- never rely on outside knowledge, and never guess.

Rules:
- Cite every claim with the bracketed source number(s) it came from, e.g. "[1]" or "[1][3]".
- If the context does not contain enough information to answer, say so explicitly rather than \
guessing -- do not fabricate figures, requirement IDs, or policy details.
- Prefer exact figures, thresholds, and identifiers from the source text over paraphrasing them."""


def build_user_message(query: str, results: list[dict]) -> str:
    context = format_context(results)
    return (
        f"Context:\n{context}\n\n"
        f"Question: {query}\n\n"
        "Answer using only the context above, citing sources by number."
    )


def answer_question(query: str, top_k: int | None = None) -> dict:
    """Retrieve grounding chunks and generate a cited answer.

    Returns {"query", "answer", "sources"} where each source records the
    citation number, source_file, heading_path, and retrieval score so a
    caller (Part 8's API, Part 9's UI) can render citations without
    re-deriving them from the answer text.
    """
    results = retrieve(query, top_k=top_k)
    if not results:
        return {
            "query": query,
            "answer": "No indexed documents are available to answer this question.",
            "sources": [],
        }

    config.require_anthropic_key()
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=MAX_ANSWER_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": build_user_message(query, results)}],
    )

    if response.stop_reason == "refusal":
        answer_text = "Claude declined to answer this question."
    else:
        answer_text = "".join(block.text for block in response.content if block.type == "text")

    return {
        "query": query,
        "answer": answer_text,
        "sources": [
            {
                "number": i,
                "source_file": r["source_file"],
                "heading_path": r["heading_path"],
                "score": r["score"],
            }
            for i, r in enumerate(results, start=1)
        ],
    }


def main() -> None:
    query = " ".join(sys.argv[1:]) or "What is the RTO for the core banking service?"
    result = answer_question(query)

    print(f"Query: {result['query']}\n")
    print(f"Answer:\n{result['answer']}\n")
    print("Sources:")
    for source in result["sources"]:
        print(f"  [{source['number']}] {source['source_file']} | {source['heading_path']} "
              f"(score={source['score']:.3f})")


if __name__ == "__main__":
    main()
