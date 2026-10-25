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
s = r["stream"]
# timing-dependent lower bounds, loose on purpose (4-vCPU VM under 8 stress-ng hogs: worst GEMM peak seen 6.7 GFLOP/s vs 1.0)
assert s["add_gbs"] > 0.5, "STREAM add bandwidth implausibly low"
assert s["copy_gbs"] > 0.5, "STREAM copy bandwidth implausibly low"
peak = r["peak_gemm_gflops"]
assert peak > 1.0, "GEMM throughput implausibly low"
# deterministic checks: byte counts of the course (example 3.1) and the roofline algebra
assert (s["copy_bytes_per_elem"], s["add_bytes_per_elem"]) == (16, 24), "STREAM byte counts differ from the course"
assert abs(r["ridge_flop_per_byte"] - peak / s["add_gbs"]) <= 1e-9 * r["ridge_flop_per_byte"], "ridge = peak / add bandwidth"
assert r["ridge_flop_per_byte"] > 0, "ridge point must be positive"
for g in r["gemm"]:
    n = g["n"]
    assert g["flops"] == 2 * n**3 and g["ideal_bytes"] == 12 * n * n, "float32 GEMM: 2n^3 FLOP, 3n^2 x 4 B"
    assert abs(g["intensity_flop_per_byte"] - n / 6) < 1e-9, "float32 GEMM intensity is n/6"
    expected = min(peak, g["intensity_flop_per_byte"] * s["add_gbs"])
    assert abs(g["roofline_gflops"] - expected) <= 1e-9 * expected, "roofline = min(peak, I x B)"
    assert g["gflops"] <= peak * (1 + 1e-9), "the roof of the compute plateau is the best measured GEMM"
    # measured_over_roofline may exceed 1 on the memory slope (cache-resident GEMM beats the single-core DRAM roof): not asserted
print("OK roofline coherent: ridge = %.1f FLOP/byte" % r["ridge_flop_per_byte"])
PYEOF
