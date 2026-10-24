#!/usr/bin/env bash
# Proves: the reference passes every test, the starter does not (so the tests discriminate),
# and prints the success criterion (break-even utilization of the owned option vs on-demand).
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
"$PY" -c "import pytest, yaml" 2>/dev/null || { echo "FAIL: PYTHON needs pytest and pyyaml" >&2; exit 2; }
LOG="$(mktemp)"; trap 'rm -f "$LOG"' EXIT
IMPL=reference "$PY" -m pytest -q -p no:cacheprovider tests
echo "--- starter (failures expected) ---"
if IMPL=starter "$PY" -m pytest -q -p no:cacheprovider tests > "$LOG" 2>&1; then
  echo "starter passes all tests: the tests do not discriminate"; exit 1
fi
tail -1 "$LOG"
"$PY" reference/tco.py assumptions.yaml --breakeven | grep -E 'breakeven owned vs (on_demand|spot)|yearly cost per GPU'
"$PY" decision_matrix.py
echo "ok: tco-model reference passes, starter fails as intended"
