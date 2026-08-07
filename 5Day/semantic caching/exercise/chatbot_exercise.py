"""EXERCISE — build a Q&A bot, then add semantic caching to it.

Follow INSTRUCTIONS.md. Do not skip ahead — the file is meant to be
completed in the order the TODOs appear:

  PART 1 (no caching): implement ask_claude() and run_without_cache().
  PART 2 (add caching): implement the SemanticCache class and run_with_cache().

Search for "TODO" — every one needs code before this file will run.
"""

import os
import time

import anthropic
from dotenv import load_dotenv

# TODO (Part 2 only): you will need two more imports here once you start
# building SemanticCache — a way to turn text into a vector, and something
# to do math on vectors. Look at what demo/semantic_cache.py in the sibling
# `demo/` folder imports for a hint, but don't just copy it in yet — get
# there via the instructions first.

load_dotenv()

MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-5")

# Same question set the instructions walk through: some originals, an exact
# repeat, paraphrases of two of them, and one genuinely different question.
QUESTIONS = [
    ("What is the capital of France?", "original"),
    ("How many days are in a leap year?", "original"),
    ("What is the capital of France?", "EXACT REPEAT of Q1"),
    ("Which city is the capital of France?", "PARAPHRASE of Q1"),
    ("How many days does a leap year have?", "PARAPHRASE of Q2"),
    ("What is the capital of Spain?", "DIFFERENT question - should NOT hit"),
]


def get_client() -> anthropic.Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("Set ANTHROPIC_API_KEY in your environment or .env file.")
    return anthropic.Anthropic(api_key=api_key)


def ask_claude(client: anthropic.Anthropic, question: str) -> str:
    """TODO (Part 1): send `question` to Claude and return the reply text.

    Hints:
    - client.messages.create(model=MODEL, max_tokens=..., messages=[...])
    - `messages` is a list with one dict: {"role": "user", "content": question}
    - The response has response.content, a list of content blocks. Each
      text block has a `.text` attribute and `.type == "text"`. Join them.
    """
    raise NotImplementedError("TODO: implement ask_claude")


class SemanticCache:
    """TODO (Part 2): serve an existing answer whenever a NEW question is
    semantically close enough to one already asked — even worded completely
    differently.

    You'll need:
    - An embedding model to turn text into a vector. Suggested:
      `SentenceTransformer("all-MiniLM-L6-v2")` from the `sentence-transformers`
      package — call `.encode(text, normalize_embeddings=True)`.
    - A similarity function between two vectors. Because embeddings above
      are normalized, cosine similarity is just `numpy.dot(a, b)`.
    - A `similarity_threshold` (start around 0.85) above which two
      questions count as "the same question."
    - Somewhere to store every (question, answer, embedding) triple you've
      already handled, so lookup() can compare a new question against all
      of them and keep the best match.
    """

    def __init__(self, similarity_threshold: float = 0.85):
        # TODO: save similarity_threshold, load an embedding model, and set
        # up a place to store entries (e.g. a list).
        raise NotImplementedError("TODO: implement __init__")

    def lookup(self, question: str):
        """TODO: return (cached_answer, similarity) for the best-matching
        stored question if its similarity >= self.similarity_threshold,
        otherwise return None."""
        raise NotImplementedError("TODO: implement lookup")

    def store(self, question: str, answer: str) -> None:
        """TODO: embed `question` and save it alongside `answer` so future
        lookups can find it."""
        raise NotImplementedError("TODO: implement store")

    def __len__(self) -> int:
        raise NotImplementedError("TODO: return how many entries are stored")


def run_without_cache(client: anthropic.Anthropic) -> tuple[int, float]:
    """PART 1 checkpoint. Call Claude for every question, no caching at all.
    Should already work once ask_claude() is implemented — nothing else to
    do here."""
    print("\n=== WITHOUT semantic caching ===")
    calls = 0
    start = time.perf_counter()
    for question, label in QUESTIONS:
        answer = ask_claude(client, question)
        calls += 1
        print(f"\n[{label}] {question!r}\n  -> {answer[:100]}")
    elapsed = time.perf_counter() - start
    print(f"\nTotal: {calls} Claude calls, {elapsed:.2f}s")
    return calls, elapsed


def run_with_cache(client: anthropic.Anthropic) -> tuple[int, float]:
    """PART 2 checkpoint. Same questions, but routed through a SemanticCache.

    TODO: for each (question, label) in QUESTIONS:
      1. Call cache.lookup(question).
      2. If it returns a (answer, similarity) hit, print it as a CACHE HIT
         (include the similarity score) and do NOT call Claude.
      3. If it returns None, call ask_claude(), print it as a CACHE MISS,
         then cache.store(question, answer) so a later similar question
         can reuse it.
      4. Only count towards `calls` the questions that actually reached
         Claude.
    """
    cache = SemanticCache(similarity_threshold=0.85)
    print("\n=== WITH semantic caching ===")
    calls = 0
    start = time.perf_counter()

    # TODO: replace this line with the loop described above.
    raise NotImplementedError("TODO: implement the cache-aware loop")

    elapsed = time.perf_counter() - start
    print(f"\nTotal: {calls} Claude calls, {elapsed:.2f}s, {len(cache)} entries cached")
    return calls, elapsed


if __name__ == "__main__":
    client = get_client()
    run_without_cache(client)
    # TODO: once Part 1 works end to end, uncomment the line below and
    # move on to Part 2.
    # run_with_cache(client)
