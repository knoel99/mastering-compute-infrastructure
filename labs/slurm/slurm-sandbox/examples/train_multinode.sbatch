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
set -euo pipefail
head_node="$(scontrol show hostnames "$SLURM_JOB_NODELIST" | head -n 1)"
export OMP_NUM_THREADS=8
srun --kill-on-bad-exit=1 \
  torchrun --nnodes="$SLURM_NNODES" --nproc_per_node=8 \
           --rdzv_backend=c10d --rdzv_endpoint="${head_node}:29500" --rdzv_id="$SLURM_JOB_ID" \
           train.py --config config.yaml --resume-latest
