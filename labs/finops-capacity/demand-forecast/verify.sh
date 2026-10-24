#!/usr/bin/env bash
# Proves: the reference passes every test, the starter does not; prints the success criterion
# (committed GPUs at the critical ratio, shortage probability and saving versus all-on-demand).
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
"$PY" -c "import pytest, numpy" 2>/dev/null || { echo "FAIL: PYTHON needs pytest and numpy" >&2; exit 2; }
LOG="$(mktemp)"; trap 'rm -f "$LOG"' EXIT
IMPL=reference "$PY" -m pytest -q -p no:cacheprovider tests
echo "--- starter (failures expected) ---"
if IMPL=starter "$PY" -m pytest -q -p no:cacheprovider tests > "$LOG" 2>&1; then
  echo "starter passes all tests: the tests do not discriminate"; exit 1
fi
tail -1 "$LOG"
(cd reference && "$PY" demo.py | grep -E 'critical ratio|mean yearly cost|backtest')
echo "ok: demand-forecast reference passes, starter fails as intended"
