#!/usr/bin/env bash
# Lab 13.2 (kind: cluster). What this script RUNS here, without any cloud account:
#   1. lint: bash -n, shellcheck, compile of the Python files, yamllint;
#   2. the governance rules (policy_check.py) and their tests;
#   3. OPTIONAL branch: an offline parse of the YAML with the real SkyPilot code, only if a Python with `skypilot`
#      is available (SKY_PYTHON, or PYTHON itself). If not, the script says SKIPPED: it never pretends;
#   4. a local rehearsal of preemption and resume (a simulation, not SkyPilot).
# What it does NOT run: `sky jobs launch` on a real cloud, Kubernetes context or GPU. That part is unverified.
set -euo pipefail
cd "$(dirname "$0")"
export PYTHONDONTWRITEBYTECODE=1
PY="${PYTHON:-python3}"
"$PY" -c "import pytest, yaml" 2>/dev/null || { echo "FAIL: PYTHON needs pytest and pyyaml" >&2; exit 2; }

echo "--- 1. lint"
bash -n verify.sh rehearse_preemption.sh
if command -v shellcheck >/dev/null; then shellcheck verify.sh rehearse_preemption.sh; echo "shellcheck: ok"; else echo "shellcheck: not installed, SKIPPED"; fi
"$PY" -c "import sys; [compile(open(f, encoding='utf-8').read(), f, 'exec') for f in sys.argv[1:]]" \
  train.py policy_check.py parse_with_skypilot.py test_policy_check.py
if command -v yamllint >/dev/null; then yamllint -c .yamllint.yaml job.yaml dev-cluster.yaml bad-job.yaml bad-job-fixed.yaml job-eu.yaml; echo "yamllint: ok"; else echo "yamllint: not installed, SKIPPED"; fi

echo "--- 2. governance rules"
"$PY" -B policy_check.py job.yaml
"$PY" -B policy_check.py dev-cluster.yaml --kind cluster
if "$PY" -B policy_check.py job.yaml --kind cluster >/dev/null; then echo "FAIL: a managed job passed the cluster rules" >&2; exit 1; fi
if "$PY" -B policy_check.py bad-job.yaml; then echo "FAIL: bad-job.yaml passed the rules" >&2; exit 1; else echo "(bad-job.yaml refused, as intended)"; fi
FIXED="$("$PY" -B policy_check.py bad-job-fixed.yaml)"
echo "$FIXED"
case "$FIXED" in
  *"0 error(s), 1 warning(s)") ;;
  *) echo "FAIL: bad-job-fixed.yaml should give 0 errors and exactly one warning (W3)" >&2; exit 1 ;;
esac
if "$PY" -B policy_check.py job.yaml --allow-prefix aws/eu- --allow-prefix gcp/europe-; then echo "FAIL: job.yaml passed the residency rule" >&2; exit 1; else echo "(job.yaml refused for residency, as intended)"; fi
"$PY" -B policy_check.py job-eu.yaml --allow-prefix aws/eu- --allow-prefix gcp/europe-
"$PY" -m pytest -q -p no:cacheprovider test_policy_check.py

echo "--- 3. offline parse with SkyPilot (optional branch)"
SKY="${SKY_PYTHON:-$PY}"
if "$SKY" -c "import sky" 2>/dev/null; then
  "$SKY" -B parse_with_skypilot.py
else
  echo "SKIPPED: no Python with skypilot (pip install skypilot==0.14.1 in a venv, then SKY_PYTHON=/that/python)"
fi

echo "--- 4. local rehearsal of preemption and resume (simulation)"
PYTHON="$PY" bash rehearse_preemption.sh
echo "ok: skypilot-yaml offline branch passed (the cloud branch is NOT run here)"
