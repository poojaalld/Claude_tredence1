# Deep Eval Demo (Trainer's Guide)

This is the second stage of the prompt-testing story that started in the parent
`claude-prompt-eval-app` folder. That app checked one thing: does the response
*contain* the word "Approve" or "Reject"? That's enough to catch a totally broken
prompt, but it can't tell you *why* an answer is wrong, whether the model made
up facts, or whether it's actually answering the right question. **DeepEval**
is a framework built for that next layer: instead of string matching, an LLM
(the "judge") reads the response and scores it against a rubric you define.

This folder is built so you can run it live in front of participants and have
something real to point at - not a canned result. Every number quoted below
came from an actual run of this exact code.

## The story arc for participants

1. Parent app: "Does the output contain the right word?" -> both prompts looked
   plausible; simple checking already showed prompt v1 failing more often.
2. This folder: "*Why* is it failing, and is it failing in ways a string match
   can't even see?" -> deep eval finds prompt v1 isn't just picking the wrong
   word sometimes - it's **hallucinating a fact that was never given to it**,
   and that's what's driving the wrong answer.

## What's in here

- `claude_model.py` - wraps Claude as DeepEval's judge model. DeepEval defaults
  to OpenAI; this is the ~15 lines needed to point it at Claude instead. Good
  to show participants directly - it's the entire "plug in your own LLM"
  contract (`load_model` / `generate` / `a_generate` / `get_model_name`).
- `generate_outputs.py` - **Step 1.** Reuses the *same* golden dataset and the
  *same* two prompts from the parent app (`../data`, `../prompts`) and calls
  Claude for real, saving the results to `generated_outputs.json`. Kept
  separate from grading on purpose: generation costs an API call per case;
  grading (step 2) doesn't need to repeat that every time you tweak a metric.
- `test_deep_eval_loan.py` - **Step 2.** A pytest file. Loads
  `generated_outputs.json` and grades every case with three DeepEval metrics
  (explained below), judged by Claude.
- `run_demo.ps1` - runs step 2 with the environment variables this setup needs
  (see "Windows quirks" below) already set.

## Setup (do this before the session)

```powershell
cd deepeval-demo
python -m venv venv
venv\Scripts\pip install -r requirements.txt
```

`.env` already has `ANTHROPIC_API_KEY` set for this workshop.

Generate the outputs once, ahead of time (takes ~10 seconds, costs a few cents):

```powershell
venv\Scripts\python generate_outputs.py
```

This calls Claude for 3 representative golden cases x 2 prompt versions and
writes `generated_outputs.json`. It's checked in, so participants (or you, on
demo day) don't strictly need to re-run this - but running it live once, so
they see the raw text Claude actually produced, is a good warm-up before the
grading step.

## Running the live demo

```powershell
.\run_demo.ps1
```

This is the moment to narrate. It takes about 1-2 minutes and prints a table
scoring all 6 test cases (3 cases x 2 prompt versions) across 3 metrics each.

### Suggested narration, in order

1. **Before it finishes** - remind participants what's being tested: the exact
   same 3 loan applications, run through prompt v1 (loose) and prompt v2
   (structured), just like the Node app - except now Claude itself is grading
   the answers on three dimensions, not just "did it say the right word."

2. **When the table appears** - point at the overall pass rate first (a real
   run of this exact setup produced **4/6 passed, 2 failed** - both failures on
   prompt v1). Ask: "the two prompts both look like reasonable asks to write -
   so why does one score so much worse?"

3. **Open the failing case's reason field** (case `L001-prompt-v1`, metric
   *Loan Decision Correctness*). This is real output from an actual run - read
   it out loud:

   > "The ACTUAL_OUTPUT decision (Reject) directly contradicts the
   > EXPECTED_OUTPUT decision (Approve)... while the ACTUAL_OUTPUT correctly
   > calculates the total monthly EMI obligations (₹24,800) and identifies
   > that this exceeds the 50% threshold of monthly salary (₹3,750)... the
   > ACTUAL_OUTPUT's reasoning is logically sound and mathematically accurate,
   > but it reaches the opposite decision from what is expected."

   This is the key teaching moment: **the model's math was internally
   consistent - it just started from a wrong assumption.** A plain
   "contains('Reject')" check would have failed this case too, but it
   would never have told you *why*, or that the failure is systematic rather
   than random.

