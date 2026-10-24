#!/usr/bin/env bash
# Proves two things: the reference supervisor passes every test, and the starter does not (otherwise the tests
# would not discriminate). The "nodes" and the trainer are simulated (worker.py). Also lints the examples that
# cannot run here (a Slurm batch script and a Kubernetes Job): those are NOT executed by this script.
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
"$PY" -c "import pytest" 2>/dev/null || { echo "FAIL: PYTHON needs pytest" >&2; exit 2; }
IMPL=reference "$PY" -m pytest -q -p no:cacheprovider test_supervisor.py test_xid.py
log="$(mktemp)"
trap 'rm -f "$log"' EXIT
if IMPL=starter "$PY" -m pytest -q -p no:cacheprovider test_supervisor.py >"$log" 2>&1; then
  echo "starter passes all tests: the tests do not discriminate"; exit 1
fi
echo "starter (failures expected): $(tail -1 "$log")"
bash -n examples/train.sbatch
if command -v shellcheck >/dev/null; then shellcheck examples/train.sbatch; fi
"$PY" -c "import yaml,sys; [d for d in yaml.safe_load_all(open('examples/job.yaml'))]"
if command -v yamllint >/dev/null; then yamllint -d '{extends: relaxed, rules: {line-length: {max: 140}}}' examples/job.yaml; fi
"$PY" xid_triage.py fixtures/kernel_log_sample.txt | tail -1
echo "OK supervisor-loop: reference green, starter red; examples linted (not executed)"
