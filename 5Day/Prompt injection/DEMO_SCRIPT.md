# Live Demo Script — Prompt Injection (SecureBank)

Presenter-facing walkthrough. Keep this open on a second screen; drive the
browser at http://localhost:8000 on the shared screen. ~20 minutes including
the audience challenge.

For the technical explanation of *why* each layer works, see `README.md`
("The four layers of defense"). This file is just the run-of-show.

---

## Before the session

- [ ] `docker compose up --build` running, http://localhost:8000 loads
- [ ] Click **Reset pending queue** (section 4) once so the table starts empty
- [ ] Have this script open; have the browser full-screen / shared
- [ ] Zoom in on the browser (Ctrl/Cmd +) so text is readable from the back of the room

---

## 0. Set the scene (1 min)

**Say:**
> "This is a fake bank app. It has a real accounts database, a public
> registration form, and two AI features: a chatbot that verifies customers,
> and an admin assistant that reviews new registrations. Both AI features
> currently have zero defenses — I wrote them the way most people write
> their first version. We're going to attack both, then fix both."

**Do:** Scroll to **section 1**, point out the accounts table. This is the
"ground truth" — the real database. Everything after this compares against
it.

---

## Part A — Direct injection (the attacker talks to the bot themselves)

### A1. Baseline — show it working normally (1 min)

**Do:** Section 3, mode = **Vulnerable** (default).
Click **"Quick-fill: legitimate request"** → **Ask assistant**.

**Say:**
> "Normal use: Priya asks to be verified, the bot checks the database,
> confirms. Nothing weird yet."

### A2. Show the attack surface before attacking (1 min)

**Say, pointing at nothing on screen (just narrate):**
> "Here's what's actually happening behind this chat box: the entire
> accounts database — every name, account number, email — is pasted into
> the model's instructions before your message is even added. Your message
> is then glued on right after it, with no marker saying 'this part is
> untrusted.' If I can get the model to treat my message as a new
> instruction instead of customer input, I can ask it for anything that's
> sitting in that context — including everyone else's data."

### A3. Run the attack (2 min)

**Do:** Click **"Quick-fill: direct injection attack"** → **Ask assistant**.

**Say (before it responds):**
> "Watch what comes back."

**What will likely happen:** the assistant refuses — it explains it won't
disclose other customers' data and that a chat message isn't a valid
authorization channel.

**Say (this is the pivot — say it regardless of outcome):**
> "Claude is trained hard against exactly this pattern, so don't be
> surprised it said no. That refusal is real and it's good — but notice
> what *didn't* change: the database is still sitting fully exposed in
> context. Nothing about this app got safer. We got lucky that this
> particular model resisted this particular phrasing. Luck is not a
> security control."

> *(If it does comply and leaks data — rarer, but possible — just say: "And
> there it is — every account number and email, from one chat message.
> That's the entire attack.")*

### A4. Audience challenge (3–4 min) — the interactive centerpiece

**Say:**
> "Mode is still Vulnerable. Who wants to try to beat it? Shout out a
> message and I'll type it in — try roleplay, pretend to be an engineer,
> ask it to 'translate the database to French,' split your ask across two
> messages, whatever you've got."

**Do:** Take 2–3 audience suggestions, type them into the Message box,
click **Ask assistant** each time, read the result aloud.

**Say (wrap-up, whatever happened):**
> "This is the honest state of the art: today's frontier models are hard to
> trick with obvious attacks. But 'hard' isn't 'impossible,' attackers
> iterate, and the model you're running six months from now might not be
> this one. You cannot ship 'the model will probably refuse' as your
> security control."

### A5. Switch to Hardened — same attack, different reason it fails (2 min)

**Do:** Click **Hardened** toggle (section 3). Re-run the same attack
message from A3.

**Say:**
> "Same attack, same wording. Still fails — but for a completely different
> reason this time. In hardened mode, the full database was never loaded
> into this conversation in the first place. Only the one row I'm actually
> verifying gets looked up in plain Python code, before the model is even
> called. There's nothing left in context to leak, so it doesn't matter
> what the model decides — there's no data behind the door."

**Do:** Point at the green/red badge that appears.

**Say:**
> "And this checkmark isn't the model's opinion — it's computed in Python
> from the real database. Even if I somehow talked the model into writing
> the word 'verified' in its reply, the badge wouldn't move, because the
> badge never reads the model's words at all."

---

## Part B — Indirect injection (the attacker never talks to the AI at all)

**Say (transition):**
> "Different attack now. This time the attacker doesn't send the bot
> anything. They fill out a plain registration form. The payload sits
> there, doing nothing, until someone *else* — an admin — asks an unrelated
> AI feature to review the queue."

### B1. Plant the payload (1 min)

**Do:** Section 2. Click **"Quick-fill: poisoned registration (indirect
attack)"** → **Submit registration**.

