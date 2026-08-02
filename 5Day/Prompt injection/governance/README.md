# AI Governance — SecureBank

Three governance capabilities layered on top of the prompt-injection demo,
built to show how they interlock in practice rather than as three separate
slideware ideas:

| Capability | What it is | Where |
|---|---|---|
| **Eval regression tracking** | Automated tests that hit the live hardened endpoints and alert when the pass rate drops below a threshold | `evals/` |
| **SKILL.md library** | The hardened prompts, extracted from code into versioned, owned, reviewable Markdown files that the app refuses to use unless `status: approved` | `skills/` |
| **Community of Practice** | A shared, browsable incident log any team can write to — and that eval regressions file into automatically | `community-of-practice/` |

## How they connect

```
 skill edited  ──▶  eval suite run  ──▶  score < threshold?
 (governance/       (evals/run_eval.py)         │
  skills/*.md)                                  ▼
                                        alert + auto-filed
                                        draft incident
                                                 │
                                                 ▼
                                    community-of-practice/incidents/
                                    (team fills in root cause / fix /
                                     lesson — now visible to every
                                     other team, not just the one
                                     that broke it)
```

The eval suite is what makes the skill library's "approved" status mean
something more than a label — a skill can be marked `approved` and still
regress in *behavior* if the surrounding Python changes (see the
regression-probe case in `evals/eval_cases.py`). The incident log is what
turns a failed eval from "something one engineer fixed quietly" into
something the next team building an LLM feature actually reads before they
repeat the same mistake.

## Quick start

```bash
# from 5Day/Prompt injection/ , with the app already running (docker compose up)

# Browse the governed prompt-template registry
python governance/skills/list_skills.py

# Run the production eval suite
python governance/evals/run_eval.py

# Browse cross-team incidents
python governance/community-of-practice/list_incidents.py
```

Full click-by-click walkthrough, including how to trigger and resolve a
live regression: **`DEMO_SCRIPT.md`** in this folder.

## Design choices worth calling out to participants

- **Only the hardened prompts are governed skills.** The vulnerable
  endpoints' prompts stay as plain inline strings in `app/main.py` on
  purpose — that contrast *is* the lesson. No governance process, no
  version history, no approval gate: exactly what "vulnerable" means in
  practice, not just in the model's behavior.
- **Eval assertions check computed fields, never model prose.** Every case
  in `evals/eval_cases.py` asserts on `server_verdict` / `decision` /
  `is_suspicious` — values Python computes — not on what the model's reply
  text says. This is what makes the suite reliable enough to gate a deploy
  on: it doesn't flake because the model phrased something differently.
- **The regression used in the demo is a code bug, not a prompt attack.**
  `compute_verify_verdict()` in `app/main.py` has a `REGRESSION_MODE`-gated
  bug (a hardcoded "admin override" keyword shortcut) so the eval-failure
  demo is 100% reproducible on stage — it doesn't depend on Claude
  happening to misbehave, which (as the main demo shows) it mostly doesn't.
  This is realistic on its own terms: most production regressions caught by
  evals are ordinary logic bugs, not the model going rogue.
