#!/usr/bin/env bash
#SBATCH --job-name=ckpt-signal
#SBATCH --cpus-per-task=1
#SBATCH --time=00:05:00
#SBATCH --signal=B:USR1@30
#SBATCH --requeue
# Slurm sends SIGUSR1 to the batch shell 30 s before the time limit (B: = batch shell only).
# The shell forwards it to the trainer, which checkpoints and exits cleanly; --requeue lets Slurm restart it.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$here/trainer.py" &
pid=$!
trap 'kill -USR1 "$pid" 2>/dev/null || true' USR1
# `wait` returns early when a trapped signal arrives: loop until the trainer is really gone
while kill -0 "$pid" 2>/dev/null; do wait "$pid" || true; done
wait "$pid" 2>/dev/null || true
