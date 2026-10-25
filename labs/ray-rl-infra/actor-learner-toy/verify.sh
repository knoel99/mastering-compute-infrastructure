#!/usr/bin/env bash
# Lab 11.2 - sandbox check: toy actor-learner loop, deterministic simulation + real local Ray actors (CPU).
# Part A (controlled lag) is reproducible from a seed. Part B (Ray) is asserted on structure only.
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
"$PY" -m pytest -q -p no:cacheprovider test_toy.py
"$PY" report.py
echo "OK actor-learner-toy"
