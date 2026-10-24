#!/usr/bin/env bash
# Proves: the reference solution passes every test, and the starter code does not.
# PYTHON needs pytest, pyyaml and yamllint. No GPU, no cloud account, no cluster is used.
set -euo pipefail
cd "$(dirname "$0")"
export PYTHONDONTWRITEBYTECODE=1
LOG="$(mktemp)"
trap 'rm -f "$LOG"' EXIT
PY="${PYTHON:-python3}"
export PYTHON="$PY"
"$PY" -c "import pytest, yaml, yamllint" 2>/dev/null || { echo "FAIL: PYTHON needs pytest, pyyaml and yamllint" >&2; exit 2; }
IMPL=reference "$PY" -m pytest -q -p no:cacheprovider tests
echo "--- starter (failures expected) ---"
if IMPL=starter "$PY" -m pytest -q -p no:cacheprovider tests > "$LOG" 2>&1; then
  echo "starter passes all tests: the tests do not discriminate"; exit 1
fi
tail -1 "$LOG"
(cd reference && "$PY" ablation.py --seeds 2 > /dev/null)  # smoke test only: the ablation table is not asserted
echo "ok: reference passes, starter fails as intended"
