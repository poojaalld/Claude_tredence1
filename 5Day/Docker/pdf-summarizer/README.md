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
