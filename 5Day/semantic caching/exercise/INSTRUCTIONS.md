# Exercise — Build a Chatbot, With and Without Semantic Caching

You'll complete `chatbot_exercise.py` in two parts. **Do them in order** —
Part 2 depends on Part 1 already working.

- **Part 1** — a plain chatbot loop with no caching at all. Every question,
  even an exact repeat, calls Claude.
- **Part 2** — add a `SemanticCache` so questions that mean the same thing
  as one you've already asked are answered instantly, without calling
  Claude again.

At the end you'll run the same question list both ways and compare.

## Setup

```bash
cd "5Day/semantic caching"
python -m venv .venv && source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env      # paste your ANTHROPIC_API_KEY in, no quotes
cd exercise
```

Open `chatbot_exercise.py`. Every place you need to write code is marked
`TODO` and currently `raise NotImplementedError(...)`.

---

## Part 1 — Chatbot without caching

### Step 1.1 — Implement `ask_claude()`

Fill in the function so it sends `question` to Claude and returns the reply
as a plain string.

```python
response = client.messages.create(
    model=MODEL,
    max_tokens=150,
    messages=[{"role": "user", "content": question}],
)
return "".join(block.text for block in response.content if block.type == "text").strip()
```

### Step 1.2 — Run it

`run_without_cache()` is already wired up to call `ask_claude()` for every
question in `QUESTIONS` — you don't need to change it. Run:

```bash
python chatbot_exercise.py
```

**Checkpoint:** you should see all 6 questions answered, including the
exact repeat of "What is the capital of France?" — notice it calls Claude
*again* for a question it already answered word-for-word. That's the
problem Part 2 fixes.

If you get a `NotImplementedError` from `run_with_cache`, ignore it for
now — the `__main__` block only calls `run_without_cache()` at this stage.

---

## Part 2 — Add semantic caching

A plain cache only helps on an *exact* repeated string. Real users rarely
repeat themselves exactly — they reword. `SemanticCache` fixes that by
comparing questions on **meaning** (via embedding vectors) instead of exact
text.

### Step 2.1 — Add the imports

At the top of the file, where the TODO comment says so, add:

```python
import numpy as np
from sentence_transformers import SentenceTransformer
```

### Step 2.2 — Implement `SemanticCache.__init__`

Store the threshold, load an embedding model, and set up storage for
answered questions:

```python
def __init__(self, similarity_threshold: float = 0.85):
    self.similarity_threshold = similarity_threshold
    self._model = SentenceTransformer("all-MiniLM-L6-v2")
    self._entries = []  # list of (question, answer, embedding) tuples
```

(First run downloads this model from Hugging Face, ~80MB — needs internet
once, then works offline.)

### Step 2.3 — Implement `SemanticCache.store`

```python
def store(self, question: str, answer: str) -> None:
    embedding = self._model.encode(question, normalize_embeddings=True)
    self._entries.append((question, answer, embedding))
```

### Step 2.4 — Implement `SemanticCache.lookup`

Embed the incoming question, compare it against every stored embedding with
cosine similarity, and return the best match if it clears the threshold —
otherwise `None`.

```python
def lookup(self, question: str):
    if not self._entries:
        return None
    query_vec = self._model.encode(question, normalize_embeddings=True)
    best_answer, best_sim = None, -1.0
    for _, answer, embedding in self._entries:
        sim = float(np.dot(query_vec, embedding))
        if sim > best_sim:
            best_answer, best_sim = answer, sim
    if best_sim >= self.similarity_threshold:
        return best_answer, best_sim
    return None
```

(Embeddings are normalized, so cosine similarity reduces to a dot product.)

### Step 2.5 — Implement `__len__`

```python
def __len__(self) -> int:
    return len(self._entries)
```

### Step 2.6 — Wire up `run_with_cache()`

Replace the `TODO` loop body with logic that, for each question:

1. Calls `cache.lookup(question)`.
2. If it's a hit — print it as a cache hit (include the similarity score),
   and **do not** call Claude.
3. If it's a miss — call `ask_claude()`, print it as a cache miss, then
   `cache.store(question, answer)`.
4. Only increments `calls` on an actual Claude call.

### Step 2.7 — Run both passes

Uncomment the `run_with_cache(client)` line in `__main__`, then:

```bash
python chatbot_exercise.py
```

---

## What you should observe

Compare the two passes:

| Question | Without cache | With cache |
|---|---|---|
| "What is the capital of France?" (original) | Claude call | Claude call (nothing to reuse yet) |
| Exact repeat | Claude call | **CACHE HIT** |
| "Which city is the capital of France?" (paraphrase) | Claude call | **CACHE HIT** — different wording, same meaning |
| "How many days does a leap year have?" (paraphrase) | Claude call | **CACHE HIT** |
| "What is the capital of Spain?" (different question) | Claude call | Claude call — **should still miss**, this is a different question, not a paraphrase |

If "capital of Spain" comes back as a cache hit, your threshold is too low
(too permissive) — try raising `similarity_threshold` toward `0.9`–`0.95`
and see what happens to the paraphrase hits.

## Stretch goals (optional)

- Print how many total Claude calls each pass made and the wall-clock time
  difference (`time.perf_counter()` is already imported).
- Try lowering the threshold until "capital of Spain" *does* wrongly hit —
  this is a good way to feel out the tradeoff between missed cache hits
  (threshold too strict) and false hits (threshold too loose).
- Add a question that's a paraphrase in a different language and see
  whether `all-MiniLM-L6-v2` (an English-tuned model) still matches it.

## If you get stuck

A completed reference implementation is in `solution/chatbot_solution.py` —
but try to get each step working yourself first. Comparing your working
code against the reference afterward is more useful than reading it before
you've attempted a step.
