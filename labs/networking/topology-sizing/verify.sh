#!/usr/bin/env bash
# Lab 7.1 - fat-tree sizing.
#   Part A (always): unit tests of the calculator + comparison with published component counts.
#   Part B (needs ibsim-utils, opensm, infiniband-diags): the real OpenSM `ftree` engine on a simulated fabric.
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"

"$PY" -m pytest -q -p no:cacheprovider test_fabric.py
"$PY" fabric.py --compare
echo "OK part A: calculator tests passed and 7 of 8 published SuperPOD rows are reproduced (SU=3 differs, see published.json)"

SIM_SO=/usr/lib/x86_64-linux-gnu/umad2sim/libumad2sim.so
have_all=1
for tool in ibsim opensm ibnetdiscover ibroute ibstat; do
  if ! command -v "$tool" >/dev/null 2>&1; then have_all=0; fi
done
if [ ! -f "$SIM_SO" ]; then have_all=0; fi

if [ "$have_all" -eq 1 ]; then
  "$PY" ibsim_check.py --radix 8 --down 4 --leaves 8
  "$PY" ibsim_check.py --radix 8 --down 6 --leaves 8
  neg="$(mktemp)"
  if "$PY" ibsim_check.py --drop-link >"$neg"; then
    echo "FAIL: the degraded fabric (one cable missing) was accepted by the ftree engine" >&2
    rm -f "$neg"
    exit 1
  fi
  grep -q "not a fat-tree" "$neg"
  sed -n '1,2p' "$neg"
  rm -f "$neg"
  echo "OK part B: ftree accepted the 1:1 and 3:1 fabrics, rejected the one with a missing cable"
  echo "OK topology-sizing (parts A and B)"
else
  echo "SKIP part B: install ibsim-utils opensm infiniband-diags (Debian/Ubuntu) to run the simulated-fabric check"
  echo "OK topology-sizing (part A only)"
fi
