#!/usr/bin/env bash
# Tests, then the timeline of the synthetic incident and the post-mortem linter against that log.
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
"$PY" -m pytest -q -p no:cacheprovider test_incident.py
"$PY" timeline.py incident.log 128
"$PY" postmortem_lint.py postmortem_example.md --log incident.log --gpus 128
echo "OK incident-review"
