# Part 7: Claude RAG Pipeline

**Status:** Implemented.

## What it does

`answer_question(query, top_k=None)` in `rag_pipeline.py` is the pipeline
Part 8's API will call: it retrieves grounding chunks via Part 6's
`retrieve()`, builds a system + user prompt that requires Claude to answer
**only** from that context and cite sources by number, calls
`CLAUDE_MODEL` (`shared/config.py`) via the Anthropic API, and returns a
structured result with the answer plus the source list used to produce it.

### Model default

`CLAUDE_MODEL` defaults to `claude-opus-5` -- Anthropic's current
recommended default absent an explicit request for a different model. (Part
1 had originally defaulted this to `claude-sonnet-5`; corrected here, where
the model is actually invoked, per Anthropic's own guidance to default to
the most capable model unless told otherwise. Override via `CLAUDE_MODEL` in
`shared/.env` if you want a cheaper/faster model for this workload.)

### Groundedness -- verified, not just prompted

The system prompt requires bracketed citations (`[1]`, `[1][3]`) for every
claim and instructs Claude to say so explicitly rather than guess when the
context doesn't contain an answer. This was verified against the real
pipeline, not just asserted in the prompt:

- **On-topic** (`"What are the disaster recovery RTO and RPO targets?"`):
  returned the exact figures (RPO=0, RTO<15m) with citations to `BRD.docx`
  and `SRS.docx`, plus supporting context from a third source -- precise,
  cited, no hallucination.
- **Out-of-scope** (`"What is the capital of France?"`): the retriever still
  returned its top-5 chunks (cosine search always returns *something*), but
  at conspicuously low scores (~0.22 vs ~0.3-0.5 for genuine matches).
  Claude correctly recognized none of them were relevant and declined to
  answer, rather than answering "Paris" from outside knowledge.

## Files

| File | Purpose |
|---|---|
| `rag_pipeline.py` | `answer_question()`, `build_user_message()`. Run directly with a query string for manual inspection. |
| `test_rag_pipeline.py` | Sanity checks: result has required fields, sources are numbered/traceable, the answer contains a citation marker, an out-of-scope question doesn't fabricate an answer (checked structurally -- see note below). |

## Usage

```bash
# From 3Day_mod/, with the Part 1 venv active
python Part7_Claude_RAG_Pipeline/rag_pipeline.py "What are the disaster recovery RTO and RPO targets?"
```

Run the sanity tests:

```bash
pytest Part7_Claude_RAG_Pipeline/test_rag_pipeline.py -v
```

Each test calls both the live embedding API (via `retrieve()`) and the live
Anthropic API, so the 4-test suite has a small real cost and takes about a
minute (paced by Voyage's 3-requests/minute limit on this environment's
no-payment-method tier -- see [Part 4](../Part4_Embedding_Generation/README.md)).
All 4 currently pass. Note: the out-of-scope test checks for refusal
language in the response -- this is a property of the LLM's behavior, not a
hard guarantee, so treat it as a regression check rather than a proof the
model can never hallucinate.

## Next step

Proceed to [Part 8: FastAPI Backend](../Part8_FastAPI_Backend/README.md),
which will expose `answer_question()` over HTTP for
[Part 9's Streamlit frontend](../Part9_Streamlit_Frontend/README.md) to call.
