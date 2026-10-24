#!/usr/bin/env bash
#SBATCH --job-name=ckpt-signal
#SBATCH --cpus-per-task=1
#SBATCH --time=00:05:00
#SBATCH --signal=B:USR1@30
#SBATCH --requeue
# Slurm sends SIGUSR1 to the batch shell 30 s before the time limit (B: = batch shell only).
# The shell forwards it to the trainer, which checkpoints and exits cleanly; --requeue lets Slurm restart it.
# Slurm runs a COPY of this script from its spool directory: ${BASH_SOURCE[0]} no longer points to your
# repository. SLURM_SUBMIT_DIR is the directory sbatch was invoked from: submit from the directory of trainer.py.
set -euo pipefail
python3 "${SLURM_SUBMIT_DIR:?}/trainer.py" &
pid=$!
trap 'kill -USR1 "$pid" 2>/dev/null || true' USR1
# `wait` returns early (status > 128) when a trapped signal arrives: loop until the trainer is really gone,
# and exit with the trainer's own status so that a crash is never reported as COMPLETED.
rc=0
while :; do
  wait "$pid" && rc=0 || rc=$?
  kill -0 "$pid" 2>/dev/null || break
done
exit "$rc"
