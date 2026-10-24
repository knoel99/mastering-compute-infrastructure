#!/usr/bin/env bash
# Little's law on a real block device: concurrency = throughput x latency.
# Runs 4 KiB random reads with O_DIRECT at queue depth 1 and 32, then checks IOPS x mean latency ~ queue depth.
# Needs fio. WORKDIR must be on a filesystem that supports O_DIRECT (not tmpfs): default /tmp on a disk.
set -euo pipefail
command -v fio >/dev/null || { echo "fio not installed: part B skipped (apt-get install fio)"; exit 0; }
PY="${PYTHON:-python3}"
work="$(mktemp -d "${WORKDIR:-/tmp}/littles-law.XXXXXX")"
trap 'rm -rf "$work"' EXIT
for qd in 1 32; do
  fio --name=ll --filename="$work/f.dat" --size=256M --rw=randread --bs=4k --direct=1 --ioengine=libaio \
      --iodepth="$qd" --runtime=3 --time_based --output-format=json > "$work/out$qd.json" 2>"$work/err$qd.log" \
    || { cat "$work/err$qd.log" >&2; echo "fio failed: is $work on a filesystem with O_DIRECT?" >&2; exit 1; }
  "$PY" - "$work/out$qd.json" "$qd" <<'PYEOF'
import json, sys
r = json.load(open(sys.argv[1]))["jobs"][0]["read"]
qd = int(sys.argv[2])
iops, lat_us = r["iops"], r["lat_ns"]["mean"] / 1000
product = iops * lat_us * 1e-6
print(f"iodepth={qd:<3} iops={iops:8.0f}  mean latency={lat_us:7.1f} us  iops x latency = {product:5.2f}")
if abs(product - qd) > 0.25 * qd:
    sys.exit(f"FAIL: iops x latency = {product:.2f}, expected about {qd}")
PYEOF
done
echo "OK littles-law"
