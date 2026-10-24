#!/usr/bin/env bash
# Proves two things: the reference solution passes every test, and the starter code does not
# (otherwise the tests would not discriminate). PYTHON must point to a Python with torch (CPU).
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
export PYTHON="$PY"
"$PY" -c "import torch, pytest" 2>/dev/null || { echo "FAIL: PYTHON must point to a Python with torch (CPU) and pytest" >&2; exit 2; }
IMPL=reference "$PY" -m pytest -q -p no:cacheprovider tests
echo "--- starter (failures expected) ---"
LOG="$(mktemp)"
trap 'rm -f "$LOG"' EXIT
if IMPL=starter "$PY" -m pytest -q -p no:cacheprovider tests > "$LOG" 2>&1; then
  echo "starter passes all tests: the tests do not discriminate"; exit 1
fi
tail -1 "$LOG"
echo "ok: reference passes, starter fails as intended"
