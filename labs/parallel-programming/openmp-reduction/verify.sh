#!/usr/bin/env bash
# Lab 3.1 check (sandbox): compile six small OpenMP programs, run them with 4 threads,
# assert results, counts and iteration->thread assignments. Never asserts a wall-clock time.
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
command -v gcc >/dev/null || { echo "gcc not found: install it (apt-get install gcc) and retry" >&2; exit 1; }
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
for prog in sum_variants false_sharing schedule_demo tasks_fib default_schedule fs_counters; do
  gcc -O2 -fopenmp -Wall -Wextra -o "$tmp/$prog" "$prog.c"
done
echo "gcc $(gcc -dumpfullversion), libgomp OpenMP _OPENMP=$(printf '#include <omp.h>\n_OPENMP\n' | gcc -fopenmp -E -x c - | tail -1)"
export OMP_NUM_THREADS=4 OMP_PROC_BIND=true OMP_PLACES=cores

# 1. sums (n = 2^22: fast; critical and atomic use a smaller n because they are slow by design)
: > "$tmp/sums.txt"
for v in serial simd reduction reduction_simd local race; do
  "$tmp/sum_variants" "$v" 4194304 3 >> "$tmp/sums.txt"
done
for v in critical atomic; do
  "$tmp/sum_variants" "$v" 200000 3 >> "$tmp/sums.txt"
done
OMP_NUM_THREADS=1 "$tmp/sum_variants" race 4194304 2 > "$tmp/race1.txt"
grep -E 'variant=(race|reduction) ' "$tmp/sums.txt" | cut -c1-150

# 2. false sharing
: > "$tmp/false_sharing.txt"
for l in packed padded private; do "$tmp/false_sharing" "$l" 8000000 3 >> "$tmp/false_sharing.txt"; done
cut -c1-170 "$tmp/false_sharing.txt"

for kind in volatile atomic; do for lay in packed padded; do "$tmp/fs_counters" "$kind" "$lay" 4000000 2 | cut -c1-140; done; done

# 3. schedules (structure on 64 iterations, imbalance on the triangular loop)
: > "$tmp/schedule.txt"
for s in static static,1 static,4 dynamic,1 dynamic,8 guided; do
  OMP_SCHEDULE="$s" "$tmp/schedule_demo" 64 uniform 2000 >> "$tmp/schedule.txt"
done
for s in static static,1; do
  OMP_SCHEDULE="$s" "$tmp/schedule_demo" 2000 triangular 8 >> "$tmp/schedule.txt"
done

# 4. tasks (fib(24); cutoff 0 = no task at all)
: > "$tmp/tasks.txt"
for c in 0 4 10 24; do "$tmp/tasks_fib" 24 "$c" >> "$tmp/tasks.txt"; done
cut -c1-130 "$tmp/tasks.txt"

"$tmp/default_schedule"
# libgomp (GCC) gives one contiguous block per thread when no schedule clause is written; the specification does not promise it
if [ "$("$tmp/default_schedule")" != "threads=4 owner=0000111122223333" ]; then
  echo "note: this OpenMP runtime does not use static blocks by default (allowed by the specification)"
fi
"$PY" check_outputs.py "$tmp"

# exercise helpers: they must agree with the C program (same rules, same numbers)
imb="$("$PY" exercises/imbalance.py 2000 4 static 16 | tail -1)"
echo "$imb"
case "$imb" in "imbalance = 1.0240;"*) ;; *) echo "exercises/imbalance.py disagrees with schedule_demo (static,16: 1.024)" >&2; exit 1 ;; esac
ls_out="$("$PY" exercises/line_sharing.py 8 56)"
echo "$ls_out"
case "$ls_out" in *"7 shared line(s)"*) ;; *) echo "exercises/line_sharing.py: expected 7 shared lines" >&2; exit 1 ;; esac
echo "OK openmp-reduction: results exact, assignments as specified, no timing asserted"
