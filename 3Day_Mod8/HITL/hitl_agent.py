"""HITL (Human-in-the-Loop) lab.

An agent with three tools:
  - list_files   (read-only, executes automatically)
  - archive_file (reversible - moves a file into sandbox_files/archive/)
  - delete_file  (IRREVERSIBLE - permanently removes a file)

Whenever Claude requests a tool marked irreversible, the agent pauses the
loop and asks a human on the console to approve or deny it before the tool
actually runs. Reversible/read-only tools execute without asking.

Run:
    venv\\Scripts\\python hitl_agent.py
"""

import json
import os
import shutil
import sys
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

MODEL = "claude-sonnet-5"

SANDBOX_DIR = Path(__file__).parent / "sandbox_files"
ARCHIVE_DIR = SANDBOX_DIR / "archive"

# Tools that must NOT run without explicit human sign-off.
IRREVERSIBLE_TOOLS = {"delete_file"}


def seed_sandbox():
    """Create a demo sandbox with a few throwaway files, if not already present."""
    SANDBOX_DIR.mkdir(exist_ok=True)
    ARCHIVE_DIR.mkdir(exist_ok=True)
    demo_files = {
        "draft_report.txt": "Q3 draft report - not yet reviewed.\n",
        "old_meeting_notes.txt": "Notes from the 2025-01-10 sync. Superseded.\n",
        "customer_list_backup.csv": "id,name\n1,Acme Corp\n2,Globex\n",
    }
    for name, content in demo_files.items():
        path = SANDBOX_DIR / name
        if not path.exists():
            path.write_text(content)


TOOLS = [
    {
        "name": "list_files",
        "description": "List files currently in the sandbox directory.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "archive_file",
        "description": "Move a file into the archive/ subfolder. Reversible - the file is kept, just relocated.",
        "input_schema": {
            "type": "object",
            "properties": {"filename": {"type": "string", "description": "Name of the file to archive"}},
            "required": ["filename"],
        },
    },
    {
        "name": "delete_file",
        "description": "Permanently delete a file from the sandbox. IRREVERSIBLE - the file cannot be recovered afterwards.",
        "input_schema": {
            "type": "object",
            "properties": {"filename": {"type": "string", "description": "Name of the file to delete"}},
            "required": ["filename"],
        },
    },
]


def tool_list_files(_input):
    files = sorted(p.name for p in SANDBOX_DIR.iterdir() if p.is_file())
    return {"files": files}


def tool_archive_file(tool_input):
    filename = tool_input["filename"]
    src = SANDBOX_DIR / filename
    if not src.exists():
        return {"error": f"{filename} does not exist"}
    dest = ARCHIVE_DIR / filename
    shutil.move(str(src), str(dest))
    return {"status": "archived", "filename": filename, "location": str(dest)}


def tool_delete_file(tool_input):
    filename = tool_input["filename"]
    target = SANDBOX_DIR / filename
    if not target.exists():
        return {"error": f"{filename} does not exist"}
    target.unlink()
    return {"status": "deleted", "filename": filename}


TOOL_IMPL = {
    "list_files": tool_list_files,
    "archive_file": tool_archive_file,
    "delete_file": tool_delete_file,
}


def ask_human_for_confirmation(tool_name, tool_input):
    print("\n--- HUMAN CONFIRMATION REQUIRED ---")
    print(f"The agent wants to run an IRREVERSIBLE action: {tool_name}({json.dumps(tool_input)})")
    answer = input("Approve this action? [y/N]: ").strip().lower()
    print("------------------------------------\n")
    return answer == "y"


def execute_tool(tool_name, tool_input):
    if tool_name in IRREVERSIBLE_TOOLS:
        approved = ask_human_for_confirmation(tool_name, tool_input)
        if not approved:
            return {"status": "denied_by_human", "message": "The human did not approve this action. Do not retry it without a different justification."}

    impl = TOOL_IMPL[tool_name]
    return impl(tool_input)


def run_agent(user_request: str):
    messages = [{"role": "user", "content": user_request}]

    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            tools=TOOLS,
            messages=messages,
        )

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            final_text = "".join(b.text for b in response.content if b.type == "text")
            print("\nAgent:", final_text)
            return

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue

            print(f"[tool call] {block.name}({json.dumps(block.input)})")
            result = execute_tool(block.name, block.input)
            print(f"[tool result] {result}")

            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result),
                }
            )

        messages.append({"role": "user", "content": tool_results})


if __name__ == "__main__":
    seed_sandbox()
    print(f"Sandbox ready at: {SANDBOX_DIR}")
    request = input("What should the agent do? ")
    run_agent(request)
