#!/usr/bin/env bash
# Proves: the reference solution passes every test, and the starter code does not.
# PYTHON must point to a Python with torch (CPU), numpy and pytest.
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
export PYTHON="$PY" OMP_NUM_THREADS=1
"$PY" -c "import torch, numpy, pytest" 2>/dev/null || { echo "FAIL: PYTHON needs torch (CPU), numpy and pytest" >&2; exit 2; }
IMPL=reference "$PY" -m pytest -q -p no:cacheprovider tests
echo "--- starter (failures expected) ---"
if IMPL=starter "$PY" -m pytest -q -p no:cacheprovider tests > /tmp/ss-starter.log 2>&1; then
  echo "starter passes all tests: the tests do not discriminate"; exit 1
fi
tail -1 /tmp/ss-starter.log
echo "ok: reference passes, starter fails as intended"
