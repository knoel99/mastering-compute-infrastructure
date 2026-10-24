#!/usr/bin/env bash
# Resilient multi-node training job under Slurm (NOT executed in the course sandbox: it needs GPUs).
# Idea: Slurm requeues the job after a node failure (--requeue), the batch script restarts from its
# beginning with the same job id, and torchrun resumes from the last valid checkpoint.
#SBATCH --job-name=train
#SBATCH --nodes=4
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=8
#SBATCH --exclusive
#SBATCH --time=2-00:00:00
#SBATCH --requeue
#SBATCH --signal=B:USR1@600
#SBATCH --open-mode=append
#SBATCH --output=logs/%x-%j.out
set -euo pipefail

CKPT_DIR="${CKPT_DIR:-/shared/ckpt/${SLURM_JOB_NAME}}"
MASTER_ADDR="$(scontrol show hostnames "$SLURM_JOB_NODELIST" | head -n 1)"
echo "restart_count=${SLURM_RESTART_COUNT:-0} nodes=${SLURM_JOB_NODELIST} master=${MASTER_ADDR}"

# Slurm sends USR1 600 s before the time limit: ask the trainer to checkpoint, then requeue ourselves.
trap 'echo "USR1 received: checkpoint requested"; kill -USR1 "$TRAIN_PID" 2>/dev/null || true; wait "$TRAIN_PID" || true; scontrol requeue "$SLURM_JOB_ID"; exit 0' USR1

srun --kill-on-bad-exit=1 torchrun \
  --nnodes="$SLURM_NNODES" --nproc-per-node=8 \
  --rdzv-id="$SLURM_JOB_ID" --rdzv-backend=c10d --rdzv-endpoint="${MASTER_ADDR}:29400" \
  --max-restarts=0 \
  train.py --ckpt-dir "$CKPT_DIR" --resume latest &
TRAIN_PID=$!
wait "$TRAIN_PID"
