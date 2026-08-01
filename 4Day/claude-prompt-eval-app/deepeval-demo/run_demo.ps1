# Convenience wrapper so the trainer doesn't have to remember 4 environment
# variables. See README.md for what each one is working around.
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"
$env:DEEPEVAL_TELEMETRY_OPT_OUT = "YES"
$env:DEEPEVAL_FILE_SYSTEM = "READ_ONLY"

& ".\venv\Scripts\deepeval.exe" test run test_deep_eval_loan.py
