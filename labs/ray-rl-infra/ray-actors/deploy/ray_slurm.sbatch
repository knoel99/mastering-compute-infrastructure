#!/bin/bash
# Ray on Slurm with `ray symmetric-run` (Ray >= 2.49), after the walkthrough of the Ray documentation
# "Deploying on Slurm". LINTED (shellcheck), NOT EXECUTED: it needs a Slurm cluster with GPUs.
#SBATCH --job-name=ray-rl
#SBATCH --nodes=4
#SBATCH --exclusive
#SBATCH --tasks-per-node=1
#SBATCH --cpus-per-task=32
#SBATCH --gpus-per-task=8
#SBATCH --time=04:00:00
set -euo pipefail

port=6379
mapfile -t nodes_array < <(scontrol show hostnames "$SLURM_JOB_NODELIST")
head_node=${nodes_array[0]}
ip_head=$head_node:$port
export ip_head
echo "IP Head: $ip_head"

# Every node starts a Ray runtime; the entrypoint after `--` runs on the head node only.
srun --nodes="$SLURM_JOB_NUM_NODES" --ntasks="$SLURM_JOB_NUM_NODES" \
  ray symmetric-run \
  --address "$ip_head" \
  --min-nodes "$SLURM_JOB_NUM_NODES" \
  --num-cpus="${SLURM_CPUS_PER_TASK}" \
  --num-gpus="${SLURM_GPUS_PER_TASK}" \
  -- \
  python -u rl_driver.py
