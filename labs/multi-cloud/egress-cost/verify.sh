#!/usr/bin/env bash
# Proves: the reference passes every test, the starter does not (the tests discriminate), the code passes
# py_compile, and prints the scenario table of scenarios.py (rates from rates.yaml, read 2026-10-24).
set -euo pipefail
cd "$(dirname "$0")"
export PYTHONDONTWRITEBYTECODE=1
PY="${PYTHON:-python3}"
"$PY" -c "import pytest, yaml" 2>/dev/null || { echo "FAIL: PYTHON needs pytest and pyyaml" >&2; exit 2; }
LOG="$(mktemp)"
trap 'rm -f "$LOG"' EXIT
"$PY" -c "import sys; [compile(open(f, encoding='utf-8').read(), f, 'exec') for f in sys.argv[1:]]" reference/egress.py starter/egress.py scenarios.py
IMPL=reference "$PY" -m pytest -q -p no:cacheprovider tests
echo "--- starter (failures expected) ---"
if IMPL=starter "$PY" -m pytest -q -p no:cacheprovider tests > "$LOG" 2>&1; then
  echo "starter passes all tests: the tests do not discriminate"; exit 1
fi
tail -1 "$LOG"
"$PY" scenarios.py
echo "ok: egress-cost reference passes, starter fails as intended"
