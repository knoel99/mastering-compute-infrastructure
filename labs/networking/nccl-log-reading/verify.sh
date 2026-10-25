#!/usr/bin/env bash
# Lab 7.2 - read an NCCL_DEBUG=INFO log.  Sandbox lab: all inputs are SYNTHETIC fixtures (plus one short public excerpt).
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
"$PY" -m pytest -q -p no:cacheprovider test_nccl_log.py
"$PY" nccl_log.py fixtures/healthy_2node_ib.log
"$PY" nccl_log.py fixtures/socket_fallback.log --expect socket_network | tail -2
"$PY" nccl_log.py fixtures/degraded_rail.log --expect hca_mismatch | tail -2
"$PY" nccl_log.py fixtures/hang_in_init.log --expect init_incomplete | tail -2
"$PY" nccl_log.py fixtures/public_nccl_docs.log | tail -2
echo "OK nccl-log-reading: healthy log clean, 3 broken logs diagnosed with the expected code"
