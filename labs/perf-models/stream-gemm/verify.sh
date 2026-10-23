#!/usr/bin/env bash
# Sandbox check: runs the measurement at small sizes and asserts the output is coherent.
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
out="$(mktemp -d)/results.json"
"$PY" stream_gemm.py --quick --out "$out"
"$PY" - "$out" <<'PYEOF'
import json, sys
r = json.load(open(sys.argv[1]))
assert r["stream"]["add_gbs"] > 0.5, "STREAM add bandwidth implausibly low"
assert r["stream"]["copy_gbs"] > 0.5, "STREAM copy bandwidth implausibly low"
assert r["peak_gemm_gflops"] > 1.0, "GEMM throughput implausibly low"
assert r["ridge_flop_per_byte"] > 0, "ridge point must be positive"
for g in r["gemm"]:
    assert g["roofline_gflops"] > 0
    assert g["measured_over_roofline"] <= 1.0 + 1e-9, "by construction the roofline uses the best GEMM as its roof"
print("OK roofline coherent: ridge = %.1f FLOP/byte" % r["ridge_flop_per_byte"])
PYEOF
