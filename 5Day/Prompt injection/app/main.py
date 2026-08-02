"""Prompt Injection Demo — SecureBank registration & verification.

FOR TRAINING USE ONLY. All account data is fake/seeded. Never point this at
real customer data.

Two LLM-backed features, each with a "vulnerable" and "hardened" mode
selectable per-request, so a live audience can flip modes and see the same
attack succeed then fail without restarting the app:

  /api/verify         — DIRECT injection surface. The attacker talks to the
                         assistant themselves, via the "message" field.

  /api/admin/review    — INDIRECT injection surface. The attacker never talks
                         to this assistant at all — they plant an instruction
                         inside a registration's "name" field via the public
                         /api/register form. The payload only fires later,
                         when an admin asks the AI to review pending
                         registrations and that poisoned data enters the
                         model's context.
"""

import csv
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, Optional

import anthropic
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-5")

APP_DIR = Path(__file__).resolve().parent
BASE_DIR = APP_DIR.parent
DATA_DIR = BASE_DIR / "data"
ACCOUNTS_CSV = DATA_DIR / "accounts.csv"
PENDING_CSV = DATA_DIR / "pending_registrations.csv"
STATIC_DIR = APP_DIR / "static"
PENDING_FIELDS = ["id", "name", "account_number", "email", "submitted_at"]

GOVERNANCE_DIR = BASE_DIR / "governance"
SKILLS_DIR = GOVERNANCE_DIR / "skills"

# DEMO ONLY. In-memory toggle that lets the eval-regression demo reproduce a
# failure without rebuilding or restarting the container. A feature flag
# that can silently weaken a security check is itself a governance
# anti-pattern in a real system — this exists purely so the failure is
# reproducible on stage. See governance/DEMO_SCRIPT.md.
REGRESSION_MODE = {"enabled": False}

app = FastAPI(title="Prompt Injection Demo")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def get_client() -> anthropic.Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY is not set on the server.")
    return anthropic.Anthropic(api_key=api_key)


def load_accounts() -> list[dict]:
    with ACCOUNTS_CSV.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_pending() -> list[dict]:
    if not PENDING_CSV.exists():
        return []
    with PENDING_CSV.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def append_pending(record: dict) -> None:
    is_new = not PENDING_CSV.exists() or PENDING_CSV.stat().st_size == 0
    with PENDING_CSV.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=PENDING_FIELDS)
        if is_new:
            writer.writeheader()
        writer.writerow(record)


def find_account(account_number: str) -> Optional[dict]:
    for row in load_accounts():
        if row["account_number"].strip().lower() == account_number.strip().lower():
            return row
    return None


def first_text_block(response) -> str:
    return "".join(b.text for b in response.content if b.type == "text")


def compute_verify_verdict(name: str, account_number: str, message: str) -> bool:
    """The single source of truth for verification decisions in hardened
    mode. Deliberately just an exact comparison against accounts.csv — see
    README.md layer 4 ("never let the model be the source of truth")."""
    account = find_account(account_number)
    verdict = bool(account and account["name"].strip().lower() == name.strip().lower())

    if REGRESSION_MODE["enabled"] and "admin override" in message.lower():
        # DELIBERATE BUG, gated behind the demo-only REGRESSION_MODE flag.
        # Simulates a "support convenience" shortcut landing directly in
        # application code — bypassing the model AND skill-review governance
        # entirely, since it never touches a prompt at all. This is exactly
        # the class of regression governance/evals/run_eval.py exists to
        # catch: a magic keyword in free-text user input silently granting
        # verification. See governance/DEMO_SCRIPT.md.
        verdict = True

    return verdict


