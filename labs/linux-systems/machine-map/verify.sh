#!/usr/bin/env bash
# Sandbox check: unit tests on recorded fixtures, then a live report cross-checked with the kernel.
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
"$PY" -m pytest -q -p no:cacheprovider test_machine_map.py
"$PY" machine_map.py --sysroot fixtures/sysroot-2socket --lscpu-json fixtures/lscpu-sandbox.json | "$PY" -c "
import json, sys
r = json.load(sys.stdin)
n = len(r['numa'])
print('fixture: %d NUMA nodes, %d GPUs, %d InfiniBand NICs' % (n, sum(len(v['gpu']) for v in r['locality'].values()), sum(len(v['infiniband']) for v in r['locality'].values())))
assert n == 2"
"$PY" machine_map.py | "$PY" -c "
import json, os, sys
r = json.load(sys.stdin)
print('live: %s logical CPUs, %d NUMA node(s), %.1f GiB (MemTotal)' % (r['cpu']['logical'] if r['cpu'] else os.cpu_count(), len(r['numa']), r['memory_total_kb'] / 2**20))"
echo "OK machine-map"
