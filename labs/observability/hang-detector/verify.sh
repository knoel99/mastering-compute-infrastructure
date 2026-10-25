#!/usr/bin/env bash
# Lab 14.3 check (about 30 s, no GPU): unit tests, simulated comparison/sweep, a real CPU hang caught live,
# MLflow join (part C) and OpenTelemetry spans (part D). A skipped part prints PARTIAL; STRICT=1 makes it fail.
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
out_c="$(MLFLOW_DISABLE_AGENT_HINT=1 "$PY" regress.py 2>&1 | grep -v -E "INFO mlflow")"
echo "$out_c"

echo "--- 6. traces: one OpenTelemetry span per step, written to a file (no collector, simulated timings)"
out_d="$("$PY" trace_steps.py)"
echo "$out_d"

# A skipped part is not a pass: say PARTIAL, and fail under STRICT=1.
skipped=""
case "$out_c" in *"SKIPPED part C"*) skipped="part C: pip install mlflow-skinny sqlalchemy alembic" ;; esac
case "$out_d" in *"SKIPPED part D"*) skipped="${skipped:+$skipped; }part D: pip install opentelemetry-sdk" ;; esac
if [ -n "$skipped" ]; then
  echo "PARTIAL hang-detector ($skipped)"
  [ "${STRICT:-0}" = "1" ] && exit 1
  exit 0
fi
echo "OK hang-detector"
