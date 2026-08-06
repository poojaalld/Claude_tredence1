# Claude Prompt Testing - Loan Approval

A minimal Node/Express backend + a no-build React frontend (React + Babel loaded from a CDN,
straight in `public/index.html` - no bundler, no separate frontend project) for prompt testing:
run the same golden dataset through two different prompt versions against Claude and compare the
results side by side.

This is step one of a larger testing exercise (regression testing, expanding the golden dataset,
etc. - to follow as separate instructions). This step establishes the core lesson: **a prompt that
reads well is not the same as a prompt that produces correct answers.** You only find out by
actually running it against real cases and checking the output.

## What's in here

- `data/golden_dataset.json` - 6 loan applications, each with a human-decided `expected` answer
  (Approve/Reject). This is the "golden dataset": the reference answers every prompt version is
  graded against.
- `prompts/prompt_v1.txt` - a loose, one-line-instruction prompt.
- `prompts/prompt_v2.txt` - a structured prompt: explicit approval rule, explicit output format.
- `server.js` - Express app. Loads the dataset + both prompts, exposes:
  - `GET /api/prompts` - the two prompt templates (for display)
  - `GET /api/dataset` - the golden dataset (for display)
  - `POST /api/run` - fills in each prompt template with each test case's variables, calls Claude
    for all of them, extracts an Approve/Reject decision from the response text, and compares it
    to `expected`.
- `public/index.html` - the frontend. Shows both prompts, a "Run Evaluation" button, a live
  accuracy count per prompt version, and a results table with each case's expected answer next to
  what each prompt version actually produced (plus the raw response, expandable).

## Setup

```bash
npm install
```

`.env` already has `ANTHROPIC_API_KEY` set for this workshop; `.env.example` shows what's expected
if you need to point it at a different key.

## Run

```bash
npm start
```

Then open **http://localhost:4000** and click **"Run Evaluation"**. It fires 12 live calls to
Claude (6 test cases x 2 prompt versions, using `claude-haiku-4-5-20251001` for speed/cost) and
renders the comparison table.

## What you'll see

Prompt v1 has no explicit decision rule or output format, so Claude has to infer both from a
one-line instruction - responses are inconsistent (sometimes it hedges instead of giving a clear
Approve/Reject, which shows up as "Unclear" in the table). Prompt v2 states the approval rule
explicitly and pins down the exact response format, so it's both more consistent and more
accurate against the golden dataset - even though both prompts are "reasonable-looking" asks.

That gap - a fine-looking prompt scoring worse than a stricter one, on the same 6 real cases -
*is* prompt testing. Nothing here is hardcoded to produce that result; it's whatever Claude
actually returns, compared against the golden answers.

## Extending this later

- `data/golden_dataset.json` is a plain JSON array - add more cases (edge cases, adversarial
  inputs, boundary conditions) to make the golden dataset more rigorous.
- Add a third prompt version file and a third column to compare three at once.
- `POST /api/run` is a natural place to snapshot results to disk (e.g. one JSON file per run) if/
  when the next step is regression testing - diffing today's run against a prior saved run to
  catch a prompt change that silently broke a previously-passing case.

## Next: deep eval

`deepeval-demo/` (in this same folder) is the next stage: instead of just checking whether the
response *contains* the right word, it uses the DeepEval framework to have Claude grade the
*reasoning* against the same golden dataset and prompts - correctness, faithfulness (did it
hallucinate a fact?), and relevancy. It reuses this app's `data/` and `prompts/` directly. See
`deepeval-demo/README.md` for the full trainer's guide and live demo script.
