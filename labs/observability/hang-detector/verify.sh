#!/usr/bin/env bash
# Lab 14.3 check (about 30 s, no GPU): unit tests, simulated comparison/sweep, and a real CPU hang caught live.
# Never asserts on a duration: the real-hang part waits on events with generous bounds.
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
"$PY" -c "import torch" 2>/dev/null || { echo "needs a Python with torch (CPU build is enough) and pytest" >&2; exit 2; }

echo "--- 1. unit tests and structural claims on the simulator"
"$PY" -m pytest -q -p no:cacheprovider tests

echo "--- 2. simulated detectors: false alarms, delays (assumptions in sim.py)"
"$PY" evaluate.py

echo "--- 3. a REAL hang: two gloo ranks on CPU, rank 1 stops, the watcher alarms, stacks localise the rank"
timeout 180 "$PY" real_hang.py
echo "--- 4. drift: CUSUM against a fixed threshold (simulated series)"
"$PY" drift.py

echo "--- 5. system or model? the same metrics joined through the MLflow tracking API (SQLite backend)"
MLFLOW_DISABLE_AGENT_HINT=1 "$PY" regress.py 2>&1 | grep -v -E "INFO mlflow"
echo "OK hang-detector"
