#!/usr/bin/env bash
# Rehearse on one machine what a JobSet does on a cluster, with the SAME torchrun flags as the manifest
# (c10d rendezvous, --nnodes, --rdzv_endpoint): two "pods" are two torchrun processes of 1 rank each (gloo, CPU).
# The restart loop below plays the role of spec.failurePolicy.maxRestarts: if any pod fails, ALL pods are
# restarted, and train.py resumes from the checkpoint. This is a simulation of the orchestration, not Kubernetes.
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
PORT="${RDZV_PORT:-29531}"
MAX_RESTARTS="${MAX_RESTARTS:-3}"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
export OMP_NUM_THREADS=1 PYTHONUNBUFFERED=1 DIE_RANK=1

attempt=0
while :; do
  rcs=()
  pids=()
  for node in 0 1; do
    timeout 120 "$PY" -m torch.distributed.run --nnodes=2 --nproc_per_node=1 --max-restarts=0 \
      --rdzv_backend=c10d --rdzv_endpoint="127.0.0.1:$((PORT + attempt))" --rdzv_id="local-$attempt" \
      train.py --steps 60 --ckpt-every 20 --ckpt-dir "$WORK/ckpt" --die-at-step 30 \
      >"$WORK/attempt$attempt.node$node.log" 2>&1 &
    pids+=($!)
  done
  for p in "${pids[@]}"; do
    if wait "$p"; then rcs+=(0); else rcs+=($?); fi
  done
  echo "attempt $attempt: exit codes of the 2 pods = ${rcs[*]}"
  grep -h -E 'world_size|injected|checkpoint|done' "$WORK"/attempt$attempt.node*.log | sed 's/^/    /'
  if [ "${rcs[0]}" = 0 ] && [ "${rcs[1]}" = 0 ]; then break; fi
  attempt=$((attempt + 1))
  if [ "$attempt" -gt "$MAX_RESTARTS" ]; then echo "FAIL: restart budget ($MAX_RESTARTS) exhausted" >&2; exit 1; fi
  echo "  -> restarting the whole set (restart $attempt of $MAX_RESTARTS)"
done
echo "RESTARTS=$attempt"
