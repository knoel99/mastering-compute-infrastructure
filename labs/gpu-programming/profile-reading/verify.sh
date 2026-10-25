#!/usr/bin/env bash
# Lab 4.4 - reading a profile. Sandbox lab: CPU profile of a tiny transformer + SYNTHETIC GPU-style traces.
# VERIFIED here: the CPU profile (operator counts, FLOPs, nesting), the trace parser, the verdicts.
# NOT A MEASUREMENT of any GPU: fixtures/*.json are hand-made by make_fixture.py.
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

echo "== tests =="
if ! "$PY" -m pytest -q -p no:cacheprovider test_profile.py >"$tmp/pytest.log" 2>&1; then
  sed "/USDT/d" "$tmp/pytest.log"
  echo "FAIL: tests" >&2
  exit 1
fi
tail -n 1 "$tmp/pytest.log"

echo "== CPU profile of one training step (torch.profiler, 2 threads) =="
"$PY" profile_cpu.py --out "$tmp/trace.json" 2>"$tmp/err.log" | tee "$tmp/profile.txt"
grep -Eq 'mm\+addmm\+bmm: [0-9]+ = 3\.000 x analytic' "$tmp/profile.txt"
test -s "$tmp/trace.json"

echo "== reading the CPU trace =="
"$PY" trace_report.py "$tmp/trace.json" >"$tmp/report.txt"
sed -n '1,7p' "$tmp/report.txt"

for f in launch_bound gpu_bound transfer_bound; do
  echo "== synthetic trace: $f =="
  "$PY" trace_report.py "fixtures/$f.json" | tail -n 3
done
echo "OK profile-reading: profiler FLOPs = 3 x forward, verdicts launch/gpu/transfer-bound on the synthetic traces"
