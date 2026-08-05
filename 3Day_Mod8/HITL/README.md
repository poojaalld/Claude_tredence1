# ResearchAgent

## Labs

### HITL (Human-in-the-Loop) — `hitl_agent.py`

An agent with three file-management tools over a sandboxed `sandbox_files/`
folder:

- `list_files` / `archive_file` — safe/reversible, execute immediately.
- `delete_file` — marked **irreversible**. Before it runs, the script pauses
  the tool loop and asks a human on the console to approve or deny it. If
  denied, Claude is told so via the tool result and must adjust its response
  instead of the file actually being deleted.

Run:

```
venv\Scripts\python hitl_agent.py
```

Try asking it to delete a file and answering `n`, then again answering `y`,
to see both paths.

### Extended Thinking — `extended_thinking_lab.py`

Runs the same multi-rule loan-eligibility logic puzzle twice:

- **Standard**: `thinking={"type": "disabled"}` — no reasoning scratchpad.
- **Extended thinking**: `thinking={"type": "adaptive"}` with
  `output_config={"effort": "high"}` — Claude gets a scratchpad to work
  through the rules before answering.

The puzzle has one verifiably correct answer (worked out by hand in the
script's closing comparison), so you can check not just token usage but
whether each mode actually applied every rule correctly.

Run:

```
venv\Scripts\python extended_thinking_lab.py
```

Note: on the Claude 5 model family, extended thinking is configured via
`thinking.type: "adaptive"` + `output_config.effort`, not the older
`thinking.type: "enabled"` + `budget_tokens` shape.

## Original search agent

- `claude_client.py` — minimal "hello world" Messages API call.
- `search.py` — Tavily web search helper.
- `main.py` — asks a question, searches the web, and asks Claude to compare/
  cite the results.

## Setup

```
venv\Scripts\pip install -r requirements.txt
```

Requires `ANTHROPIC_API_KEY` and `TAVILY_API_KEY` in `.env`.
