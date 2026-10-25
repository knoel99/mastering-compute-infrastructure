#!/usr/bin/env bash
# Sandbox check for lab 8.3: tests, then the benchmark, then structural assertions on its JSON output.
# No assertion on an absolute duration: only orderings with a large margin, model-versus-measure agreement
# within generous tolerances, and byte-exact round trips.
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
# O_DIRECT and the write_bytes counter need a disk-backed directory: tmpfs pages are memory.
base="${TMPDIR:-/tmp}"
case "$(stat -f -c %T "$base")" in
  tmpfs|ramfs) base="${HOME:-$PWD}"; echo "note: the temporary directory is memory-backed, lab files go to $base" ;;
  *) ;;
esac
"$PY" -m pytest -q -p no:cacheprovider test_ckpt_io.py
"$PY" bench_ckpt.py --dir "$base" --out "$tmp/result.json"
"$PY" - "$tmp/result.json" <<'PYEOF'
import json, sys
r = json.load(open(sys.argv[1]))
a, b, c = r["a"], r["b"], r["c"]
def check(cond, msg):
    if not cond:
        sys.exit("FAIL: " + msg)
check(all(x["roundtrip_ok"] for x in a["rows"]), "every checkpoint must read back byte for byte")
check(a["median_rel_error"] < 0.6, "alpha-beta must explain the fsync write times (median error < 60 %)")
big = a["rows"][-1]
check(big["atomic_s"] > 1.2 * big["buffered_s"], "fsync + rename must cost clearly more than a buffered write")
check(0.5 < big["write_bytes_per_call_over_size"] < 1.5, "write_bytes counter should be about the checkpoint size")
for case in b["cases"]:
    check(abs(case["sync"] - case["pred_sync"]) < max(0.15, 0.35 * case["pred_sync"]), "sync overhead should match the model")
    check(abs(case["async"] - case["pred_async"]) < 0.20, "async overhead should match the model within 20 points")
    check(case["async"] < 0.5 * case["sync"], "async must block much less than sync on slow storage")
check(len(c["rows"]) == 3 and all(x["aggregate_mib_s"] > 0 for x in c["rows"]), "part C must report 3 writer counts")
check(r["d"]["first_copy_s"] > 0 and r["d"]["second_copy_s"] > 0, "part D must report two copy times (informational, not asserted)")
last = b["cases"][-1]
print("OK checkpoint-io: fit B = %.0f MiB/s, error %.0f %%; sync %.1f %% vs model %.1f %%; async %.1f %% vs model %.1f %%"
      % (a["B_bytes_per_s"] / (1 << 20), 100 * a["median_rel_error"], 100 * last["sync"], 100 * last["pred_sync"],
         100 * last["async"], 100 * last["pred_async"]))
PYEOF
