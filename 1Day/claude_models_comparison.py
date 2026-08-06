"""Claude model comparison — change MODEL below, re-run, compare the output.

Same prompt, same code, only the model changes. Watch the response text,
the response time, and the token counts change with it.

Setup (one-time):
    pip install anthropic python-dotenv
    Put ANTHROPIC_API_KEY=sk-ant-... in a .env file in this folder
    (or just export ANTHROPIC_API_KEY in your shell instead).

Usage:
    python claude_models_comparison.py
"""

import sys
import time

import anthropic
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")  # Windows consoles default to cp1252, which can't print every character Claude might use
load_dotenv()

# ---- Change this line, then re-run the script -----------------------
#MODEL = "claude-haiku-4-5"
#MODEL = "claude-sonnet-5"
MODEL = "claude-opus-5"
# -----------------------------------------------------------------------

PROMPT = (
    "A farmer has 17 sheep. All but 9 die. How many sheep are left? "
    "Then, in one short paragraph, explain a subtle mistake someone might "
    "make when answering this."
)

client = anthropic.Anthropic()

start = time.time()
response = client.messages.create(
    model=MODEL,
    max_tokens=1024,
    messages=[{"role": "user", "content": PROMPT}],
)
elapsed = time.time() - start

reply = "".join(block.text for block in response.content if block.type == "text")

print(f"Model:         {MODEL}")
print(f"Time taken:    {elapsed:.2f}s")
print(f"Input tokens:  {response.usage.input_tokens}")
print(f"Output tokens: {response.usage.output_tokens}")
print()
print("Response:")
print(reply)
