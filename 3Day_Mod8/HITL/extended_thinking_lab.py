"""Extended Thinking lab.

Runs the same complex analytical prompt twice against Claude:
  1. Standard mode      - no thinking, straight to an answer.
  2. Extended thinking   - Claude gets a scratchpad (budget_tokens) to reason
                           step by step before answering.

Prints both outputs side by side so you can compare depth of reasoning,
answer quality, and token usage.

Run:
    venv\\Scripts\\python extended_thinking_lab.py
"""

import os
import sys

from anthropic import Anthropic
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

MODEL = "claude-sonnet-5"

ANALYTICAL_PROMPT = """
A bank has exactly ONE commercial lending slot left this quarter. Using
ALL of the rules and applicant data below, determine which single
applicant must be approved. Show your elimination logic rule by rule,
then state the final answer as one applicant name.

Rules:
1. Debt-to-equity (D/E) must be under 1.8, UNLESS collateral coverage is
   above 90%, in which case the D/E cap does not apply.
2. An applicant with an active lawsuit can only be approved if the
   potential judgment is less than 5% of the requested loan amount.
3. Applicants in the Manufacturing or Freight sectors must show at least
   2 consecutive quarters of positive revenue growth. This rule does not
   apply to other sectors.
4. If the requested loan amount is above $1,500,000, the applicant needs
   BOTH collateral coverage above 75% AND a D/E ratio under 2.0.
5. Among all applicants who pass rules 1-4, approve the one with the
   LOWEST debt-to-equity ratio.

Applicant data:
- Acme Textiles: Manufacturing, requests $1.2M, D/E 1.9, collateral 80%,
  no lawsuit, revenue growth last 2 quarters +2%, +3%.
- Bright Foods: Food Retail, requests $900K, D/E 1.5, collateral 60%,
  no lawsuit, revenue growth last 2 quarters +1%, -1%.
- Cedar Freight: Freight, requests $2.0M, D/E 1.7, collateral 85%, active
  lawsuit with potential judgment = 3% of loan amount, revenue growth
  last 2 quarters +4%, +5%.
- Delta Robotics: Manufacturing, requests $1.8M, D/E 2.1, collateral 92%,
  no lawsuit, revenue growth last 2 quarters +6%, +7%.
- Everest Mining: Mining, requests $1.0M, D/E 1.6, collateral 70%, active
  lawsuit with potential judgment = 8% of loan amount.
"""


def run_standard():
    print("=" * 70)
    print("STANDARD MODE (no extended thinking)")
    print("=" * 70)

    response = client.messages.create(
        model=MODEL,
        max_tokens=1200,
        thinking={"type": "disabled"},
        messages=[{"role": "user", "content": ANALYTICAL_PROMPT}],
    )

    answer = "".join(b.text for b in response.content if b.type == "text")
    print(answer)
    print(f"\n[usage] {response.usage}")
    return response


def run_extended_thinking():
    print("\n" + "=" * 70)
    print("EXTENDED THINKING MODE (adaptive thinking, effort=high)")
    print("=" * 70)

    response = client.messages.create(
        model=MODEL,
        max_tokens=10000,
        thinking={"type": "adaptive"},
        output_config={"effort": "high"},
        messages=[{"role": "user", "content": ANALYTICAL_PROMPT}],
    )

    thinking_text = "".join(b.thinking for b in response.content if b.type == "thinking")
    answer = "".join(b.text for b in response.content if b.type == "text")

    print("--- Claude's reasoning trace (thinking block) ---")
    print(thinking_text if thinking_text else "(no thinking block returned)")
    print("\n--- Final answer ---")
    print(answer)
    print(f"\n[usage] {response.usage}")
    return response


if __name__ == "__main__":
    standard_response = run_standard()
    extended_response = run_extended_thinking()

    print("\n" + "=" * 70)
    print("COMPARISON")
    print("=" * 70)
    standard_thinking_tokens = standard_response.usage.output_tokens_details.thinking_tokens
    extended_thinking_tokens = extended_response.usage.output_tokens_details.thinking_tokens
    print(f"Standard   output_tokens: {standard_response.usage.output_tokens}  (thinking_tokens: {standard_thinking_tokens})")
    print(f"Extended   output_tokens: {extended_response.usage.output_tokens}  (thinking_tokens: {extended_thinking_tokens})")
    print(
        "\nCorrect answer (worked by hand): Bright Foods.\n"
        "  - Acme Textiles fails rule 1 (D/E 1.9, collateral only 80%).\n"
        "  - Everest Mining fails rule 2 (judgment 8% >= 5% of loan).\n"
        "  - Delta Robotics fails rule 4 (loan > $1.5M needs D/E < 2.0, has 2.1).\n"
        "  - Bright Foods and Cedar Freight both pass rules 1-4; rule 5 picks the\n"
        "    lower D/E ratio: Bright Foods (1.5) beats Cedar Freight (1.7).\n"
        "Check whether each mode reached 'Bright Foods' and whether it applied "
        "every rule (especially the two exception clauses in rules 1 and 4) "
        "instead of skipping straight to the obvious-looking growth story."
    )
