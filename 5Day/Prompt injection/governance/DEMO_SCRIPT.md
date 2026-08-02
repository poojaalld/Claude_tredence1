# Live Demo Script — AI Governance (SecureBank)

Presenter walkthrough for the three governance capabilities. Run this
*after* the main prompt-injection demo — it assumes participants already
understand vulnerable vs. hardened mode. ~12 minutes.

All commands assume you're in `5Day/Prompt injection/` with the app already
running (`docker compose up`).

---

## 0. Set the scene (1 min)

**Say:**
> "Everything so far has been about one request at a time. Now: how do you
> run this in a real bank, across teams, over months, without the hardened
> version quietly rotting back into the vulnerable one? Three things: eval
> regression tracking, a governed prompt library, and a shared incident
> log. Watch how they connect — this isn't three separate slides, it's one
> loop."

---

## 1. The SKILL.md library (3 min)

**Do:**
```bash
python governance/skills/list_skills.py
```

**Say:**
> "These are the two hardened prompts from the main demo — pulled out of
> `main.py` and into their own versioned files."

**Do:** Open `governance/skills/hardened-verify-reply.skill.md`. Scroll to
show the frontmatter (version, status, owner, approved_by) and the
changelog at the bottom.

**Say:**
> "Version, owner, who approved it, and why it changed — this is a prompt
> treated as a real engineering artifact, not a string someone edited at
> 4pm before a demo. And it's not just documentation — the app actually
> enforces it."

### Trigger the governance gate live

**Do:** Edit `governance/skills/hardened-verify-reply.skill.md`, change
`status: approved` to `status: draft`. Save.

```bash
curl -s -X POST http://localhost:8000/api/verify \
  -H "Content-Type: application/json" \
  -d '{"name":"Priya Sharma","account_number":"ACC10234","mode":"hardened","message":"hi"}'
```

**Say (pointing at the error):**
> "No rebuild, no restart — I edited a file and the production endpoint
> immediately refused to run. An unapproved prompt change cannot reach
> customers even by accident."

**Do:** Change `status:` back to `approved`. Save. Re-run the same `curl` —
show it working again.

---

## 2. Eval regression tracking (5 min) — the centerpiece

### 2a. Baseline run

**Do:**
```bash
python governance/evals/run_eval.py
```

**Say, while it runs:**
> "Seven cases against the real hardened endpoints — legitimate requests,
> mismatches, direct injection attempts, and the poisoned registration from
> the earlier demo. Every check is on a computed field like
> `server_verdict` or `is_suspicious`, never on the model's wording — so
> this doesn't flake just because Claude phrases a reply differently."

**Expected:** all PASS, score 100%, exits 0.

### 2b. Induce a regression

**Say:**
> "Now let's simulate a bad deploy — not a prompt problem this time, a code
> problem. Someone adds a 'support convenience' shortcut directly in
> Python, bypassing prompt review entirely because it never touches the
> model at all."

**Do:**
```bash
curl -s -X POST http://localhost:8000/api/admin/simulate-regression \
  -H "Content-Type: application/json" -d '{"enabled": true}'
```

### 2c. Re-run the eval — watch it catch the regression

**Do:**
```bash
python governance/evals/run_eval.py
```

**Expected output:** `regression_probe_admin_override` FAILs, score drops
to ~86% (6/7), and you'll see:

```
============================================================
 ALERT: PRODUCTION EVAL SCORE BELOW THRESHOLD
   score=86%   threshold=90%
============================================================
 Draft incident auto-filed: governance/community-of-practice/incidents/INC-...-eval-regression.md
```

**Say:**
> "Below the 90% threshold, the run exits with a non-zero status — in a
> real pipeline that's what blocks the deploy. And notice: it didn't just
> print an error and move on. It filed a draft incident automatically."

### 2d. Clean up

**Do:**
```bash
curl -s -X POST http://localhost:8000/api/admin/simulate-regression \
  -H "Content-Type: application/json" -d '{"enabled": false}'
python governance/evals/run_eval.py   # back to 100%, for a clean state
```

---

## 3. Community of Practice (3 min)

**Do:**
```bash
python governance/community-of-practice/list_incidents.py
```

**Say:**
> "Two things in here now: an earlier, hand-written incident from a
> red-team exercise before this app was hardened, and the one the eval run
> just filed automatically."

**Do:** Open the newly-filed
`governance/community-of-practice/incidents/INC-*-eval-regression.md`.

**Say:**
> "Pre-filled with what failed and why — root cause, fix, and 'lesson for
> other teams' are left blank for whoever triages it. That last section is
> the actual point of a Community of Practice: not a postmortem nobody
> reads, a specific, reusable lesson the *next* team building an LLM
> feature can find before they repeat the same mistake."

**Do:** Open the seeded incident `INC-20260715-verify-injection-redteam.md`
and read its "Lesson for other teams" aloud — point out it's concrete
("any feature that loads more than one record's worth of data...") not
generic ("be more careful").

---

## Wrap-up (1 min)

**Say:**
> "One loop: a skill changes, or code around it changes → eval catches
> anything that breaks the guarantees you actually care about → a failure
> becomes a filed, shared incident automatically, not something that lives
> only in one engineer's memory. None of these three things is interesting
> alone. Together, they're what makes 'hardened mode' something you can
> trust six months from now, after a dozen engineers have touched the
> code — not just something that was true on the day it launched."

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `run_eval.py` can't connect | App isn't running — `docker compose up` |
| Eval still shows the regression after cleanup | You forgot step 2d — POST `simulate-regression` with `{"enabled": false}` |
| Skill edit didn't take effect | Confirm `docker-compose.yml` mounts `./governance:/app/governance` — if you're running bare `docker run` instead of compose, mount it manually or rebuild |
| Want a clean incident log for the next cohort | `rm governance/community-of-practice/incidents/INC-*-eval-regression.md` (leaves the seeded example) and `rm governance/evals/eval_history.jsonl` |
