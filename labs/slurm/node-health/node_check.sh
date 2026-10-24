#!/usr/bin/env bash
# Node health check run periodically by slurmd (HealthCheckProgram in slurm.conf).
# It drains the node when a check fails and resumes it when the node is healthy again,
# but ONLY if the drain reason was set by this script (never undo an operator's decision).
set -u
node="$(hostname -s)"
reasons=()

free_kb="$(df --output=avail /tmp | tail -1 | tr -d ' ')"
[ "$free_kb" -lt "${MIN_FREE_KB:-1048576}" ] && reasons+=("tmp_free_low")

# Simulated GPU error counter (a real check would read DCGM / nvidia-smi / dmesg for Xid errors)
xid_file="${FAKE_XID_FILE:-/tmp/fake_gpu_xid}"
if [ -s "$xid_file" ]; then reasons+=("gpu_xid:$(head -1 "$xid_file")"); fi

command -v python3 >/dev/null || reasons+=("missing_python3")

current_reason="$(scontrol show node "$node" | sed -n 's/.*Reason=\(.*\) \[.*/\1/p')"
state="$(scontrol show node "$node" | grep -o 'State=[A-Z+_]*' | head -1)"

if [ "${#reasons[@]}" -gt 0 ]; then
  case "$state" in
    *DRAIN*) ;;  # already drained: keep the first reason
    *) scontrol update nodename="$node" state=drain reason="health: ${reasons[*]}" ;;
  esac
  exit 1
fi

case "$current_reason" in
  health:*) scontrol update nodename="$node" state=resume ;;
esac
exit 0
