# 2Day — Enterprise Banking AI Assistant (Claude API)

A minimal, terminal-based chat assistant built on the Claude API, with the
system prompt tuned to act as a senior solution architect for an
enterprise digital banking platform. Alongside it, a small standalone
example of wiring up Python's `logging` module.

## What's in this folder

| File | Purpose |
|---|---|
| `app.py` | The assistant itself — a command-line chat loop against the Claude API |
| `config.py` | Loads `ANTHROPIC_API_KEY` from `.env` via `python-dotenv` |
| `prompts.py` | `SYSTEM_PROMPT` — defines the assistant's persona, responsibilities, and tech stack |
| `logger.py` | Configures a logger that writes to `logs/assistant.log` |
| `test.py` | A one-line smoke test of `logger.py` (not part of the assistant flow — see note below) |
| `requirements.txt` | `anthropic`, `python-dotenv` |
| `.env` | Holds the real API key locally — never commit this |
| `venv/` | A pre-built virtual environment for this folder |
| `logs/assistant.log` | Output file for `logger.py` |

## Objective

Demonstrate the smallest possible building block of an LLM-powered
enterprise tool: a persistent, multi-turn conversation with Claude, steered
by a system prompt into a specific professional role rather than a generic
assistant.

`prompts.py` sets Claude up as:

> Senior Solution Architect for the Enterprise Digital Banking Platform —
> designs scalable software following Clean Architecture, SOLID, and
> OWASP, recommends production-ready solutions across a stack of Angular,
> Spring Boot, Java 21, Kafka, PostgreSQL, Redis, Docker, and Kubernetes,
> and always explains architecture before writing code.

`app.py` shows the mechanics that make a *conversation* work with a
stateless API: every turn's user message and Claude's reply are appended
to a running `conversation` list, and the full list is resent on each
call — Claude has no memory of its own between requests, so the app has to
carry it.

On startup, `app.py` prints an intro explaining the conversation type
(system-design questions for the enterprise banking platform) and gives an
example prompt, so it's clear what to type at `You:` rather than just
guessing.

**Note on `logger.py` / `test.py`:** `logger.py` is now wired into
`app.py` — every user query, Claude response (truncated preview), API
error, and session start/end is written to `logs/assistant.log`.
`test.py` remains a tiny standalone smoke test of the logger by itself, in
case you want to verify logging works before running the full assistant.

## How to run it

1. **Activate the environment** (from inside `2Day/`):

   ```powershell
   venv\Scripts\activate
   ```

   Or, without the bundled venv, install fresh:

   ```bash
   pip install -r requirements.txt
   ```

2. **Set your API key.** `.env` already exists in this folder with
   `ANTHROPIC_API_KEY=...` — if you need to set it up again elsewhere,
   copy that pattern (no quotes around the key).

3. **Run the assistant:**

   ```bash
   python app.py
   ```

   Chat at the `You:` prompt. Type `exit` to end the session. Each
   response comes from `claude-haiku-4-5-20251001` with the banking
   solution-architect system prompt applied.

4. **Run the logging smoke test** (optional, separate from the assistant):

   ```bash
   python test.py
   ```

   Writes one line to `logs/assistant.log`.

## Resilience built in

- **Error handling.** Authentication failures, rate limits, connection
  problems, and other API errors are caught individually, printed as a
  short friendly message, and logged — the loop keeps running instead of
  crashing. The unanswered user turn is removed from `conversation` on
  error so history stays consistent with what Claude actually saw.
- **Bounded history.** `conversation` is capped at `MAX_MESSAGES = 20`
  (~10 user/assistant turns). Once exceeded, the oldest turn is dropped
  before the next request, so a long session never grows past the model's
  context window. Alternation (`user`, `assistant`, `user`, ...) is
  preserved.
- **Logging.** Every turn and error is written to `logs/assistant.log` —
  see the note above.

## Known limitations (as currently written)

- Console output assumes a UTF-8-capable terminal (`sys.stdout` is
  reconfigured to UTF-8 at startup to handle this on Windows) — an
  unusual terminal setup could still misrender some characters.
- The trimmed-away history is gone for good within a session; there's no
  summarization of dropped turns, so Claude will "forget" details from
  early in a very long conversation once they age out.