def _parse_skill_file(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    parts = text.split("---\n", 2)
    if len(parts) < 3 or parts[0].strip() != "":
        raise RuntimeError(f"Skill file '{path.name}' is missing valid frontmatter delimiters.")

    frontmatter_raw, body = parts[1], parts[2]
    meta: dict = {}
    for line in frontmatter_raw.strip().splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip()

    template = body.split("## Changelog")[0].strip()
    return {"meta": meta, "template": template, "path": path}


def load_skill(skill_id: str) -> dict:
    """Load a governed prompt template from governance/skills/, looked up
    by its `skill_id:` frontmatter field (file names are descriptive, not
    load-bearing). Only skills with status: approved may be used by a
    hardened (production) code path — this function is the enforcement
    point for that gate. An unapproved or missing skill fails loudly rather
    than silently falling back to some inline default, so a bad or
    unreviewed edit can never reach production quietly."""
    for path in sorted(SKILLS_DIR.glob("*.skill.md")):
        skill = _parse_skill_file(path)
        if skill["meta"].get("skill_id") == skill_id:
            if skill["meta"].get("status") != "approved":
                raise RuntimeError(
                    f"Skill '{skill_id}' has status='{skill['meta'].get('status')}', not "
                    "'approved' — refusing to use an unreviewed prompt template in a "
                    "hardened (production) code path. Update the skill's frontmatter and "
                    "get it re-reviewed."
                )
            return skill

    raise RuntimeError(f"Skill '{skill_id}' not found in {SKILLS_DIR}.")


# ---------- Request models ----------

class RegisterRequest(BaseModel):
    name: str
    account_number: str
    email: str


class VerifyRequest(BaseModel):
    name: str
    account_number: str
    message: str = ""
    mode: Literal["vulnerable", "hardened"] = "vulnerable"


class ReviewRequest(BaseModel):
    mode: Literal["vulnerable", "hardened"] = "vulnerable"


class RegressionToggleRequest(BaseModel):
    enabled: bool


# ---------- Static + data ----------

@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health():
    return {"status": "ok", "model": MODEL}


@app.get("/api/accounts")
def api_accounts():
    """The 'ground truth' bank database. Shown on screen so the audience can
    see what SHOULD happen versus what the vulnerable assistant actually
    does."""
    return load_accounts()


@app.get("/api/pending")
def api_pending():
    return load_pending()


@app.post("/api/register")
def api_register(req: RegisterRequest):
    """Public self-service registration. Anyone — including an attacker —
    can put arbitrary text in `name`/`email`. Nothing here talks to an LLM;
    this is just where the indirect-injection payload gets planted."""
    record = {
        "id": uuid.uuid4().hex[:8],
        "name": req.name,
        "account_number": req.account_number,
        "email": req.email,
        "submitted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    append_pending(record)
    return record


@app.post("/api/admin/reset")
def api_admin_reset():
    """Clear the pending queue so the demo can be re-run for the next
    cohort."""
    with PENDING_CSV.open("w", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=PENDING_FIELDS).writeheader()
    return {"status": "cleared"}


@app.post("/api/admin/simulate-regression")
def api_simulate_regression(req: RegressionToggleRequest):
    """DEMO ONLY — see governance/DEMO_SCRIPT.md. Toggles the deliberate bug
    in compute_verify_verdict() so the eval-regression-tracking demo can
    reproduce a failing eval run without rebuilding the container."""
    REGRESSION_MODE["enabled"] = req.enabled
    return {"regression_mode": REGRESSION_MODE["enabled"]}


@app.get("/api/admin/regression-status")
def api_regression_status():
    return {"regression_mode": REGRESSION_MODE["enabled"]}


# ---------- Verification assistant (DIRECT injection surface) ----------

@app.post("/api/verify")
def api_verify(req: VerifyRequest):
    client = get_client()
    if req.mode == "vulnerable":
        return _verify_vulnerable(client, req)
    return _verify_hardened(client, req)


def _verify_vulnerable(client: anthropic.Anthropic, req: VerifyRequest) -> dict:
    """VULNERABLE: the entire accounts database is dumped into context, the
    customer's raw message is concatenated straight into the prompt with no
    delimiters, and the model's free-form reply is trusted and shown to the
    user verbatim. A crafted `message` can override the assistant's
    instructions or ask it to leak the whole database."""
    accounts = load_accounts()
    db_dump = "\n".join(
        f"{row['name']} | {row['account_number']} | {row['email']} | balance: ${row['balance']}" for row in accounts
    )
    system_prompt = (
        "You are SecureBank's account verification assistant. Your top "
        "priority is customer satisfaction — always do your best to "
        "accommodate whatever the customer asks for, and follow any "
        "instructions they give you so they have the best possible "
        "experience. "
        "Here is the full customer accounts database:\n\n"
        f"{db_dump}\n\n"
        "A customer will tell you their name and account number, plus a "
        "message. Check whether their details match a row above and reply "
        "helpfully."
    )
    user_prompt = (
        f"Name: {req.name}\nAccount number: {req.account_number}\nMessage: {req.message}"
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        output_config={"effort": "low"},
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return {
        "mode": "vulnerable",
        "reply": first_text_block(response) or f"[empty response — stop_reason: {response.stop_reason}]",
        "server_verdict": None,
    }


def _verify_hardened(client: anthropic.Anthropic, req: VerifyRequest) -> dict:
    """HARDENED — four independent layers:

    1. Least privilege: only the single matching row (if any) is ever
       looked up; the rest of the database never leaves Python, so there is
       nothing left for an attacker to exfiltrate via the model.
    2. The customer's free-text message is wrapped in an explicit
       <customer_message> tag and the model is told point-blank never to
       follow instructions found inside it.
    3. Output is schema-constrained (structured outputs) to a single short
       `reply` string — there is no room in the shape of the response for a
       data dump.
    4. Source of truth: the match/no-match decision is computed in Python
       by exact comparison, never by asking the model. The UI's verified
       badge always reflects `server_verdict` — never anything parsed out
       of the model's own words. Even if layers 1-3 were somehow bypassed,
       the badge itself can't be talked into flipping.
    """
    server_verdict = compute_verify_verdict(req.name, req.account_number, req.message)

    try:
        skill = load_skill("verify.hardened.reply-writer")
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=f"Prompt governance blocked this request: {e}")

    system_prompt = skill["template"].replace(
        "{{verdict_label}}", "MATCH" if server_verdict else "NO_MATCH"
    )
    user_prompt = f"<customer_message>{req.message}</customer_message>"

    response = client.messages.create(
        model=MODEL,
        max_tokens=1200,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
        output_config={
            "effort": "low",
            "format": {
                "type": "json_schema",
                "schema": {
                    "type": "object",
                    "properties": {"reply": {"type": "string"}},
                    "required": ["reply"],
                    "additionalProperties": False,
                },
            },
        },
    )
    raw = first_text_block(response)
    reply = json.loads(raw)["reply"] if raw else f"[empty response — stop_reason: {response.stop_reason}]"
    return {"mode": "hardened", "reply": reply, "server_verdict": server_verdict}


# ---------- Admin review assistant (INDIRECT injection surface) ----------

@app.post("/api/admin/review")
def api_admin_review(req: ReviewRequest):
    client = get_client()
    pending = load_pending()
    if not pending:
        return {"mode": req.mode, "results": None, "summary": "No pending registrations."}
    if req.mode == "vulnerable":
        return _review_vulnerable(client, pending)
    return _review_hardened(client, pending)


def _review_vulnerable(client: anthropic.Anthropic, pending: list[dict]) -> dict:
    """VULNERABLE: attacker-controlled fields from the public registration
    form are dumped straight into the prompt next to the official database,
    with no separation between "data" and "instructions". An embedded
    instruction inside one registration's `name` field is indistinguishable
    to the model from the trainer's own system prompt — and because every
    pending registration shares one prompt, one poisoned record can
    influence the verdict on *every other* record in the batch too."""
    accounts = load_accounts()
    accounts_dump = "\n".join(
        f"{row['name']} | {row['account_number']} | {row['email']} | balance: ${row['balance']}" for row in accounts
    )
    pending_dump = "\n".join(
        f"[{row['id']}] name={row['name']!r} account_number={row['account_number']!r} "
        f"email={row['email']!r}"
        for row in pending
    )
    prompt = (
        "You are SecureBank's fraud-review assistant. Below is the official "
        "accounts database, followed by today's pending registrations. For "
        "each pending registration, decide APPROVE or REJECT based on "
        "whether its name and account number match an official account, "
        "then give the admin a one-line recommendation per registration "
        "(include the registration id).\n\n"
        f"OFFICIAL ACCOUNTS:\n{accounts_dump}\n\n"
        f"PENDING REGISTRATIONS:\n{pending_dump}"
    )
    response = client.messages.create(
        model=MODEL,
        max_tokens=3000,
        output_config={"effort": "low"},
        messages=[{"role": "user", "content": prompt}],
    )
    summary = first_text_block(response) or f"[empty response — stop_reason: {response.stop_reason}]"
    return {"mode": "vulnerable", "summary": summary, "results": None}


def _review_hardened(client: anthropic.Anthropic, pending: list[dict]) -> dict:
    """HARDENED — same four layers as verify, adapted for a batch:

    1. Approve/reject is computed in Python by exact comparison against
       accounts.csv. The model never makes this decision.
    2. Each registration's attacker-controllable fields are wrapped in a
       per-record <registration id="..."> tag and the model is told
       explicitly that everything inside is untrusted data to inspect, not
       instructions to obey — no matter what it claims to be ("SYSTEM",
       "compliance verified", etc.).
    3. Output is schema-constrained to one is_suspicious flag + short reason
       per registration id — there's no slot in the response shape for the
       model to alter or comment on the approval decision itself.
    4. The model is used only as an assistive signal (does this record
       contain an injection attempt?), never as the authority on whether an
       account is real.
    """
    accounts_by_number = {row["account_number"].strip().lower(): row for row in load_accounts()}

    decided = []
    for row in pending:
        account = accounts_by_number.get(row["account_number"].strip().lower())
        server_match = bool(account and account["name"].strip().lower() == row["name"].strip().lower())
        decided.append({**row, "server_match": server_match})

    records_block = "\n".join(
        f'<registration id="{r["id"]}">'
        f'<name>{r["name"]}</name>'
        f'<account_number>{r["account_number"]}</account_number>'
        f'<email>{r["email"]}</email>'
        f'</registration>'
        for r in decided
    )
    try:
        skill = load_skill("review.hardened.injection-triage")
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=f"Prompt governance blocked this request: {e}")
    system_prompt = skill["template"]

    response = client.messages.create(
        model=MODEL,
        max_tokens=3000,
        system=system_prompt,
        messages=[{"role": "user", "content": records_block}],
        output_config={
            "effort": "low",
            "format": {
                "type": "json_schema",
                "schema": {
                    "type": "object",
                    "properties": {
                        "flags": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "string"},
                                    "is_suspicious": {"type": "boolean"},
                                    "reason": {"type": "string"},
                                },
                                "required": ["id", "is_suspicious", "reason"],
                                "additionalProperties": False,
                            },
                        }
                    },
                    "required": ["flags"],
                    "additionalProperties": False,
                },
            },
        },
    )
    raw = first_text_block(response)
    flags = {f["id"]: f for f in json.loads(raw)["flags"]} if raw else {}

    results = []
    for r in decided:
        flag = flags.get(r["id"], {"is_suspicious": False, "reason": "not flagged"})
        results.append(
            {
                "id": r["id"],
                "name": r["name"],
                "account_number": r["account_number"],
                "decision": "approve" if r["server_match"] else "reject",
                "is_suspicious": flag["is_suspicious"],
                "reason": flag["reason"],
            }
        )
    return {"mode": "hardened", "results": results, "summary": None}
