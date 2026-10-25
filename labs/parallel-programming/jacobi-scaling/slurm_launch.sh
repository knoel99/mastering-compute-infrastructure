#!/usr/bin/env bash
# Optional part D of lab 3.3: launch the hybrid Jacobi solver through a REAL Slurm (single-node sandbox of
# module 5). Needs root, the packages of labs/slurm/slurm-sandbox and Open MPI. Run with:  bash slurm_launch.sh
# It starts the Slurm sandbox only if none is running, and stops it only if it started it.
set -euo pipefail
cd "$(dirname "$0")"
SANDBOX="$(cd ../../slurm/slurm-sandbox && pwd)"
tmp="$(mktemp -d)"
started=0
cleanup() {
  if [ "$started" = 1 ]; then bash "$SANDBOX/teardown.sh" > /dev/null 2>&1 || echo "teardown failed" >&2; fi
  rm -rf "$tmp"
}
trap cleanup EXIT
if pgrep -x slurmctld-wlm > /dev/null; then
  echo "a Slurm is already running here: using it, leaving it running"
else
  bash "$SANDBOX/setup.sh" > /dev/null
  started=1
fi
sinfo --version
mpicc -O2 -fopenmp -Wall -Wextra -o "$tmp/jacobi" jacobi.c -lm
MPIRUN_EXTRA=""
if [ "$(id -u)" = 0 ]; then MPIRUN_EXTRA="--allow-run-as-root"; fi
export JACOBI="$tmp/jacobi" MPIRUN_EXTRA

echo "--- what Slurm gives each task (the sandbox uses TaskPlugin=task/none: no CPU binding by Slurm)"
# shellcheck disable=SC2016  # the variables must be expanded by each task, not by this shell
srun -n 2 -c 2 bash -c 'echo "task=$SLURM_PROCID cpus_per_task=$SLURM_CPUS_PER_TASK affinity=$(taskset -cp $$ | sed "s/.*: //")"' | sort

echo "--- direct launch with srun (Open MPI must have been built with Slurm's PMI support)"
if srun --mpi=pmi2 -n 2 "$tmp/jacobi" --nx 100 --ny 100 --iters 5 > "$tmp/direct.out" 2>&1; then
  echo "direct launch works with this Open MPI"
elif grep -q "direct launched" "$tmp/direct.out"; then
  echo "direct launch refused by this Open MPI build, as documented: use mpirun inside the allocation (mode 2)"
else
  cat "$tmp/direct.out"; echo "direct launch failed for another reason" >&2; exit 1
fi

echo "--- sbatch: 2 tasks x 2 CPUs, mpirun inside the allocation"
sbatch --wait -o "$tmp/job.out" slurm_hybrid.sbatch > /dev/null
cat "$tmp/job.out"
grep -q "ntasks=2 cpus_per_task=2 omp_threads=2" "$tmp/job.out"
test "$(grep -c 'MCW rank' "$tmp/job.out")" -eq 2
grep -q 'rank 0 bound to socket 0\[core 0\[hwt 0\]\], socket 0\[core 1\[hwt 0\]\]' "$tmp/job.out"
# the field computed under Slurm must equal the field computed by a plain single-rank run
ref="$(OMP_NUM_THREADS=1 mpirun $MPIRUN_EXTRA -np 1 "$tmp/jacobi" --nx 400 --ny 400 --iters 20 | grep -o 'checksum=[0-9a-f]*')"
grep -q "$ref" "$tmp/job.out"
sacct -X -n -j "$(sacct -X -n -P --format=JobID | tail -1)" --format=JobName%14,State%10,AllocCPUS%9 | head -2
echo "OK slurm launch: allocation variables, bindings and field checksum ($ref) as expected"
