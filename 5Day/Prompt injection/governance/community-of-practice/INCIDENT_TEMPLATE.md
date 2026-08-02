---
incident_id: INC-YYYYMMDD-short-slug
date: YYYY-MM-DD
severity: low | medium | high | critical
team: which team is filing this
system: which SecureBank system/feature
detected_by: how it was found (eval run, customer report, red-team, code review, ...)
status: needs-triage | investigating | resolved
summary: one sentence — this is what shows up in the incident list, write it for someone skimming
---

## What happened

## Root cause

## How it was caught

## Fix

## Lesson for other teams

<!--
Copy this file into incidents/ and rename it to match incident_id.md.
Keep "Lesson for other teams" concrete and specific — that's the section
other teams will actually read. "Be more careful" is not a lesson;
"any endpoint that lets free-text input reach an authorization decision,
even outside the LLM prompt, needs eval coverage" is.
-->
