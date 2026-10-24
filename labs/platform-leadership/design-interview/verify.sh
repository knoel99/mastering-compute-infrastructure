#!/usr/bin/env bash
# Tests of the sizing calculator, then the calculator on the interview prompt.
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
"$PY" -m pytest -q -p no:cacheprovider test_sizing.py
"$PY" sizing.py --params 70e9 --tokens 2e12 --gpus 256 --peak-tflops 989 --mfu 0.40 --bytes-per-param 14 --write-gb-s 50 --gpu-failure-rate 0.0002
echo "OK design-interview"