4. **Now open the Faithfulness metric for the same case** and read this real
   reason:

   > "The retrieval context clearly states a monthly salary of ₹90,000, but
   > the actual output incorrectly treats this as an annual salary and
   > calculates a monthly income of ₹7,500. This fundamental
   > misinterpretation cascades into an incorrect debt-to-income ratio
   > calculation of 330% when it should be approximately 13.3%."

   Say it plainly: **the loose prompt (v1) never said "monthly" - it just
   said "Salary: 90000" - so Claude guessed it meant annual, invented a
   currency symbol that was never in the prompt at all, and that single
   invented assumption is what flipped a clearly approvable loan into a
   rejection.** The structured prompt (v2) says "Monthly Salary" explicitly
   and this exact failure does not happen for it.

5. **Land the point:** a prompt review that only reads the prompt text, or
   only checks "did it contain the right word," would have missed this
   entirely - v1 *looks* like a perfectly normal instruction. You only find a
   silent, wrong assumption like this by checking the *reasoning*, against
   the *actual facts given* - which is exactly what "deep" evaluation adds
   over simple output matching.

## The three metrics, and what each one is for

| Metric | Question it answers | Catches |
|---|---|---|
| **Correctness** (`GEval`) | Does the decision match the expected answer, with reasoning that's actually consistent with the stated rule? | Right answer/wrong reasoning, and confident-sounding wrong answers - not just wrong words |
| **Faithfulness** | Does the reasoning stick to the facts it was actually given (the applicant's real numbers), or invent something? | Hallucination - exactly the "annual vs monthly" fabrication above |
| **Answer Relevancy** | Does the response actually address *this* applicant's numbers, or could it be generic filler? | Off-topic or templated non-answers |

`GEval` is DeepEval's "define your own rubric in plain English, an LLM judges
against it" metric - show participants the `criteria=` string in
`test_deep_eval_loan.py` directly; that's the whole mechanism. Faithfulness
and Answer Relevancy are built-in metrics that ship with DeepEval.

## Why Claude is grading Claude (and why that's fine here)

Using a judge model in the same family as the model being tested (Claude
generating the answer, Claude grading it) is a legitimate, common pattern
called LLM-as-judge - it's not circular reasoning, because the judge is given
an explicit rubric/expected answer to check against, not asked to just "vibe
check" its own sibling's work. Worth naming for participants as a discussion
point though: a judge model can share blind spots with the model it's
grading, which is why real production eval pipelines sometimes mix judge
providers, or spot-check judge scores against a human periodically.

## Windows quirks this repo works around (context if something looks odd)

Two Windows-specific issues showed up while building this, both worked around
in `run_demo.ps1`:

- **Console encoding**: `deepeval`'s pretty-printed results table can include
  non-ASCII characters (the ₹ symbol above, checkmarks, etc.) that crash on
  Windows' default `cp1252` console encoding. `PYTHONIOENCODING=utf-8` and
  `PYTHONUTF8=1` fix this.
- **Disk-cache bug**: DeepEval normally caches test results to disk (to speed
  up reruns). On this machine, that cache manager hit a file-locking issue
  specific to Windows and crashed every test with an unrelated
  `AttributeError`. Setting `DEEPEVAL_FILE_SYSTEM=READ_ONLY` tells DeepEval to
  skip the disk cache entirely - harmless for a one-off demo, since we aren't
  relying on cached reruns.

If you ever see a `ValueError: Evaluation LLM outputted an invalid JSON`
instead of a real score: that's the judge model occasionally not following
the "reply with strict JSON" instruction DeepEval sends it internally (LLM
judges are themselves imperfect - a good aside if it happens live). Just
re-run `.\run_demo.ps1` - it's not a bug in this project's code.

## Extending this later

- `generate_outputs.py`'s `DEMO_CASE_IDS` only covers 3 of the 6 golden cases,
  chosen to keep a live demo fast and cheap. Add more IDs from
  `../data/golden_dataset.json` to widen coverage.
- Add a `HallucinationMetric` alongside `FaithfulnessMetric` for a second,
  differently-worded check on the same fabrication problem.
- Swap `ClaudeJudge` for DeepEval's built-in `deepeval.models.AnthropicModel`
  if you want the officially maintained version instead of this hand-rolled
  one - `claude_model.py`'s docstring explains the tradeoff.
