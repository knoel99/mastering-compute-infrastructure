#!/usr/bin/env bash
# Optional part B (needs root and the Slurm sandbox of labs/slurm/slurm-sandbox; not run by verify.sh).
set -euo pipefail
cd "$(dirname "$0")"
bash ../../slurm/slurm-sandbox/setup.sh >/dev/null
trap 'bash ../../slurm/slurm-sandbox/teardown.sh >/dev/null 2>&1 || true' EXIT
out="$(mktemp -d)"
jid="$(sbatch --parsable -o "$out/demo.out" examples/requeue_demo.sbatch)"
for _ in $(seq 1 900); do  # each requeue waits ~2 minutes (Reason=BeginTime) on a default 23.11 configuration
  state="$(sacct -X -n -j "$jid" -o State%12 2>/dev/null | tr -d ' ' | head -n 1)"
  [ "$state" = "COMPLETED" ] && break
  sleep 1
done
cat "$out/demo.out"
sacct -X -j "$jid" -o JobID,State,ExitCode
scontrol show job "$jid" | grep -E 'Restarts|SubmitTime|StartTime'  # sacct has no Restarts field in 23.11
[ "$state" = "COMPLETED" ] && echo "OK slurm requeue demo: job $jid completed after $(grep -c 'simulated node failure' "$out/demo.out") requeues"
