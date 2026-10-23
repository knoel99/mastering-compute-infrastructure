#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
"$PY" -m pytest -q -p no:cacheprovider test_mfu.py
"$PY" mfu.py --params 7e9 --layers 32 --heads 32 --head-dim 128 --seq-len 4096 --tokens-per-step 4194304 --step-seconds 7.0 --gpus 64 --peak-tflops 989
