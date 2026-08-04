# Part 8: FastAPI Backend

**Status:** Implemented.

## What it does

`main.py` exposes Part 7's `answer_question()` over HTTP so no other
process needs direct access to the embedding provider, vector store, or
Claude credentials -- only this service does. Part 9's Streamlit frontend
(or any other client) talks to it purely over HTTP.

| Endpoint | Method | Purpose |
|---|---|---|
| `/health` | GET | Returns `status`, `vector_store`, `embedding_provider`, `claude_model` -- confirms the service is up and which backends it's configured to use. |
| `/query` | POST | Body: `{"query": str, "top_k": int \| null}`. Returns `{"query", "answer", "sources": [{"number", "source_file", "heading_path", "score"}]}`. |

### Startup warm-up

The FastAPI `lifespan` handler calls Part 6's `warm_up()` at startup, which
eagerly loads the FAISS index and metadata (a no-op for pgvector, which has
no local file to preload). This means a missing or corrupt index fails
**server startup** with a clear traceback, instead of failing silently until
a user's first request -- and that first request doesn't pay the disk-read
cost either.

### Validation and error handling

Request validation is entirely declarative via Pydantic (`QueryRequest`):
an empty `query` or a non-positive `top_k` returns `422` automatically,
verified against the running server:

```
POST /query {"query": ""}        -> 422 "String should have at least 1 character"
POST /query {"query": "x", "top_k": 0} -> 422 "Input should be greater than 0"
```

A `RuntimeError` from `answer_question()` (e.g. a missing `ANTHROPIC_API_KEY`
or embedding key) is caught and returned as a `500` with the underlying
message -- that's a server configuration problem, not something the caller
can fix by changing their request.

## Files

| File | Purpose |
|---|---|
| `main.py` | The FastAPI app: `/health`, `/query`, startup warm-up. Run directly or via `uvicorn`. |
| `test_main.py` | Sanity checks via `TestClient`: health check shape, empty-query and invalid-`top_k` validation (422), a real query returns an answer with correctly-numbered sources. |

## Verification

Ran the server live end-to-end (not just through the test client) and
confirmed:

```bash
$ curl http://127.0.0.1:8000/health
{"status":"ok","vector_store":"faiss","embedding_provider":"voyage","claude_model":"claude-opus-5"}

$ curl -X POST http://127.0.0.1:8000/query -H "Content-Type: application/json" \
    -d '{"query": "What multi-factor authentication and encryption standards does the platform use?", "top_k": 3}'
# -> full answer citing Security_Guidelines.docx, SRS.docx, BRD.docx, and
#    correctly flagging that user-level MFA specifics are NOT in the corpus
#    (the source documents only describe service-to-service auth and PSD2's
#    SCA requirement) rather than fabricating MFA mechanisms.
```

## Usage

```bash
# From 3Day_mod/, with the Part 1 venv active
python Part8_FastAPI_Backend/main.py
# or: uvicorn main:app --app-dir Part8_FastAPI_Backend --host 0.0.0.0 --port 8000
```

Interactive API docs (Swagger UI) are available at `http://localhost:8000/docs`
once the server is running (FastAPI generates this automatically from the
Pydantic models).

Run the sanity tests:

```bash
pytest Part8_FastAPI_Backend/test_main.py -v
```

3 of the 4 tests are free (health check, both validation checks); one calls
the live embedding + Claude APIs. All 4 currently pass.

## Next step

Proceed to [Part 9: Streamlit Frontend](../Part9_Streamlit_Frontend/README.md),
which will call `POST /query` on this server to build a chat UI.
