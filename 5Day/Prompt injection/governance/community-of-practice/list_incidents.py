#!/usr/bin/env python3
"""List every incident in the Community of Practice log, newest first.

This is the cross-team learning surface: any team can drop a Markdown file
into incidents/ (see INCIDENT_TEMPLATE.md) and it shows up here for
everyone else to browse — no ticketing system, no login, just files in a
folder that live in version control alongside the code they're about.

Usage:
    python list_incidents.py
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
INCIDENTS_DIR = HERE / "incidents"


def parse_frontmatter(text: str) -> dict:
    parts = text.split("---\n", 2)
    if len(parts) < 3 or parts[0].strip() != "":
        return {}
    meta = {}
    for line in parts[1].strip().splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip()
    return meta


def main():
    entries = []
    for path in sorted(INCIDENTS_DIR.glob("*.md")):
        meta = parse_frontmatter(path.read_text(encoding="utf-8"))
        entries.append(meta | {"_file": path.name})

    entries.sort(key=lambda m: m.get("date", ""), reverse=True)

    if not entries:
        print("No incidents filed yet.")
        return

    for m in entries:
        sev = m.get("severity", "?").upper()
        print(f"[{sev}] {m.get('incident_id', m['_file'])}  ({m.get('date', '?')})  status={m.get('status', '?')}")
        print(f"        team: {m.get('team', '?')}   system: {m.get('system', '?')}")
        print(f"        {m.get('summary', '(no summary)')}")
        print()

    open_count = sum(1 for m in entries if m.get("status") != "resolved")
    print(f"{len(entries)} incident(s) total — {open_count} not yet resolved.")


if __name__ == "__main__":
    main()
