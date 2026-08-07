# PDF Summarizer — Docker Demo

A minimal Claude-powered app: upload a PDF in the browser, get a summary back.
Built to demonstrate a full "build → containerize → run" Docker workflow to
participants in one pass.

- Backend: FastAPI (`app/main.py`) — one endpoint, `/api/summarize`
- Frontend: a single static HTML page (`app/static/index.html`), no build step
- Model: Claude, called via the `anthropic` Python SDK using native PDF input

## 1. Get an API key

Participants need an Anthropic API key from https://console.anthropic.com/

## 2. Configure

```bash
cp .env.example .env
# edit .env and paste your key into ANTHROPIC_API_KEY
```

## 3. Build the image

```bash
docker build -t pdf-summarizer .
```

Talk through what's happening: base image pull, dependency layer caching,
copying app code, final image size (`docker images`).

## 4. Run the container

```bash
docker run --rm -p 8000:8000 --env-file .env pdf-summarizer
```

Or with Compose:

```bash
docker compose up --build
```

## 5. Try it

Open http://localhost:8000, upload any PDF, click **Summarize**.

Useful things to point out live:

- `docker ps` — the container running
- `docker logs <container>` — requests hitting FastAPI
- Stop and restart the container — no local Python install required at all
- `curl http://localhost:8000/api/health` — quick health check endpoint

## How it works

1. The browser posts the PDF as `multipart/form-data` to `/api/summarize`.
2. FastAPI reads the bytes, base64-encodes them, and sends a single Claude
   API request with the PDF as a `document` content block plus a text
   instruction to summarize.
3. Claude's text response is returned as JSON and rendered on the page.

No file is written to disk and nothing is persisted — each request is
stateless, which keeps the demo container trivial to reason about.

## Configuration

| Env var | Required | Default | Purpose |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | yes | — | Claude API key |
| `CLAUDE_MODEL` | no | `claude-opus-5` | Override the model, e.g. `claude-sonnet-5` for a cheaper/faster demo |

## Notes for a live audience

- PDFs are capped at 32MB (Claude's per-request document limit).
- If `ANTHROPIC_API_KEY` isn't set, `/api/summarize` returns a clear 500
  instead of a stack trace — good for demonstrating error handling.
- To show a rebuild-on-change loop, edit the summarization prompt in
  `app/main.py`, then `docker build` + `docker run` again.



Steps
0. Command parsing
-t pdf-summarizer sets the image name/tag (defaults to :latest). The trailing . is the build context — the directory whose contents Docker is allowed to see and COPY from (here, pdf-summarizer/).

1. Send the build context to the Docker daemon
Docker Desktop runs a daemon (and BuildKit/buildx as the build engine). The CLI tars up the contents of . and streams it to that daemon — this is why files listed in .dockerignore are excluded (keeps .env, __pycache__, etc. out of the context).

2. Read and parse the Dockerfile
BuildKit parses Dockerfile into a sequence of build steps (a DAG of layers), each becoming a cache-checkable unit.

3. FROM python:3.11-slim
Docker checks if this base image is already cached locally. If not, it pulls it from Docker Hub, layer by layer.

4. WORKDIR /app
Sets /app as the working directory inside the image for every instruction after it.

5. COPY requirements.txt .
Copies just that one file from the build context into the image. It's deliberately copied before the rest of the app code — this is a caching trick: this layer only invalidates when requirements.txt changes.

6. RUN pip install --no-cache-dir -r requirements.txt
Runs inside a temporary container based on the image-so-far, installing FastAPI, uvicorn, the anthropic SDK, etc. (you saw this in the earlier build log — each package downloaded and installed). The result is committed as a new layer.

Because of the ordering in steps 5–6, if you only edit app/main.py later, Docker reuses the cached dependency-install layer instead of reinstalling everything — much faster rebuilds.

7. COPY app ./app
Copies the app/ folder (backend code + static frontend) into the image. This layer does invalidate on every code change, which is intentional — it's cheap, so it's placed last.

8. EXPOSE 8000
Metadata only — documents that the container listens on port 8000. It doesn't actually publish the port (that happens at docker run -p).

9. CMD [...]
Records the default command (uvicorn app.main:app --host 0.0.0.0 --port 8000) that runs when a container starts from this image. Not executed during build.

10. Export the final image
BuildKit assembles all the layers into a final image, writes the manifest/config, and tags it pdf-summarizer:latest in your local image store.

11. Done
docker images pdf-summarizer now shows the new image (as you saw earlier: ~274MB). No container is running yet — that only happens on docker run or docker compose u