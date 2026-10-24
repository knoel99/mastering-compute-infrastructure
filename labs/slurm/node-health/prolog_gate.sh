#!/usr/bin/env bash
# Slurm Prolog: runs on the node before each job. A non-zero exit drains the node and requeues the job,
# so a job never starts on a node that fails the check.
[ -s "${FAKE_XID_FILE:-/tmp/fake_gpu_xid}" ] && { echo "prolog: gpu error counter non-zero" >&2; exit 1; }
exit 0
