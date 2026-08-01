"""Runs the same 3 metrics as test_deep_eval_loan.py, but instead of printing
DeepEval's console table, writes the results straight to a CSV - handy for
dropping into a slide, a spreadsheet, or handing to participants.

Run:
    venv\\Scripts\\python export_results_csv.py

Produces: results.csv (one row per test case x metric, i.e. 6 cases x 3
metrics = 18 rows), plus a per-case overall pass/fail column.
"""

import csv
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()

from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric, GEval
from deepeval.test_case import LLMTestCase, SingleTurnParams

from claude_model import ClaudeJudge

GENERATED_OUTPUTS_PATH = Path(__file__).resolve().parent / "generated_outputs.json"
OUTPUT_CSV_PATH = Path(__file__).resolve().parent / "results.csv"

judge = ClaudeJudge(model_name="claude-haiku-4-5-20251001")

correctness_metric = GEval(
    name="Loan Decision Correctness",
    criteria=(
        "Determine whether the ACTUAL_OUTPUT's loan decision (Approve or Reject) matches the "
        "EXPECTED_OUTPUT's decision, AND whether the stated reason is logically consistent with "
        "this rule: total monthly EMI obligations (existing + new loan) must not exceed 50% of "
        "monthly salary. A response that reaches the right decision through flawed or "
        "unsupported reasoning should score lower than one that reaches it correctly."
    ),
    evaluation_params=[SingleTurnParams.INPUT, SingleTurnParams.ACTUAL_OUTPUT, SingleTurnParams.EXPECTED_OUTPUT],
    model=judge,
    threshold=0.7,
)
faithfulness_metric = FaithfulnessMetric(model=judge, threshold=0.7)
relevancy_metric = AnswerRelevancyMetric(model=judge, threshold=0.7)

METRICS = [correctness_metric, faithfulness_metric, relevancy_metric]


def main():
    records = json.loads(GENERATED_OUTPUTS_PATH.read_text(encoding="utf-8"))

    rows = []
    for record in records:
        test_case = LLMTestCase(
            input=record["input"],
            actual_output=record["actual_output"],
            expected_output=f"Decision: {record['expected']}",
            retrieval_context=[record["applicant_facts"]],
        )

        case_results = []
        for metric in METRICS:
            metric.measure(test_case)
            case_results.append(
                {
                    "case_id": record["id"],
                    "prompt_version": record["prompt_version"],
                    "expected_decision": record["expected"],
                    "metric": metric.__name__,
                    "score": round(metric.score, 2) if metric.score is not None else None,
                    "threshold": metric.threshold,
                    "status": "PASS" if metric.success else "FAIL",
                    "reason": (metric.reason or "").replace("\n", " ").strip(),
                }
            )
            print(f"[{record['id']} / {record['prompt_version']}] {metric.__class__.__name__}: "
                  f"{metric.score:.2f} ({'PASS' if metric.success else 'FAIL'})")

        overall_status = "PASS" if all(r["status"] == "PASS" for r in case_results) else "FAIL"
        for r in case_results:
            r["overall_case_status"] = overall_status
        rows.extend(case_results)

    fieldnames = [
        "case_id",
        "prompt_version",
        "expected_decision",
        "metric",
        "score",
        "threshold",
        "status",
        "overall_case_status",
        "reason",
    ]
    with open(OUTPUT_CSV_PATH, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nWrote {len(rows)} rows to {OUTPUT_CSV_PATH}")


if __name__ == "__main__":
    main()
