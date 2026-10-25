#!/usr/bin/env bash
# Sandbox check for lab 8.2. Counters only (opens, read syscalls, bytes asked, bytes from the block layer) plus one
# fio ratio with a large margin; no absolute duration is asserted. Needs fio, numpy, pytest; pyarrow and webdataset are
# used when installed (the script says so).
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
# The counters (read_bytes) and O_DIRECT need a disk-backed directory: tmpfs pages are memory, so read_bytes would stay 0.
base="${TMPDIR:-/tmp}"
case "$(stat -f -c %T "$base")" in
  tmpfs|ramfs) base="${HOME:-$PWD}"; echo "note: the temporary directory is memory-backed, lab files go to $base" ;;
  *) ;;
esac
if "$PY" -c "import pyarrow" 2>/dev/null; then echo "pyarrow: present, Parquet rows included"; else echo "pyarrow: ABSENT, Parquet rows skipped"; fi
if "$PY" -c "import webdataset" 2>/dev/null; then echo "webdataset: present, shard compatibility tested"; else echo "webdataset: ABSENT, compatibility test skipped"; fi
"$PY" -m pytest -q -p no:cacheprovider test_shard_lab.py
"$PY" run_shards.py --dir "$base" --out "$tmp/shards.json"
"$PY" fio_gap.py --dir "$base" --out "$tmp/fio.json"
"$PY" - "$tmp/shards.json" "$tmp/fio.json" <<'PYEOF'
import json, sys
s = json.load(open(sys.argv[1]))
f = json.load(open(sys.argv[2]))
def check(cond, msg):
    if not cond:
        sys.exit("FAIL: " + msg)
R = {(r["format"], r["pattern"]): r for r in s["rows"]}
n, rows = s["dataset"]["n"], s["dataset"]["rows_per_group"]
check(all(r["checksum_ok"] for r in s["rows"]), "every reader must return the checksum of the bytes it should read")
check(R[("files", "sequential")]["opens"] == n and R[("files", "random")]["opens"] == R[("files", "random")]["samples"],
      "one open per sample for the file-per-sample layout")
check(R[("tar shards", "sequential")]["opens"] == s["dataset"]["shards"], "one open per shard when reading shards")
check(R[("packed pread", "sequential")]["opens"] == 1, "one open for the packed file")
for key in [("files", "sequential"), ("tar shards", "sequential"), ("packed pread", "sequential"), ("packed pread", "random")]:
    d = R[key]["device_over_payload"]
    check(0.9 <= d <= 1.6, "%s: device/payload %.2f should be close to 1 (cold cache, no amplification)" % (key, d))
check(R[("files", "sequential")]["read_syscalls_per_sample"] >= 1.9, "a file read costs at least read + end-of-file read")
check(R[("tar shards", "sequential")]["read_syscalls_per_sample"] <= R[("files", "sequential")]["read_syscalls_per_sample"],
      "sequential shard reads must not need more read() calls per sample than file-per-sample")
mm, pr = R[("packed mmap", "random")]["device_over_payload"], R[("packed pread", "random")]["device_over_payload"]
check(mm > 1.5 * pr, "mmap random access must read around the fault: device/payload %.2f vs pread %.2f" % (mm, pr))
if ("parquet", "random") in R:
    p = R[("parquet", "random")]
    check(0.75 * rows <= p["requested_over_payload"] <= 1.25 * rows, "Parquet random access asks for a whole row group per sample")
    check(p["requested_over_payload"] > 50 * R[("packed pread", "random")]["requested_over_payload"], "row-group amplification")
check(f["gap"] > 2.0, "1 MiB reads must give clearly more bandwidth than 4 KiB reads at queue depth 1")
check(f["fit"]["median_rel_error"] < 0.6, "the alpha-beta model must explain the per-request times")
print("OK shard-format: opens files/tar/packed = %d/%d/%d; mmap random device/payload %.1f vs pread %.1f; parquet asked/payload %s; fio gap %.0fx, n_1/2 = %.0f KiB"
      % (R[("files", "sequential")]["opens"], R[("tar shards", "sequential")]["opens"], R[("packed pread", "sequential")]["opens"], mm, pr,
         "%.0f" % R[("parquet", "random")]["requested_over_payload"] if ("parquet", "random") in R else "n/a",
         f["gap"], f["fit"]["n_half_kib"]))
PYEOF
