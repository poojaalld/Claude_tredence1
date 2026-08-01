"""Step 1 of the demo: generate real Claude outputs for a handful of golden
cases, for both prompt versions, and save them to disk.

This is kept as a separate step from the actual deep-eval grading
(test_deep_eval_loan.py) on purpose: generation costs money/time and its
result should be stable across repeated grading runs during a live demo -
you don't want to re-call Claude for the *answer* every time you just want
to re-run or tweak the *metrics*.

Reuses the same data/prompts as the parent Node app (../data,
../prompts) - same golden dataset, same two prompt versions - so this is a
direct "here's what deep eval adds on top of what we already built" step,
not a separate exercise.

Run:
    venv\\Scripts\\python generate_outputs.py
"""

import json
import os
import sys
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
GENERATION_MODEL = "claude-haiku-4-5-20251001"

APP_ROOT = Path(__file__).resolve().parent.parent
DATASET_PATH = APP_ROOT / "data" / "golden_dataset.json"
PROMPT_PATHS = {
    "v1": APP_ROOT / "prompts" / "prompt_v1.txt",
    "v2": APP_ROOT / "prompts" / "prompt_v2.txt",
}
OUTPUT_PATH = Path(__file__).resolve().parent / "generated_outputs.json"

# A small, representative slice of the golden dataset - enough to show the
# v1-vs-v2 contrast live without a long wait or a big API bill. Extend this
# list to cover the full dataset once you're comfortable with the pipeline.
DEMO_CASE_IDS = ["L001", "L002", "L003"]


def fill_template(template: str, case: dict) -> str:
    filled = template
    for key in ("salary", "existing_emi", "loan_amount", "tenure"):
        filled = filled.replace("{{" + key + "}}", str(case[key]))
    return filled


def applicant_facts(case: dict) -> str:
    return (
        f"Monthly Salary: {case['salary']}. "
        f"Existing Monthly EMI obligations: {case['existing_emi']}. "
        f"Requested Loan Amount: {case['loan_amount']}. "
        f"Requested Tenure: {case['tenure']} months."
    )


def call_claude(prompt: str) -> str:
    response = client.messages.create(
        model=GENERATION_MODEL,
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in response.content if block.type == "text")


def main():
    dataset = {c["id"]: c for c in json.loads(DATASET_PATH.read_text())}
    templates = {v: p.read_text() for v, p in PROMPT_PATHS.items()}

    records = []
    for case_id in DEMO_CASE_IDS:
        case = dataset[case_id]
        for version, template in templates.items():
            filled_prompt = fill_template(template, case)
            actual_output = call_claude(filled_prompt)
            print(f"[{case_id} / prompt {version}] -> {actual_output[:80].strip()!r}...")
            records.append(
                {
                    "id": case_id,
                    "prompt_version": version,
                    "input": filled_prompt,
                    "applicant_facts": applicant_facts(case),
                    "expected": case["expected"],
                    "actual_output": actual_output,
                }
            )

    OUTPUT_PATH.write_text(json.dumps(records, indent=2))
    print(f"\nWrote {len(records)} generated outputs to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
