#!/usr/bin/env bash
# Lab 3.3 check (sandbox): build the MPI+OpenMP Jacobi solver, prove its field is independent of the
# decomposition, check the halo counters against the closed forms, run a tiny scaling study end to end.
# Timings are produced and printed, never asserted.
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
command -v mpicc >/dev/null || { echo "mpicc not found: apt-get install openmpi-bin libopenmpi-dev" >&2; exit 1; }
"$PY" -c "import numpy" 2>/dev/null || { echo "numpy missing for $PY" >&2; exit 1; }
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
mpicc -O2 -fopenmp -Wall -Wextra -o "$tmp/jacobi" jacobi.c -lm
MPI=(mpirun --oversubscribe --mca mpi_yield_when_idle 1)
if [ "$(id -u)" = 0 ]; then MPI+=(--allow-run-as-root); fi
ver="$(mpirun --version)"; echo "${ver%%$'\n'*}"

echo "--- A. same field for every decomposition (200 x 150 grid, 20 sweeps)"
: > "$tmp/runs.txt"
run() { # np threads extra-args...
  local np="$1" thr="$2"; shift 2
  OMP_NUM_THREADS="$thr" "${MPI[@]}" -np "$np" "$tmp/jacobi" --nx 200 --ny 150 --iters 20 "$@" >> "$tmp/runs.txt"
}
run 1 1
run 2 1
run 3 1
run 4 1
run 4 1 --decomp 2d
run 2 1 --decomp 2d
run 4 1 --overlap
run 4 1 --decomp 2d --overlap
run 2 2 --overlap
run 4 1 --check-every 5
echo "--- B. halo counters on a 96 x 96 grid, up to 9 ranks (oversubscribed: counters, not times)"
for spec in "1 1d" "5 1d" "8 1d" "4 2d" "6 2d" "9 2d"; do
  read -r np dec <<< "$spec"
  OMP_NUM_THREADS=1 "${MPI[@]}" -np "$np" "$tmp/jacobi" --nx 96 --ny 96 --iters 10 --decomp "$dec" >> "$tmp/runs.txt"
done
"$PY" check_jacobi.py "$tmp/runs.txt"
echo "--- C. a miniature scaling study, end to end (2 repetitions, 384 x 384 grid)"
"$PY" run_study.py --jacobi "$tmp/jacobi" --out "$tmp/study.json" --quick
"$PY" analyze_study.py "$tmp/study.json" --svg "$tmp/speedup.svg" | cut -c1-150
"$PY" - "$tmp/study.json" "$tmp/speedup.svg" <<'PYEOF'
import json, sys, xml.dom.minidom
sys.path.insert(0, ".")
import analyze_study as A
d = json.load(open(sys.argv[1]))
kinds = {(r["kind"], r["decomp"], r["p"]) for r in d["runs"]}
assert {("strong", "1d", 1), ("strong", "1d", 4), ("strong", "2d", 4), ("weak", "1d", 4), ("comm", "1d", 2)} <= kinds, kinds
t = A.table(sys.argv[1])
assert all(r["speedup"] > 0 and r["efficiency"] > 0 for r in t["strong"]) and all(r["lo"] <= r["t"] <= r["hi"] for r in t["strong"])
assert abs(A.analysis.karp_flatt(3.0, 4) - 1 / 9) < 1e-12          # (1/3 - 1/4) / (1 - 1/4)
m, lo, hi = A.median_ci([1.0, 2.0, 3.0, 4.0, 5.0])
assert (m, lo <= m <= hi) == (3.0, True)
svg = open(sys.argv[2]).read()
xml.dom.minidom.parseString(svg)                                    # well-formed
assert "#" not in svg.replace("url(#", ""), "hard-coded colour in the SVG"
print("OK study: runs, tables, Karp-Flatt, bootstrap interval and SVG are consistent")
PYEOF
echo "--- D. reproducible sums and MPI-IO (mpi4py)"
if "$PY" -c "import mpi4py" 2>/dev/null; then
  : > "$tmp/repro.txt"
  : > "$tmp/io.txt"
  for p in 1 2 3 4 5; do
    "${MPI[@]}" -np "$p" "$PY" repro_sum.py >> "$tmp/repro.txt"
    "${MPI[@]}" -np "$p" "$PY" mpiio_demo.py "$tmp/io.bin" >> "$tmp/io.txt"
  done
  "$PY" - "$tmp/repro.txt" "$tmp/io.txt" <<'PYEOF'
import re, sys
rep = open(sys.argv[1]).read()
blocked = set(re.findall(r"blocked=(\S+)", rep))
naive = set(re.findall(r"naive=(\S+)", rep))
exact = set(re.findall(r"exact=(\S+)", rep))
assert len(exact) == 1 and len(blocked) == 1, (exact, blocked)  # the fixed-order sum does not depend on p
io = set(re.findall(r"sha256=(\S+)", open(sys.argv[2]).read()))
assert len(io) == 1, io                                          # same file for 1..5 ranks
print(f"OK reproducibility: blocked sum identical for p=1..5; naive sum takes {len(naive)} distinct value(s); "
      f"MPI-IO file identical (sha256 {io.pop()}...)")
PYEOF
else
  echo "mpi4py missing for $PY: part D not run" >&2; exit 1
fi

echo "--- E. exercise helpers and hybrid layouts"
out="$("$PY" exercises/halo_sizing.py 1536 1536 4)"
case "$out" in *"1-D 4x1: 73728 bytes"*) ;; *) echo "halo_sizing: expected 73728 bytes for 1-D p=4" >&2; exit 1 ;; esac
out="$("$PY" exercises/scaling_table.py 1:100 2:51 4:27)"
case "$out" in *"0.027"*) ;; *) echo "scaling_table: expected e(4) = 0.027" >&2; exit 1 ;; esac
OMP_NUM_THREADS=1 "$PY" hybrid_compare.py --jacobi "$tmp/jacobi" --cores 4 --reps 2 --n 192 --iters 10 --misbound | tail -3
"$PY" compare_variants.py --jacobi "$tmp/jacobi" --np 4 --n 192 --iters 10 --reps 2 | tail -3
if command -v shellcheck > /dev/null; then
  shellcheck verify.sh slurm_launch.sh slurm_hybrid.sbatch exercises/slurm_hybrid_2nodes.sbatch
  echo "shellcheck: clean"
else
  echo "shellcheck not installed: running bash -n only"
  bash -n verify.sh; bash -n slurm_launch.sh; bash -n slurm_hybrid.sbatch; bash -n exercises/slurm_hybrid_2nodes.sbatch
fi
if [ "${RUN_SLURM:-0}" = 1 ]; then
  echo "--- F. launch through a real Slurm (RUN_SLURM=1)"
  bash slurm_launch.sh
fi
echo "OK jacobi-scaling: field independent of decomposition, counters match formulas, study pipeline runs"
