#!/usr/bin/env bash
# Lab 11.3 - sandbox check: closed-form model against a discrete-event simulation (simulated time, no wall clock).
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
"$PY" -m pytest -q -p no:cacheprovider test_throughput.py
"$PY" report.py
"$PY" sweep.py --m 200 --t-roll 2 --t-sync 0.2 --b 4 --s-l 1 --queue-cap 8 --n 12 --credits 8 --horizon 2000 | tail -3
"$PY" make_log.py   # no `| head`: a closed pipe would make Python fail with BrokenPipeError
echo "OK throughput-model"
