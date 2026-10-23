#!/usr/bin/env bash
# Sandbox check: 4 gloo processes on CPU, measure all-reduce, fit alpha-beta, assert the fit is usable.
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
tmp="$(mktemp -d)"
TORCHRUN=("$PY" -m torch.distributed.run)
OMP_NUM_THREADS=1 "${TORCHRUN[@]}" --nproc_per_node=4 bench_allreduce.py --max-exp 20 --repeat 9 --out "$tmp/allreduce.json" >/dev/null 2>"$tmp/err.log" || { cat "$tmp/err.log"; exit 1; }
"$PY" fit_alpha_beta.py "$tmp/allreduce.json" --out "$tmp/fit.json"
"$PY" - "$tmp/fit.json" <<'PYEOF'
import json, sys
r = json.load(open(sys.argv[1]))
assert r["alpha_s"] > 0 and r["B_bytes_per_s"] > 0, "fitted parameters must be positive"
assert r["median_rel_error_fit_range"] < 0.6, "linear alpha-beta model should explain the large-message regime"
print("OK alpha-beta fit usable: median relative error %.0f%%" % (100 * r["median_rel_error_fit_range"]))
PYEOF
