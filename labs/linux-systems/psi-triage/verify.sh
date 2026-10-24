#!/usr/bin/env bash
# Sandbox check: unit tests, then three REAL load patterns must each be recognised.
# Needs stress-ng and fio (apt-get install stress-ng fio) and /proc/pressure (kernel with PSI).
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
for t in stress-ng fio; do command -v "$t" >/dev/null || { echo "FAIL: $t is required (apt-get install $t)" >&2; exit 2; }; done
[ -r /proc/pressure/cpu ] || { echo "FAIL: this kernel has no PSI (/proc/pressure)" >&2; exit 2; }
"$PY" -m pytest -q -p no:cacheprovider test_triage.py
work="$(mktemp -d)"
trap 'rm -rf "$work"; jobs -p | xargs -r kill 2>/dev/null || true' EXIT  # only the jobs started here, never other users' fio or stress-ng
run() { "$PY" triage.py --seconds 4 --json; }
field() { "$PY" -c "import json,sys; d=json.load(sys.stdin); print($1)"; }

echo "--- idle"
out="$(run)"; echo "$out"
[ "$(echo "$out" | field "len(d['findings'])")" = 0 ] || { echo "machine not idle: stop other workloads and retry" >&2; exit 1; }

echo "--- CPU: two workers per core"
stress-ng --cpu $(( 2 * $(nproc) )) --timeout 8s >/dev/null 2>&1 &
sleep 1; out="$(run)"; echo "$out"; wait
echo "$out" | field "d['findings']" | grep -q "cpu: saturated" || { echo "CPU saturation not recognised" >&2; exit 1; }

echo "--- IO stall: synchronous writes with fsync"
fio --name=sync --rw=write --bs=1m --ioengine=sync --fsync=1 --runtime=8 --time_based --size=256M --filename="$work/sync.dat" >/dev/null 2>&1 &
sleep 1; out="$(run)"; echo "$out"; wait
echo "$out" | field "d['findings']" | grep -q "io: tasks are stalled" || { echo "IO stall not recognised" >&2; exit 1; }

echo "--- PSI blind spot: deep asynchronous queue, direct IO"
fio --name=aio --rw=randwrite --bs=4k --iodepth=32 --ioengine=libaio --direct=1 --runtime=8 --time_based --size=256M --filename="$work/aio.dat" >/dev/null 2>&1 &
sleep 1; out="$(run)"; echo "$out"; wait
echo "$out" | field "d['findings']" | grep -q "disk: busy, but no task stalls" || { echo "async blind spot not reproduced on this device" >&2; exit 1; }
echo "OK psi-triage"
