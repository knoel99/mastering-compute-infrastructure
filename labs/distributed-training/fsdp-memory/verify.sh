#!/usr/bin/env bash
# Sandbox check of lab 9.2: per-rank memory of DDP and FSDP2 (fully_shard) on 4 gloo processes, CPU only.
# Honours $PYTHON (needs torch CPU >= 2.6 for fully_shard, pytest). Takes about 45 s on 4 vCPUs.
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1  # keep the lab directory free of __pycache__
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
export OMP_NUM_THREADS=1 GLOO_SOCKET_IFNAME=lo
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
run4() { "$PY" -m torch.distributed.run --standalone --nproc_per_node=4 "$@" 2>"$tmp/err.log" >/dev/null || { cat "$tmp/err.log"; exit 1; }; }

"$PY" -m pytest -q -p no:cacheprovider test_predict.py
run4 fsdp_memory.py --mode ddp --out "$tmp/ddp.json"
run4 fsdp_memory.py --mode fsdp --out "$tmp/fsdp.json"
run4 fsdp_memory.py --mode fsdp --no-reshard --out "$tmp/fsdp_nr.json"
run4 equivalence.py "$tmp/eq.json"
"$PY" check_memory.py "$tmp"
