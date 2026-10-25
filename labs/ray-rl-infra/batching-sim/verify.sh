#!/usr/bin/env bash
# Lab 11.4 - sandbox check: static vs continuous batching, reserved vs paged KV cache (simulated time, no wall clock).
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
"$PY" test_sim.py | tail -1        # stdlib only; `python3 -m pytest -q test_sim.py` runs the same tests
"$PY" sim.py
"$PY" sim.py --sweep
echo "OK batching-sim"
