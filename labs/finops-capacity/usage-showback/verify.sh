#!/usr/bin/env bash
# Offline proof (no Slurm needed): the reference passes every test, the starter does not, and the report prints
# the success criterion on the SYNTHETIC trace. Live proof on a real Slurm: sudo bash verify-live.sh.
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
"$PY" -c "import pytest" 2>/dev/null || { echo "FAIL: PYTHON needs pytest" >&2; exit 2; }
LOG="$(mktemp)"; trap 'rm -f "$LOG"' EXIT
IMPL=reference "$PY" -m pytest -q -p no:cacheprovider tests
echo "--- starter (failures expected) ---"
if IMPL=starter "$PY" -m pytest -q -p no:cacheprovider tests > "$LOG" 2>&1; then
  echo "starter passes all tests: the tests do not discriminate"; exit 1
fi
tail -1 "$LOG"
"$PY" reference/showback.py fixtures/synthetic_sacct.txt --capacity 64 --rate 2.08 \
  --start 2026-09-01T00:00:00 --end 2026-09-29T00:00:00 | grep -E '^unit=|utilization|lost candidates|fleet wait'
echo "ok: usage-showback reference passes, starter fails as intended"
