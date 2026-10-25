#!/usr/bin/env bash
# Lab 4.1 - warp and memory model. Sandbox lab: pure Python, no GPU.
# 1. the reference model passes its tests; 2. the starter FAILS them (the tests are not vacuous);
# 3. the report contains the values derived by hand in the course; 4. the CUDA C++ files compile
#    when nvcc is installed (compile only: there is no GPU here, so nothing is run).
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

echo "== reference model =="
if ! "$PY" -m pytest -q -p no:cacheprovider test_warpmodel.py >"$tmp/ref.log" 2>&1; then
  cat "$tmp/ref.log"
  echo "FAIL: reference model does not pass its tests" >&2
  exit 1
fi
tail -n 1 "$tmp/ref.log"

echo "== starter must fail =="
if WARPMODEL_MODULE=starter.warpmodel "$PY" -m pytest -q -p no:cacheprovider test_warpmodel.py >"$tmp/starter.log" 2>&1; then
  echo "FAIL: the starter passes the tests, they would not catch a wrong implementation" >&2
  exit 1
fi
tail -n 1 "$tmp/starter.log"

echo "== report =="
"$PY" warpmodel.py report | tee "$tmp/report.txt"
grep -Eq '^unit stride \(lane k reads a\[k\]\) +4 +100\.0%$' "$tmp/report.txt"
grep -Eq '^stride 32 \(column of 32-wide matrix\) +32 +12\.5%$' "$tmp/report.txt"
grep -Eq '^W=32, no padding +32$' "$tmp/report.txt"
grep -Eq '^W=32, pad 1 +1$' "$tmp/report.txt"

echo "== CUDA C++ compile check =="
if command -v nvcc >/dev/null 2>&1; then
  for f in access_patterns transpose; do
    if ! nvcc -O2 -arch=sm_80 "cuda/$f.cu" -o "$tmp/$f" -Xptxas -v >"$tmp/nvcc.log" 2>&1; then
      cat "$tmp/nvcc.log"
      echo "FAIL: cuda/$f.cu does not compile" >&2
      exit 1
    fi
    grep -E 'Used [0-9]+ registers' "$tmp/nvcc.log"
  done
  echo "compiled with $(nvcc --version | tail -n 2 | head -n 1) (not run: no GPU)"
else
  echo "nvcc not installed: CUDA C++ compile check skipped (apt install nvidia-cuda-toolkit to enable it)"
fi
echo "OK warp-memory-model: reference passes, starter fails, report values as derived in the course"
