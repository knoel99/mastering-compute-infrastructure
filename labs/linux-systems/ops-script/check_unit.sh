#!/usr/bin/env bash
# check_unit.sh UNIT_FILE...
# `systemd-analyze verify` exits 0 even when it prints warnings (an invalid value is ignored, not fatal).
# For a CI check, any output is a failure: that is what this wrapper enforces.
# Exit status: 0 all units clean, 1 at least one unit produced output, 2 usage error.
set -euo pipefail
[ $# -gt 0 ] || { echo "usage: $0 unit-file..." >&2; exit 2; }
command -v systemd-analyze >/dev/null || { echo "systemd-analyze not found" >&2; exit 1; }
rc=0
for f in "$@"; do
  out="$(systemd-analyze verify "$f" 2>&1 || true)"
  if [ -n "$out" ]; then
    printf '%s\n' "$out" >&2
    echo "FAIL: $f" >&2
    rc=1
  else
    echo "ok: $f"
  fi
done
exit "$rc"
