#!/usr/bin/env bash
#SBATCH --job-name=train-70b
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=8
#SBATCH --cpus-per-task=96
#SBATCH --mem=0
#SBATCH --exclusive
#SBATCH --time=12:00:00
#SBATCH --signal=B:USR1@300
#SBATCH --requeue
#SBATCH --output=logs/%x-%j.out
# One torchrun launcher per node (srun starts 1 task per node); the first node is the rendezvous host.
# Slurm sends SIGUSR1 to this batch shell about 300 s before the time limit (B: = batch shell only).
# Without a trap, SIGUSR1 kills the shell (its default action) and the job ends early, with no resume.
# The trap requeues the job instead: Slurm stops the running step and later restarts this script with the
# same job ID, and train.py resumes from its latest periodic checkpoint (--resume-latest).
set -euo pipefail
head_node="$(scontrol show hostnames "$SLURM_JOB_NODELIST" | head -n 1)"
export OMP_NUM_THREADS=8
trap 'scontrol requeue "$SLURM_JOB_ID"' USR1
# srun runs in the background: bash only runs a trap once the foreground command has returned.
srun --kill-on-bad-exit=1 \
  torchrun --nnodes="$SLURM_NNODES" --nproc_per_node=8 \
           --rdzv_backend=c10d --rdzv_endpoint="${head_node}:29500" --rdzv_id="$SLURM_JOB_ID" \
           train.py --config config.yaml --resume-latest &
pid=$!
# `wait` returns early (status > 128) when the trapped signal arrives: keep waiting until srun is gone,
# and exit with its own status so that a crash is never reported as COMPLETED.
rc=0
while :; do
  wait "$pid" && rc=0 || rc=$?
  kill -0 "$pid" 2>/dev/null || break
done
exit "$rc"
