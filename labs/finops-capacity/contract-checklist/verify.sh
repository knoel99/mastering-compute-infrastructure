#!/usr/bin/env bash
# Proves: the review script agrees with the answer key on the fictional contract and on its negotiated version,
# the SLA arithmetic is right, and prints the success criterion (scores and deal-breakers).
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
"$PY" -c "import pytest, yaml" 2>/dev/null || { echo "FAIL: PYTHON needs pytest and pyyaml" >&2; exit 2; }
OUT="$(mktemp)"; trap 'rm -f "$OUT"' EXIT
"$PY" -m pytest -q -p no:cacheprovider tests
echo "--- original contract (exit status 1 expected: deal-breakers are red) ---"
rc=0; "$PY" review.py fictional_contract.md rubric.yaml > "$OUT" || rc=$?
head -3 "$OUT"
[ "$rc" -eq 1 ] || { echo "FAIL: expected exit status 1, got $rc" >&2; exit 1; }
echo "--- negotiated contract ---"
"$PY" review.py fictional_contract_negotiated.md rubric.yaml > "$OUT"
head -3 "$OUT"
echo "ok: contract-checklist agrees with the answer key"
