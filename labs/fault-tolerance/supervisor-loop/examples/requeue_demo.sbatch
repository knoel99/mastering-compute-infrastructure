#!/usr/bin/env bash
# Real Slurm, no GPU: the job "fails" twice by requeueing itself, to show SLURM_RESTART_COUNT and sacct Restarts.
#SBATCH --job-name=requeue-demo
#SBATCH --requeue
#SBATCH --open-mode=append
set -euo pipefail
n="${SLURM_RESTART_COUNT:-0}"
echo "job=${SLURM_JOB_ID} restart_count=${n} node=$(hostname)"
if [ "$n" -lt 2 ]; then
  echo "simulated node failure, requeueing"
  scontrol requeue "$SLURM_JOB_ID"
  exit 1
fi
echo "finished after ${n} restarts"
