#!/usr/bin/env bash
# SIMULATION of what a managed-jobs controller does after a preemption: a fresh "VM" (empty local directory), the
# same "bucket" (a shared directory), and a restart that resumes from the last checkpoint. It is NOT SkyPilot and
# no cloud is involved. Three runs of the toy trainer, 200 steps each, a checkpoint every 25 steps:
#   straight : never preempted (reference result)
#   kill     : SIGKILL at step 137, no notice  -> loses the 12 steps since the checkpoint of step 125
#   term     : SIGTERM at step 137, the handler saves -> loses nothing
# Both resumed runs must end with EXACTLY the state of the straight run. No wall-clock time is measured.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
PY="${PYTHON:-python3}"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
total=200
every=25
at=137

run_job() { # name mode preempt_at_step
  local name="$1" mode="$2" preempt="$3" attempt=1 rc
  while [ "$attempt" -le 5 ]; do
    mkdir -p "$work/vm-$name-$attempt"        # a fresh VM: nothing survives except the bucket
    # the outer group silences bash's own "Killed" notice for the SIGKILLed child; the trainer's output goes to the log
    if { (cd "$work/vm-$name-$attempt" && "$PY" -B "$here/train.py" --ckpt-dir "$work/bucket-$name" \
          --total-steps "$total" --ckpt-every "$every" --attempt "$attempt" \
          --preempt-at-step "$preempt" --preempt-mode "$mode") >> "$work/log-$name" 2>&1; } 2>/dev/null; then
      return 0
    else
      rc=$?
    fi
    echo "  [$name] attempt $attempt ended with exit status $rc: fail over to a new VM"
    attempt=$((attempt + 1))
  done
  echo "FAIL: $name did not finish in 5 attempts" >&2
  return 1
}

final_state() { sed -n 's/.* done step=[0-9]* state=\([0-9]*\)$/\1/p' "$work/log-$1" | tail -1; }
resumed() { sed -n 's/.*attempt=2 resumed_from_step=\([0-9]*\)$/\1/p' "$work/log-$1" | tail -1; }

run_job straight kill 0
run_job kill kill "$at"
run_job term term "$at"

ref="$(final_state straight)"
for name in kill term; do
  got="$(final_state "$name")"
  if [ -z "$ref" ] || [ "$got" != "$ref" ]; then
    echo "FAIL: $name ended with state '$got', expected '$ref'" >&2
    exit 1
  fi
done
r_kill="$(resumed kill)"
r_term="$(resumed term)"
[ "$r_kill" -eq $(( at / every * every )) ] || { echo "FAIL: kill resumed from $r_kill" >&2; exit 1; }
[ "$r_term" -eq "$at" ] || { echo "FAIL: term resumed from $r_term" >&2; exit 1; }
echo "straight : final state $ref"
echo "kill     : resumed from step $r_kill, lost $((at - r_kill)) steps, same final state"
echo "term     : resumed from step $r_term, lost $((at - r_term)) steps, same final state"
echo "OK preemption rehearsal: resumed runs match the uninterrupted run exactly"
