#!/usr/bin/env bash
# Lab 11.1 - sandbox check: real local Ray (CPU). Logical GPUs / eval_gpu are SIMULATED resources.
# Assertions are on values, counters and ratios, never on a duration.
# The deploy/ files are linted only (they need Slurm / Kubernetes).
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
"$PY" -m pytest -q -p no:cacheprovider test_ray_actors.py
"$PY" run_demo.py
log="$(mktemp)"
trap 'rm -f "$log"' EXIT
for demo in resources_demo.py data_demo.py train_demo.py; do
  if "$PY" "$demo" >"$log" 2>&1; then
    grep -E '^(declared|2 actors|pools placed|PACK|rows=|first batch|final metrics|OK )' "$log"
  else
    cat "$log"
    exit 1
  fi
done
if command -v shellcheck >/dev/null 2>&1; then
  shellcheck deploy/ray_slurm.sbatch
else
  bash -n deploy/ray_slurm.sbatch
fi
if command -v yamllint >/dev/null 2>&1; then
  yamllint deploy/raycluster.yaml
else
  echo "yamllint not installed: YAML parse only"
fi
"$PY" -c 'import sys, yaml; docs = list(yaml.safe_load_all(open(sys.argv[1]))); assert docs[0]["kind"] == "RayCluster"; print("yaml parsed: RayCluster, %d worker groups" % len(docs[0]["spec"]["workerGroupSpecs"]))' deploy/raycluster.yaml
echo "OK ray-actors"
