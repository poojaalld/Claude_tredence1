#!/usr/bin/env python3
"""Eval regression tracking for SecureBank's hardened endpoints.

Runs the suite in eval_cases.py against a live instance of the app,
appends a scored record to eval_history.jsonl, and — if the score falls
below the configured threshold — prints an alert and auto-files a draft
incident into ../community-of-practice/incidents/ for a human to triage.

This is the loop:
  skill/code changes → run this → threshold breach → incident filed
    → team fixes it → incident becomes a shared learning for other teams.

Usage:
    python run_eval.py
    APP_URL=http://localhost:8000 EVAL_THRESHOLD=0.9 python run_eval.py

Exit code 0 = passed threshold. Exit code 1 = below threshold (suitable
for gating a CI/CD pipeline before a deploy).
"""

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from eval_cases import REVIEW_CASES, VERIFY_CASES

HERE = Path(__file__).resolve().parent
CONFIG_PATH = HERE / "eval_config.json"
HISTORY_PATH = HERE / "eval_history.jsonl"
INCIDENTS_DIR = HERE.parent / "community-of-practice" / "incidents"


def load_config() -> dict:
    cfg = {"threshold": 0.9, "app_url": "http://localhost:8000"}
    if CONFIG_PATH.exists():
        cfg.update(json.loads(CONFIG_PATH.read_text(encoding="utf-8")))
    cfg["app_url"] = os.environ.get("APP_URL", cfg["app_url"])
    cfg["threshold"] = float(os.environ.get("EVAL_THRESHOLD", cfg["threshold"]))
    return cfg


def call(base_url: str, method: str, path: str, body: dict | None = None) -> dict:
    url = base_url.rstrip("/") + path
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {"Content-Type": "application/json"} if data is not None else {}
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def run_verify_cases(base_url: str) -> list[dict]:
    results = []
    for case in VERIFY_CASES:
        try:
            resp = call(base_url, "POST", "/api/verify", case["input"])
            passed = bool(case["check"](resp))
            results.append(
                {"id": case["id"], "kind": "verify", "passed": passed, "why": case["why"], "response": resp}
            )
        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as e:
            results.append({"id": case["id"], "kind": "verify", "passed": False, "why": case["why"], "error": str(e)})
    return results


def run_review_cases(base_url: str) -> list[dict]:
    if not REVIEW_CASES:
        return []
    results = []
    try:
        call(base_url, "POST", "/api/admin/reset")
        id_map = {}
        for case in REVIEW_CASES:
            reg = call(base_url, "POST", "/api/register", case["registration"])
            id_map[case["id"]] = reg["id"]
        review = call(base_url, "POST", "/api/admin/review", {"mode": "hardened"})
        by_id = {r["id"]: r for r in (review.get("results") or [])}
        for case in REVIEW_CASES:
            r = by_id.get(id_map[case["id"]])
            try:
                passed = bool(r and case["check"](r))
                results.append(
                    {"id": case["id"], "kind": "review", "passed": passed, "why": case["why"], "response": r}
                )
            except Exception as e:
                results.append(
                    {"id": case["id"], "kind": "review", "passed": False, "why": case["why"], "error": str(e)}
                )
    finally:
        try:
            call(base_url, "POST", "/api/admin/reset")
        except Exception:
            pass
    return results


def file_incident(cfg: dict, score: float, results: list[dict]) -> Path:
    INCIDENTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc)
    incident_id = "INC-" + ts.strftime("%Y%m%d-%H%M%S") + "-eval-regression"
    failing = [r for r in results if not r["passed"]]

    lines = [
        "---",
        f"incident_id: {incident_id}",
        f"date: {ts.strftime('%Y-%m-%d')}",
        "severity: high",
        "team: (fill in — which team owns the failing endpoint)",
        "system: SecureBank verification / review assistants",
        "detected_by: automated eval regression (governance/evals/run_eval.py)",
        "status: needs-triage",
        f"summary: Eval score {score:.0%} fell below the {cfg['threshold']:.0%} threshold ({len(failing)} case(s) failing).",
        "---",
        "",
        "## What happened",
        "",
        f"The eval suite scored {score:.0%} against `{cfg['app_url']}`, below the",
        f"configured threshold of {cfg['threshold']:.0%}. This file was filed",
        "automatically by `governance/evals/run_eval.py` — nobody has triaged it yet.",
        "",
        "## Failing cases",
        "",
    ]
    for r in failing:
        lines.append(f"- **{r['id']}** ({r['kind']}) — {r['why']}")
        if "error" in r:
            lines.append(f"  - error: `{r['error']}`")
        else:
            lines.append(f"  - response: `{json.dumps(r.get('response'))}`")
    lines += [
        "",
        "## Root cause",
        "",
        "_(fill in during triage)_",
        "",
        "## Fix",
        "",
        "_(fill in once resolved)_",
        "",
        "## Lesson for other teams",
        "",
        "_(fill in — this is the part other teams will actually read)_",
        "",
    ]

    path = INCIDENTS_DIR / f"{incident_id}.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main() -> None:
    cfg = load_config()
    print(f"Running eval suite against {cfg['app_url']} (threshold {cfg['threshold']:.0%}) ...")
    print()

    try:
        results = run_verify_cases(cfg["app_url"]) + run_review_cases(cfg["app_url"])
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        print(f"Could not reach {cfg['app_url']}: {e}")
        print("Is the app running? (docker compose up)")
        sys.exit(2)

    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    score = passed / total if total else 0.0

    for r in results:
        mark = "PASS" if r["passed"] else "FAIL"
        print(f"  [{mark}] {r['id']}  ({r['kind']})")
        if not r["passed"]:
            print(f"         {r['why']}")
            if "error" in r:
                print(f"         error: {r['error']}")
            else:
                print(f"         response: {json.dumps(r.get('response'))}")

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "app_url": cfg["app_url"],
        "score": score,
        "passed": passed,
        "total": total,
        "threshold": cfg["threshold"],
        "results": [{"id": r["id"], "kind": r["kind"], "passed": r["passed"]} for r in results],
    }
    with HISTORY_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

    print()
    print(f"Score: {passed}/{total} = {score:.0%}   (logged to {HISTORY_PATH.name})")

    if score < cfg["threshold"]:
        print()
        print("=" * 62)
        print(" ALERT: PRODUCTION EVAL SCORE BELOW THRESHOLD")
        print(f"   score={score:.0%}   threshold={cfg['threshold']:.0%}")
        print("=" * 62)
        incident_path = file_incident(cfg, score, results)
        print(f" Draft incident auto-filed: {incident_path.relative_to(HERE.parent.parent)}")
        print(" -> fill in root cause / fix / lesson-for-other-teams, then share it.")
        sys.exit(1)

    print("PASS — eval score meets threshold.")
    sys.exit(0)


if __name__ == "__main__":
    main()
