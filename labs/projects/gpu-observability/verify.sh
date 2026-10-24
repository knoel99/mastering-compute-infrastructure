#!/usr/bin/env bash
# Proves: the reference solution passes every test, and the starter code does not.
# Needs promtool (apt install prometheus) and a Python with pytest and pyyaml.
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
export PYTHON="$PY"
command -v "${PROMTOOL:-promtool}" >/dev/null || { echo "FAIL: promtool not found (apt install prometheus)" >&2; exit 2; }
"$PY" -c "import pytest, yaml" 2>/dev/null || { echo "FAIL: PYTHON needs pytest and pyyaml" >&2; exit 2; }
IMPL=reference "$PY" -m pytest -q -p no:cacheprovider tests
echo "--- starter (failures expected) ---"
if IMPL=starter "$PY" -m pytest -q -p no:cacheprovider tests > /tmp/go-starter.log 2>&1; then
  echo "starter passes all tests: the tests do not discriminate"; exit 1
fi
tail -1 /tmp/go-starter.log
echo "ok: reference passes, starter fails as intended"
