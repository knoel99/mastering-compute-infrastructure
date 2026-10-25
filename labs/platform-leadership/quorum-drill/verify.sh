#!/usr/bin/env bash
# Lab 16.4: tests of the quorum calculator, the table of example 9.1, then the formula checked
# against a seeded Monte Carlo simulation. No timing assertion; no etcd needed.
# The optional restore drill on a real local etcd cluster is etcd_drill.sh (run it yourself, see README.md).
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
"$PY" -m pytest -q -p no:cacheprovider test_quorum.py
"$PY" quorum.py table --a 0.99 0.999 --max-members 5
"$PY" quorum.py check --trials 100000 --seed 2026
bash -n etcd_drill.sh
echo "OK quorum-drill"
