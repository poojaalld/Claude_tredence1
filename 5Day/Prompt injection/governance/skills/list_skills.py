#!/usr/bin/env python3
"""List every prompt-template skill in this registry, regardless of status.

This is the "SKILL.md library" — versioned, owned, reviewed prompt
templates stored as governed artifacts (frontmatter + Markdown), not as
string literals buried inside application code. Only skills with
status: approved are ever loaded by the running app (see
app/main.py::load_skill) — this script exists so a human can audit the
*whole* registry, including drafts and deprecated versions, in one glance.

Usage:
    python list_skills.py
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent


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
    columns = ("SKILL ID", "VERSION", "STATUS", "OWNER", "FILE")
    rows = [columns]
    for path in sorted(HERE.glob("*.skill.md")):
        meta = parse_frontmatter(path.read_text(encoding="utf-8"))
        rows.append(
            (
                meta.get("skill_id", "?"),
                meta.get("version", "?"),
                meta.get("status", "?"),
                meta.get("owner", "?"),
                path.name,
            )
        )

    widths = [max(len(row[i]) for row in rows) for i in range(len(columns))]

    def fmt(row):
        return "  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row))

    print(fmt(rows[0]))
    print(fmt(tuple("-" * w for w in widths)))
    for row in rows[1:]:
        print(fmt(row))

    total = len(rows) - 1
    approved = sum(1 for row in rows[1:] if row[2] == "approved")
    print()
    print(f"{total} skill(s) registered — {approved} approved for production use.")
    print("Only status=approved skills are loaded by the running app.")


if __name__ == "__main__":
    main()
