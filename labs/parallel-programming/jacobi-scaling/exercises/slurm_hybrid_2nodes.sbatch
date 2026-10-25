#!/usr/bin/env bash
#SBATCH --job-name=jacobi-2nodes
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=8
#SBATCH --cpus-per-task=8
#SBATCH --exclusive
#SBATCH --time=00:10:00
# LINT ONLY: this script was never run (it needs two nodes of 64 cores). Example node: 64 cores in 2 NUMA
# domains of 32; 8 ranks per node, each rank owns 8 cores inside one NUMA domain (4 ranks per domain).
# Direct launch with srun (mode 1 of the Slurm MPI guide) needs an MPI built with Slurm's PMI/PMIx support;
# otherwise replace the srun line by: mpirun --map-by "slot:PE=${SLURM_CPUS_PER_TASK}" --bind-to core ...
set -euo pipefail
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK}"
export OMP_PROC_BIND=close OMP_PLACES=cores
# --cpu-bind is documented as used only when the task/affinity plugin is enabled; ask for core binding explicitly.
srun --cpu-bind=cores "${JACOBI:?set JACOBI to the jacobi binary}" --nx 16384 --ny 16384 --iters 100 --decomp 2d
