#!/usr/bin/env bash
# Lab 7.3 - nccl-tests under Slurm.  GPU LAB: this script lints the batch script and tests the table parser
# on SYNTHETIC tables.  It does NOT run nccl-tests (no GPU, no multi-node cluster in the sandbox).
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"

bash -n run_all_reduce.sbatch
echo "OK bash -n run_all_reduce.sbatch"
if command -v shellcheck >/dev/null 2>&1; then
  shellcheck run_all_reduce.sbatch verify.sh
  echo "OK shellcheck"
else
  echo "NOTE shellcheck not installed: only bash -n was run on the batch script"
fi
"$PY" -m py_compile parse_nccl_tests.py make_sample.py
"$PY" -m pytest -q -p no:cacheprovider test_parse.py
"$PY" parse_nccl_tests.py fixtures/all_reduce_synthetic_ok.txt --expect-busbw 48
if "$PY" parse_nccl_tests.py fixtures/all_reduce_synthetic_degraded.txt --expect-busbw 48 >/dev/null; then
  echo "FAIL: the degraded synthetic table should be flagged" >&2
  exit 1
fi
echo "OK degraded table flagged (exit status 1 as expected)"
echo "OK nccl-tests-run (lint and parser only): the GPU run itself is NOT verified here"
