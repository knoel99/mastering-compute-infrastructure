#!/usr/bin/env bash
# Proves: the reference passes every test, the starter does not (the tests discriminate), and the scenario scan
# meets its STRUCTURAL criterion (no wall-clock timing is asserted; draws are seeded, so the output is reproducible).
set -euo pipefail
cd "$(dirname "$0")"
export PYTHONDONTWRITEBYTECODE=1
PY="${PYTHON:-python3}"
"$PY" -c "import pytest" 2>/dev/null || { echo "FAIL: PYTHON needs pytest" >&2; exit 2; }
LOG="$(mktemp)"
trap 'rm -f "$LOG"' EXIT
"$PY" -c "import sys; [compile(open(f, encoding='utf-8').read(), f, 'exec') for f in sys.argv[1:]]" \
  reference/placement.py starter/placement.py scenarios.py threshold.py
IMPL=reference "$PY" -m pytest -q -p no:cacheprovider tests
echo "--- starter (failures expected) ---"
if IMPL=starter "$PY" -m pytest -q -p no:cacheprovider tests > "$LOG" 2>&1; then
  echo "starter passes all tests: the tests do not discriminate"; exit 1
fi
tail -1 "$LOG"
echo "--- scenario scan (reference, 100 seeds) ---"
"$PY" scenarios.py --seeds 100 | tee "$LOG" | tail -9
grep -q '^CRITERION .*: OK$' "$LOG" || { echo "FAIL: scenario criterion not met" >&2; exit 1; }
echo "--- switching threshold of 'aware' (example 5.2) ---"
"$PY" threshold.py | tee "$LOG"
grep -q '^CRITERION .*: OK$' "$LOG" || { echo "FAIL: threshold criterion not met" >&2; exit 1; }
echo "ok: cost-aware-placement reference passes, starter fails as intended"
