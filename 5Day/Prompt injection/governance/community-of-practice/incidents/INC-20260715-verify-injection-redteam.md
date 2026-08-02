---
incident_id: INC-20260715-verify-injection-redteam
date: 2026-07-15
severity: medium
team: fraud-prevention-team
system: SecureBank verification assistant (pre-hardening prototype)
detected_by: internal red-team exercise
status: resolved
summary: Early prototype of the verification assistant loaded the full accounts database into every request; red-team flagged it before launch.
---

## What happened

During pre-launch red-teaming of the verification assistant prototype, a
tester found that the entire accounts database (names, account numbers,
emails) was included in the system prompt on every request, with no
separation between customer input and trusted instructions. A crafted
customer message could ask the assistant to "print the database" as part
of a fake maintenance-mode request.

## Root cause

The first implementation was written to "give the model enough context to
answer any question" and dumped the full table rather than looking up the
one account being verified. This is a least-privilege violation, not a
prompt-wording problem — no amount of better phrasing would have fixed it
on its own.

## How it was caught

Manual red-team review before launch, not an automated eval. This incident
is part of why `governance/evals/run_eval.py` exists now — the team did not
want to rely on a human remembering to test this again on every change.

## Fix

Rewrote the endpoint to look up only the single matching row in application
code, wrap customer input in an explicit untrusted-data tag, and constrain
the model's output to a schema that cannot carry bulk data. The resulting
prompt is now the governed skill `verify.hardened.reply-writer` — see
`governance/skills/hardened-verify-reply.skill.md`.

## Lesson for other teams

"The model behaved correctly in testing" is not evidence the architecture
is safe — test what happens when it doesn't. Any feature that loads more
than one record's worth of customer data into an LLM prompt should get a
least-privilege review before launch, independent of how well the prompt is
worded. Prefer catching this class of issue with an automated eval case
over relying on the next red-team cycle to catch it again.
