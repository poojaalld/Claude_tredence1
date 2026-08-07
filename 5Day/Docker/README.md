# Docker

Hands-on Docker teaching module: containerize a small Claude-powered web app
and run it, end to end. Everything here is meant to be walked through live —
build an image, run it, inspect it, tear it down.

## Contents

```
Docker/
└── pdf-summarizer/    Claude-powered PDF summarizer, packaged as a Docker image
```

## Purpose

The goal is to give participants a complete "build → containerize → run"
workflow using a real (if minimal) application, rather than a toy
`hello-world` container. Along the way it covers:

- Writing a `Dockerfile` with cached dependency layers
- Passing secrets/config into a container via `--env-file`
- Running with plain `docker run` vs. `docker compose up`
- Inspecting a running container (`docker ps`, `docker logs`, health checks)
- Rebuild-on-change iteration

## The PDF Summarizer app

`pdf-summarizer/` is a small full-stack app: upload a PDF in the browser and
get back an AI-generated summary.

- **Backend** — FastAPI (`pdf-summarizer/app/main.py`), one endpoint:
  `POST /api/summarize`
- **Frontend** — a single static HTML page (`pdf-summarizer/app/static/index.html`),
  no build step or JS framework needed
- **Model** — Claude, called through the `anthropic` Python SDK using native
  PDF document input (the PDF is base64-encoded and sent directly to the
  model — no separate text-extraction step)

Request flow: the browser posts the PDF as `multipart/form-data` →
FastAPI reads and base64-encodes the bytes → a single Claude API request is
made with the PDF as a `document` content block plus an instruction to
summarize → Claude's text response is returned as JSON and rendered on the
page. Nothing is written to disk and nothing is persisted between requests.

## How to run it

All commands below are run from `Docker/pdf-summarizer/`.

1. **Get an API key** from https://console.anthropic.com/

2. **Configure environment**

   ```bash
   cp .env.example .env
   # edit .env and paste your key into ANTHROPIC_API_KEY
   ```

3. **Build the image**

   ```bash
   docker build -t pdf-summarizer .
   ```

4. **Run the container** — either plain Docker:

   ```bash
   docker run --rm -p 8000:8000 --env-file .env pdf-summarizer
   ```

   or with Compose:

   ```bash
   docker compose up --build
   ```

5. **Try it** — open http://localhost:8000, upload a PDF, click **Summarize**.

   Useful things to check while it's running:

   - `docker ps` — see the container running
   - `docker logs <container>` — watch requests hit FastAPI
   - `curl http://localhost:8000/api/health` — quick health check endpoint
   - Stop and restart the container — no local Python install required at all

### Configuration

| Env var | Required | Default | Purpose |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | yes | — | Claude API key |
| `CLAUDE_MODEL` | no | `claude-opus-5` | Override the model, e.g. `claude-sonnet-5` for a cheaper/faster demo |

### Notes

- PDFs are capped at 32MB (Claude's per-request document limit).
- If `ANTHROPIC_API_KEY` isn't set, `/api/summarize` returns a clear 500
  instead of a stack trace — useful for demonstrating error handling.
- To show a rebuild-on-change loop, edit the summarization prompt in
  `pdf-summarizer/app/main.py`, then `docker build` + `docker run` again.

See `pdf-summarizer/README.md` for the same walkthrough scoped to that app.
