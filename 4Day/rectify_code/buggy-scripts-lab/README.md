# Lab 3.2 – Buggy Scripts Rescue

Practice debugging a suite of intentionally broken Node scripts while the React UI guides you through explaining each failure.

## Directory layout

- `scripts/` — five standalone Node scripts (`calculateBonus.js`, `validateUser.js`, `emailScheduler.js`, `configMerge.js`, `retryHandler.js`) that each throw a different kind of runtime or syntax error.
- `frontend/` — Vite + React dashboard that lists the scripts, shows the CLI command to reproduce the failure, and calls the backend for Claude-style diagnostics.
- `backend/` — Express service that returns curated error summaries and patch previews for every script.

## Getting started

1. Run `npm install` in both `frontend/` and `backend/`.
2. Start the backend (`npm run dev`) to expose `http://localhost:5000`.
3. Start the frontend (`npm run dev`) and open the UI on `http://localhost:5174`. The UI proxies `/api` to the backend.
4. Run each script manually (`node scripts/<name>.js`) to see the raw failure before consulting the UI.

## Lab workflow

1. Execute one of the buggy scripts locally, capture the full stack trace or console error, and note the file/line the runtime points at.
2. In the React dashboard, select the matching script, click **Ask Claude for a fix**, and observe the structured diagnostics (error summary, suggested fix, patch preview).
3. Compare Claude’s patch with what you would change manually: pay attention to guards, async usage, and input validation.

## Exercise summary

Before you finish, complete this walkthrough:

1. Run all five scripts in the `scripts/` folder and collect the stack trace or syntax error for each run. Paste each trace into the lab notes or shared document.
2. For every script, record the root cause that Claude reports and the patch preview it generates—capture both the narrative and the diff.
3. Apply your own fix locally after reviewing the suggestion. Document any differences between your patch and the Claude recommendation.
4. Reflect on which script was the easiest for Claude to explain and which required additional context (mention this in your write-up so you can compare strategies next time).
