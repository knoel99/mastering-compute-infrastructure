#!/usr/bin/env bash
# Proves: the reference planner passes every test and the starter fails them for the intended reason.
# Honours $PYTHON (needs pytest, and torch CPU for the DeviceMesh check). Takes about 10 s.
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1  # keep the lab directory free of __pycache__
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
"$PY" -c "import pytest" 2>/dev/null || { echo "FAIL: PYTHON needs pytest" >&2; exit 2; }
IMPL=reference "$PY" -m pytest -q -p no:cacheprovider tests
echo "--- starter (failures expected) ---"
LOG="$(mktemp)"
trap 'rm -f "$LOG"' EXIT
if IMPL=starter "$PY" -m pytest -q -p no:cacheprovider tests >"$LOG" 2>&1; then
  echo "starter passes all tests: the tests do not discriminate"; exit 1
fi
tail -1 "$LOG"
# the starter must fail because a feature is missing (NotImplementedError), not because of an accidental error
if grep -E "^E +[A-Za-z_.]*(Error|Exception)\b" "$LOG" | grep -v -E "NotImplementedError|AssertionError"; then
  echo "starter fails for an unintended reason (see above)"; exit 1
fi
echo "ok: reference passes, starter fails as intended"
# the scenario of chapter 5 with the reference implementation: header, at least 5 layouts, all of them fitting
IMPL=reference "$PY" scenario.py --top 5 >"$LOG"
grep -q "layouts evaluated" "$LOG"
test "$(grep -c -E '^ *[0-9]+ +[0-9]+ +[0-9]+ ' "$LOG")" -eq 5
if awk '/^ *[0-9]+ +[0-9]+ +[0-9]+ /{ if ($9 > 72.0) bad=1 } END{ exit !bad }' "$LOG"; then echo "FAIL: a listed layout exceeds 90 % of 80 GB"; exit 1; fi
head -4 "$LOG"
# mesh.py (given) against PyTorch's DeviceMesh on 4 gloo processes
export OMP_NUM_THREADS=1 GLOO_SOCKET_IFNAME=lo
"$PY" -m torch.distributed.run --standalone --nproc_per_node=4 mesh_check.py 2>"$LOG" || { cat "$LOG" >&2; exit 1; }
# the snippet of example 1.2 of the course: exact expected output
"$PY" mesh_demo.py >"$LOG"
diff - "$LOG" <<'EXPECTED'
rank 5 coords (dp, pp, cp, tp): (0, 1, 0, 1)
group dp: [5, 13]
group pp: [1, 5]
group cp: [5, 7]
group tp: [4, 5]
EXPECTED
# the snippet of example 5.1 of the course: nodes spanned by the tensor- and data-parallel groups
"$PY" placement_demo.py >"$LOG"
diff - "$LOG" <<'EXPECTED'
tp spans 1 node(s); dp spans 8 nodes
same sizes, tp outermost: tp spans 4 nodes
EXPECTED
# a real 2-way tensor-parallel MLP (column/row split, f and g operators) against the dense MLP
"$PY" -m torch.distributed.run --standalone --nproc_per_node=2 tp_mlp_check.py 2>"$LOG" || { cat "$LOG" >&2; exit 1; }
# configuration files of chapter 9: parsed and their arithmetic checked (Megatron, DeepSpeed, TorchTitan are NOT run)
"$PY" check_configs.py
echo "OK parallelism-planner"
