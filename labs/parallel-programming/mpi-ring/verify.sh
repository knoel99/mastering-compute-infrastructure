#!/usr/bin/env bash
# Lab 3.2 check (sandbox): 2 to 8 local MPI ranks (Open MPI + mpi4py). Asserts results, message/byte counters
# and deadlock behaviour. Timings are measured and printed, never asserted (the machine may be shared).
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
command -v mpirun >/dev/null || { echo "mpirun not found: apt-get install openmpi-bin libopenmpi-dev" >&2; exit 1; }
"$PY" -c "import mpi4py, numpy" 2>/dev/null || { echo "mpi4py/numpy missing for $PY: $PY -m pip install mpi4py numpy" >&2; exit 1; }
MPI=(mpirun --oversubscribe --mca mpi_yield_when_idle 1)
if [ "$(id -u)" = 0 ]; then MPI+=(--allow-run-as-root); fi
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
ver="$(mpirun --version)"
echo "${ver%%$'\n'*}, mpi4py $("$PY" -c 'import mpi4py; print(mpi4py.__version__)')"

echo "--- A. the collectives, on 4 ranks"
"${MPI[@]}" -np 4 "$PY" collectives_tour.py | tee "$tmp/tour.txt"
grep -q '^OK collectives' "$tmp/tour.txt"

echo "--- B. hand-written all-reduce vs MPI_Allreduce (n = 1200 doubles, p = 2, 3, 4, 5, 8)"
for p in 2 3 4 5 8; do
  "${MPI[@]}" -np "$p" "$PY" check_allreduce.py 1200 > "$tmp/ar$p.txt"
  grep -q "^OK allreduce p=$p" "$tmp/ar$p.txt"
  sed -n 1,3p "$tmp/ar$p.txt" | cut -c1-150
done

echo "--- C. halo exchange on 1..4 ranks must match the serial stencil bit for bit"
for p in 1 2 3 4; do
  "${MPI[@]}" -np "$p" "$PY" halo_stencil.py 203 30 > "$tmp/halo$p.txt"
  grep -q "^OK halo p=$p" "$tmp/halo$p.txt"
done
tail -3 "$tmp/halo4.txt"

echo "--- D. deadlocks (2 ranks; time-out 5 s for blocking cases, 30 s for the others; exit 124 = still blocked when it fired)"
is_ompi=0
case "$ver" in *"Open MPI"*) is_ompi=1 ;; esac
fail=0
try_mode() { # mode nbytes expected(completed|deadlock) strict(1: assert, 0: report only)
  # A deadlocked run never ends, so 5 s is enough to see it; a run that should complete gets 30 s so that a loaded
  # machine (slow python start-up) is not mistaken for a deadlock.
  local rc=0 limit=5
  if [ "$3" = completed ]; then limit=30; fi
  timeout -k 2 "$limit" "${MPI[@]}" -np 2 "$PY" deadlock_demo.py "$1" "$2" > /dev/null 2>&1 || rc=$?
  local got=completed
  if [ "$rc" -eq 124 ]; then got=deadlock; elif [ "$rc" -ne 0 ]; then got="error($rc)"; fi
  printf '  %-12s %8s bytes -> %-9s (expected %s)\n' "$1" "$2" "$got" "$3"
  if [ "$4" = 1 ] && [ "$got" != "$3" ]; then fail=1; fi
}
try_mode send_send 8 completed "$is_ompi"
try_mode send_send 2048 completed "$is_ompi"
try_mode send_send 1048576 deadlock "$is_ompi"
try_mode ssend_ssend 8 deadlock 1
try_mode recv_send 1048576 completed 1
try_mode sendrecv 1048576 completed 1
try_mode isend_recv 1048576 completed 1
if [ "$fail" -ne 0 ]; then echo "unexpected deadlock behaviour" >&2; exit 1; fi
# no rank may survive its time-out (match "<interpreter> deadlock_demo.py ..." exactly)
if ps -eo args= | awk '$2 == "deadlock_demo.py" { found = 1 } END { exit !found }'; then
  echo "a blocked rank survived the time-out" >&2; exit 1
fi

echo "--- E. alpha-beta: measure, fit, compare (informational: nothing here is asserted on time)"
"${MPI[@]}" -np 4 "$PY" bench_allreduce.py "$tmp/bench4.json" --max-exp 18 > /dev/null
"$PY" model_vs_measure.py "$tmp/bench4.json" | cut -c1-120
for k in 3 4 6; do
  "${MPI[@]}" --mca coll_tuned_use_dynamic_rules 1 --mca coll_tuned_allreduce_algorithm "$k" -np 4 \
    "$PY" bench_allreduce.py "$tmp/alg$k.json" --max-exp 18 --label "algorithm$k" > /dev/null
done
"$PY" - "$tmp" <<'PYEOF'
import json, sys
d = sys.argv[1]
print("MPI_Allreduce at 256 KiB, algorithm forced (3 recursive doubling, 4 ring, 6 Rabenseifner), p=4:")
for k in (3, 4, 6):
    rows = json.load(open(f"{d}/alg{k}.json"))["rows"]
    t = [r["seconds"] for r in rows if r["kind"] == "mpi" and r["bytes"] == 2 ** 18][0]
    assert t > 0
    print(f"  algorithm {k}: {t * 1e6:8.1f} us")
PYEOF
echo "--- F. exercise helpers (ring shift, floating point, crossover, two-level all-reduce)"
shift_mode() { # mode nbytes expected(completed|deadlock|any)
  local rc=0 limit=5
  if [ "$3" = completed ]; then limit=30; fi
  timeout -k 2 "$limit" "${MPI[@]}" -np 4 "$PY" exercises/ring_shift.py "$1" "$2" > /dev/null 2>&1 || rc=$?
  local got=completed
  if [ "$rc" -eq 124 ]; then got=deadlock; elif [ "$rc" -ne 0 ]; then got="error($rc)"; fi
  printf '  ring_shift %-9s %8s bytes on 4 ranks -> %s\n' "$1" "$2" "$got"
  if [ "$3" != "any" ] && [ "$got" != "$3" ]; then echo "unexpected: wanted $3" >&2; exit 1; fi
}
shift_mode send_recv 8 any          # may pass (eager) or not: implementation-defined
shift_mode send_recv 1048576 "$(if [ "$is_ompi" = 1 ]; then echo deadlock; else echo any; fi)"
shift_mode ssend_recv 8 deadlock
shift_mode parity 1048576 completed
shift_mode sendrecv 1048576 completed
shift_mode isend 1048576 completed
if ps -eo args= | awk '$2 == "exercises/ring_shift.py" { found = 1 } END { exit !found }'; then
  echo "a blocked rank survived the time-out" >&2; exit 1
fi
out="$("$PY" exercises/fp_assoc.py)"
case "$out" in *"equal: False"*) ;; *) echo "fp_assoc: addition should not be associative" >&2; exit 1 ;; esac
out="$("$PY" exercises/crossover.py 8 5e-6 25e9)"
printf '%s\n' "${out%%$'\n'*}"
case "$out" in *"n* = 1100000 bytes"*) ;; *) echo "crossover: expected n* = 1100000 bytes" >&2; exit 1 ;; esac
"$PY" exercises/hier_allreduce.py 14e9 8 8
out="$("$PY" exercises/hier_allreduce.py 14e9 8 1)"
case "$out" in *"ratio 1.00"*) ;; *) echo "hier_allreduce: one rank per node must give ratio 1.00" >&2; exit 1 ;; esac

echo "OK mpi-ring: collectives, ring and recursive doubling exact, counters match formulas, halo bitwise equal, deadlocks as documented"
