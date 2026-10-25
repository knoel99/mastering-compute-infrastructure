#!/usr/bin/env bash
# Lab 4.3 - Triton kernels in the CPU interpreter (TRITON_INTERPRET=1). Sandbox lab: no GPU.
# VERIFIED here: correctness of the kernels, exact traffic accounting of the unfused softmax.
# NOT VERIFIED here: speed, autotune, bf16 corner cases: bench_gpu.py is only byte-compiled.
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
export TRITON_INTERPRET=1
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

"$PY" - <<'PYEOF'
import triton
print("triton", triton.__version__, "(interpreter mode)")
PYEOF

echo "== tests =="
if ! "$PY" -m pytest -q -p no:cacheprovider test_triton_kernels.py >"$tmp/pytest.log" 2>&1; then
  cat "$tmp/pytest.log"
  echo "FAIL: tests" >&2
  exit 1
fi
tail -n 1 "$tmp/pytest.log"

echo "== traffic of the unfused softmax =="
"$PY" traffic.py 4096 2048 | tee "$tmp/traffic.txt"
grep -Eq 'reads +41951232 elements' "$tmp/traffic.txt"
grep -Eq 'writes +25174016 elements' "$tmp/traffic.txt"
grep -Eq 'x4\.00[0-9]$' "$tmp/traffic.txt"

echo "== GPU branch: byte-compile only =="
"$PY" -m py_compile bench_gpu.py probe_observations.py
echo "bench_gpu.py compiles (not run: no GPU); probe_observations.py compiles (observations, nothing asserted)"
echo "OK triton-interpret: kernels correct under TRITON_INTERPRET=1, unfused/fused traffic ratio = 4.00"
