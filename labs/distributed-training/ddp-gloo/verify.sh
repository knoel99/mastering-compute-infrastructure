#!/usr/bin/env bash
# Sandbox check of lab 9.1: DDP on 4 gloo processes (CPU) against a single process.
# Honours $PYTHON (needs torch CPU, pytest). Takes about one minute on 4 vCPUs.
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1  # keep the lab directory free of __pycache__
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
export OMP_NUM_THREADS=1 GLOO_SOCKET_IFNAME=lo
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
run4() { "$PY" -m torch.distributed.run --standalone --nproc_per_node=4 "$@" 2>"$tmp/err.log" >/dev/null || { cat "$tmp/err.log"; exit 1; }; }

"$PY" -m pytest -q -p no:cacheprovider test_buckets.py
"$PY" numerics_demo.py --check
"$PY" train.py --steps 12 --out "$tmp/single.json" >/dev/null
run4 train.py --steps 12 --hook --timing --out "$tmp/ddp.json"
run4 train.py --steps 12 --out "$tmp/ddp_repeat.json"
run4 train.py --steps 12 --bucket-cap-mb 1 --out "$tmp/ddp_cap1.json"
run4 train.py --steps 12 --uneven --out "$tmp/ddp_uneven.json"
"$PY" check_ddp.py "$tmp"

# the classic error: a parameter without gradient (exit status 1 expected, then 0 with the fix)
export TORCH_DISTRIBUTED_DEBUG=INFO
if "$PY" -m torch.distributed.run --standalone --nproc_per_node=2 unused_param_demo.py >"$tmp/unused.log" 2>&1; then
  echo "FAIL: the unused-parameter demo should have failed"; exit 1
fi
grep -q "Expected to have finished reduction in the prior iteration" "$tmp/unused.log"
grep -q "Parameters which did not receive grad for rank 0: a.weight" "$tmp/unused.log"
"$PY" -m torch.distributed.run --standalone --nproc_per_node=2 unused_param_demo.py --fix >"$tmp/fixed.log" 2>&1
grep -q "3 steps completed" "$tmp/fixed.log"
echo "OK unused-parameter error reproduced (exit status 1), then fixed with find_unused_parameters=True (exit status 0)"
