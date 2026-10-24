#!/usr/bin/env bash
# Tests of the ADR linter, then the linter on the example and its refusal of the blank template.
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
"$PY" -m pytest -q -p no:cacheprovider test_adr_lint.py
"$PY" adr_lint.py example_adr.md
if "$PY" adr_lint.py adr_template.md >/dev/null; then echo "FAIL: the blank template must not pass" >&2; exit 1; fi
echo "the blank template is refused, as it should be"
"$PY" adr_lint.py solutions/adr_jupyterhub.md
echo "OK rfc-template"
