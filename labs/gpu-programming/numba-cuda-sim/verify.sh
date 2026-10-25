#!/usr/bin/env bash
# Lab 4.2 - Numba CUDA kernels in the CPU simulator. Sandbox lab: no GPU.
# VERIFIED here: kernels in the simulator (tests, counters), precision experiments, CUDA C++ compile.
# NOT VERIFIED here: bench_gpu.py and the .cu programs need a GPU; they are only byte-compiled / compiled.
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
export NUMBA_ENABLE_CUDASIM=1
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

echo "== tests (simulator, ~15 s) =="
if ! "$PY" -m pytest -q -p no:cacheprovider test_kernels.py test_precision.py >"$tmp/pytest.log" 2>&1; then
  cat "$tmp/pytest.log"
  echo "FAIL: tests" >&2
  exit 1
fi
tail -n 1 "$tmp/pytest.log"

echo "== global loads: naive versus tiled =="
"$PY" demo.py loads | tee "$tmp/loads.txt"
grep -Eq 'tile  8: +8192 loads' "$tmp/loads.txt"
grep -Eq 'tile 16: +4096 loads' "$tmp/loads.txt"
grep -Eq 'naive  : +65536 loads' "$tmp/loads.txt"

echo "== classic errors =="
"$PY" demo.py errors | tee "$tmp/errors.txt"
grep -q 'IndexError' "$tmp/errors.txt"

echo "== precision =="
"$PY" precision.py >"$tmp/precision.txt"
grep -Eq '^n=100000 +sum=2048$' "$tmp/precision.txt"
sed -n '1,9p' "$tmp/precision.txt"

echo "== GPU branch: byte-compile only =="
"$PY" -m py_compile bench_gpu.py
echo "bench_gpu.py compiles (not run: no GPU)"

echo "== CUDA C++ compile check =="
if command -v nvcc >/dev/null 2>&1; then
  for f in reduce_matmul streams_overlap; do
    if ! nvcc -O2 -arch=sm_80 "cuda/$f.cu" -o "$tmp/$f" -Xptxas -v >"$tmp/nvcc.log" 2>&1; then
      cat "$tmp/nvcc.log"
      echo "FAIL: cuda/$f.cu does not compile" >&2
      exit 1
    fi
    grep -E 'Used [0-9]+ registers' "$tmp/nvcc.log"
  done
  echo "compiled with $(nvcc --version | tail -n 2 | head -n 1) (not run: no GPU)"
else
  echo "nvcc not installed: CUDA C++ compile check skipped"
fi
echo "OK numba-cuda-sim: kernels correct in the simulator, tiled loads = naive / tile"
