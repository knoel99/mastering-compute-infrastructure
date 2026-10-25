#!/usr/bin/env bash
#SBATCH --job-name=jacobi-hybrid
#SBATCH --ntasks=2
#SBATCH --cpus-per-task=2
#SBATCH --time=00:02:00
# Hybrid MPI+OpenMP job: one MPI rank per task, one OpenMP thread per CPU given to the task.
# JACOBI must point to the binary (mpicc -O2 -fopenmp -o jacobi jacobi.c -lm); MPIRUN_EXTRA may hold
# extra mpirun options (for example --allow-run-as-root in a disposable root-only container).
set -euo pipefail
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-1}"
export OMP_PROC_BIND=close OMP_PLACES=cores
echo "slurm: ntasks=${SLURM_NTASKS} cpus_per_task=${SLURM_CPUS_PER_TASK} omp_threads=${OMP_NUM_THREADS}"
# Mode 2 of the Slurm MPI guide: mpirun starts the ranks through Slurm's infrastructure inside the allocation.
# shellcheck disable=SC2086  # MPIRUN_EXTRA is meant to be word-split
mpirun ${MPIRUN_EXTRA:-} --report-bindings --map-by "slot:PE=${OMP_NUM_THREADS}" --bind-to core \
  -np "${SLURM_NTASKS}" "${JACOBI:?set JACOBI to the jacobi binary}" --nx 400 --ny 400 --iters 20
