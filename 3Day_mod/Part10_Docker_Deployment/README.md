# Part 10: Docker, Deployment, and Testing

**Status:** Implemented.

## What it does

Containerizes the whole application and adds an end-to-end test suite that
exercises the deployed system over HTTP, the way a real client would.

### One image, three roles

`Dockerfile` builds a single image containing the whole project (installed
from Part 1's `requirements.txt`, plus the full `3Day_mod` source tree).
`docker-compose.yml` runs three services from that one image, distinguished
only by the command each overrides:

| Service | Command | Role |
|---|---|---|
| `ingest` | runs Parts 2 -> 3 -> 4 -> 5 in sequence, then exits | Builds `shared/storage` (chunks, embeddings, FAISS index) into a named volume |
| `backend` | `python Part8_FastAPI_Backend/main.py` | Part 8's API, waits for `ingest` to finish successfully |
| `frontend` | `streamlit run Part9_Streamlit_Frontend/app.py` | Part 9's UI, waits for `backend`'s healthcheck, talks to it via `API_BASE_URL=http://backend:8000` (the compose network's service name, overriding `shared/.env`'s `localhost` value) |

A `storage_data` named volume is shared between `ingest` and `backend` so
the index built by one is readable by the other. `backend` exposes a
Docker healthcheck (`GET /health`) that `frontend` waits on before starting.

### Skips re-embedding on every restart

The `ingest` service checks whether `embeddings.npy` already exists in the
volume before running anything:

```sh
if [ -f /app/shared/storage/embeddings.npy ]; then
  echo 'embeddings.npy already present -- skipping load/chunk/embed'
else
  python Part2_Document_Loader/document_loader.py &&
  python Part3_Semantic_Chunking/semantic_chunker.py &&
  python Part4_Embedding_Generation/generate_embeddings.py
fi &&
python Part5_Vector_Indexing/build_index.py   # always -- cheap, no API calls
```

This matters because embedding generation calls a real, rate-limited API
(see [Part 4](../Part4_Embedding_Generation/README.md)) -- without this
check, every `docker compose up` would re-embed all 147 chunks. Indexing
itself is always re-run since it's fast, deterministic, and needs no
external calls. Since the image is built from a checkout that already has
real `shared/storage` artifacts (from running Parts 2-5 locally), the very
first `docker compose up` skips embedding entirely -- the volume gets
seeded from the image's own baked-in files on first mount. To force a full
rebuild (e.g. after changing `Data/`), remove the volume:
`docker compose down -v`.

### Optional pgvector profile

A `postgres` service (`pgvector/pgvector:pg16`, same image verified in
[Part 5](../Part5_Vector_Indexing/README.md)) is defined behind a
`pgvector` Compose profile, off by default:

```bash
docker compose -f docker-compose.yml --profile pgvector up
```

To actually use it, also set `VECTOR_STORE=pgvector` and
`DATABASE_URL=postgresql://postgres:postgres@postgres:5432/banking_rag` in
`shared/.env` first (`postgres` is the service name on the compose network,
not `localhost`).

## Files

| File | Purpose |
|---|---|
| `Dockerfile` | Single image for ingest/backend/frontend. Build context is the project root (`3Day_mod/`), not this folder. |
| `docker-compose.yml` | Orchestrates `ingest` -> `backend` -> `frontend`, plus the optional `postgres` profile. |
| `test_end_to_end.py` | pytest + httpx suite that hits a *running* deployment (local or Docker) over HTTP -- see below. |
| `docker_stack_verified.png` | Screenshot from the live verification below. |
| `../.dockerignore` | At the project root (`3Day_mod/.dockerignore`) since that's the build context -- excludes `venv/`, `.git/`, and `shared/.env` (secrets are passed at runtime via `env_file`, never baked into a layer). Deliberately does **not** exclude `shared/storage/`, so already-built artifacts ship in the image (see above). |

## End-to-end test suite

Unlike every other part's tests (which exercise that part's code
in-process), `test_end_to_end.py` hits a **running** deployment over HTTP
with `httpx` -- exactly how Part 9's frontend, or any real client, talks to
it. It covers the full pipeline in one pass: confirms Parts 2-5 actually
produced `shared/storage` artifacts, checks `/health` reports the expected
config, then drives `/query` through retrieval and Claude generation for
both an in-scope question (citations expected) and an out-of-scope one
(no fabrication expected), plus request validation. Tests skip cleanly with
a clear message if no server is reachable at `API_BASE_URL`, rather than
failing.

```bash
pytest Part10_Docker_Deployment/test_end_to_end.py -v
```

## Verification (real Docker build + run, not just written and reviewed)

Built and ran the actual stack, end to end:

```
$ docker compose -f Part10_Docker_Deployment/docker-compose.yml build
...
 ingest  Built

$ docker compose -f Part10_Docker_Deployment/docker-compose.yml up -d
 Container part10_docker_deployment-ingest-1    Started ... Exited
 Container part10_docker_deployment-backend-1   Started ... Healthy
 Container part10_docker_deployment-frontend-1  Started

$ docker logs part10_docker_deployment-ingest-1
embeddings.npy already present -- skipping load/chunk/embed (delete the storage_data volume to force a full rebuild)
VECTOR_STORE='faiss'
Built FAISS index: 147 vectors, dimension 1024 -> /app/shared/storage/faiss.index
Copied aligned metadata -> /app/shared/storage/faiss_metadata.jsonl

$ curl http://localhost:8000/health
{"status":"ok","vector_store":"faiss","embedding_provider":"voyage","claude_model":"claude-opus-5"}
```

Then ran the full E2E suite against the dockerized backend --
**5/5 passed** -- and drove the dockerized frontend in a real headless
browser (Playwright), confirming the frontend container correctly reaches
the backend container over the compose network (`API_BASE_URL=http://backend:8000`)
and renders an answer with citations identical to the local (non-Docker)
run verified in [Part 9](../Part9_Streamlit_Frontend/README.md):

![Dockerized stack, verified end-to-end](docker_stack_verified.png)

The stack was then torn down (`docker compose down`) after verification;
the `storage_data` volume was left in place so the next `up` skips
re-embedding.

## Usage

```bash
# From 3Day_mod/, with shared/.env already configured (Part 1)
docker compose -f Part10_Docker_Deployment/docker-compose.yml up
```

- Backend: `http://localhost:8000` (docs at `/docs`)
- Frontend: `http://localhost:8501`

Stop with `docker compose -f Part10_Docker_Deployment/docker-compose.yml down`
(add `-v` to also delete the built index and force a full pipeline rebuild
next time).

## Project complete

This is the last part. See the [top-level README](../README.md) for the
full pipeline overview and links to every part.