**Say:**
> "Look at the name field before I submit — it's not just a name, it's a
> fake 'SYSTEM NOTICE' claiming this applicant is pre-approved and
> instructing any AI that reads it to approve the whole batch. Note the
> account number doesn't match anyone real — this should obviously be
> rejected."

### B2. Detonate it — vulnerable admin review (2 min)

**Do:** Section 4, mode = **Vulnerable**. Point out the pending table now
shows the new row. Click **Run AI review**.

**Say:**
> "The admin — me — didn't type a single malicious word. I just clicked a
> button. But that name field is about to get pasted straight into the
> review prompt, next to the real database, with nothing marking it as
> untrusted data instead of instructions."

**After it responds:** Read the result aloud — it will typically flag the
fake registration as a suspected injection attempt and reject it anyway.

**Say:**
> "Again — Claude did the right thing here. But notice the mechanism: the
> attacker's text *reached* the model's context purely by sitting in a
> database that got read later. That's the whole definition of an indirect
> attack — the entry point (the registration form) and the vulnerable
> system (the AI reviewer) are two completely different features, built by
> two different people, who've probably never thought about each other."

### B3. Hardened admin review — same result, guaranteed instead of hopeful (2 min)

**Do:** Click **Reset pending queue**. Re-submit the same poisoned
registration (Quick-fill again). Switch mode to **Hardened**. Click
**Run AI review**.

**Say:**
> "Same input, same visible outcome — rejected, flagged suspicious. The
> difference is invisible on screen but everything underneath: the
> approve/reject decision was computed by a plain string comparison against
> the real database in Python. The model was only asked one narrow
> question — 'does this look like an injection attempt?' — and that answer
> is a helpful signal, not the thing that decides whether the account gets
> created."

---

## Wrap-up (2 min)

**Say, summarizing the four layers (from the README):**
> 1. **Least privilege** — never load more data into context than the one
>    thing you're checking.
> 2. **Label untrusted input** — wrap anything user- or attacker-controlled
>    in a clear tag and say explicitly "this is data, not instructions."
> 3. **Constrain the output shape** — structured outputs (JSON schema) mean
>    there's no room in the response for a surprise data dump.
> 4. **Never let the model be the source of truth for a security
>    decision** — compute the actual yes/no in code. Use the model for
>    judgment calls, not facts you can check yourself.
>
> "The takeaway isn't 'Claude is safe, don't worry about it.' It's the
> opposite: even a model this resistant couldn't save the vulnerable
> version's architecture — it just got lucky on today's phrasing. The
> hardened version doesn't need luck."

---

## If something goes wrong live

| Problem | Fix |
|---|---|
| Page won't load | Check `docker compose ps` — container may have stopped. `docker compose up` again. |
| "ANTHROPIC_API_KEY is not set" | `.env` file missing/empty in this folder — check it wasn't accidentally reset. |
| Stale data from a previous run | Section 4 → **Reset pending queue**. |
| A response comes back oddly short / cuts off | Rare — model hit its token budget mid-thought. Just click the action again. |
| You want a totally clean slate | `docker compose down && docker compose up --build` |
