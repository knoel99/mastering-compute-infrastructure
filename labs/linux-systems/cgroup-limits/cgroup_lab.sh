#!/usr/bin/env bash
# Memory limit (OOM kill) and CPU quota in a throw-away cgroup. Needs root.
# Works on cgroup v2 (unified) and on cgroup v1 (including hybrid hierarchies). The v1 branch is the one
# that has been executed by the author; the v2 branch follows the kernel documentation and has NOT been run.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
PY="${PYTHON:-python3}"
LIMIT_MIB=100
QUOTA_PCT=20
CG=/sys/fs/cgroup
name="mci-lab-$$"
die() { echo "FAIL: $*" >&2; exit 1; }
[ "$(id -u)" = 0 ] || die "root is required"

if [ "$(stat -fc %T "$CG")" = cgroup2fs ] && grep -qw memory "$CG/cgroup.controllers"; then
  mode=v2
elif [ -e "$CG/memory/memory.limit_in_bytes" ] && [ -d "$CG/cpu" ]; then
  mode=v1
else
  die "need cgroup v2 with the memory and cpu controllers, or a cgroup v1 memory+cpu hierarchy"
fi
echo "cgroup mode: $mode"

case "$mode" in
  v1)
    memdir="$CG/memory/$name"; cpudir="$CG/cpu/$name"
    mkdir "$memdir" "$cpudir"
    echo $((LIMIT_MIB * 1024 * 1024)) > "$memdir/memory.limit_in_bytes"
    echo 100000 > "$cpudir/cpu.cfs_period_us"
    echo $((QUOTA_PCT * 1000)) > "$cpudir/cpu.cfs_quota_us"
    join()      { echo "$BASHPID" > "$memdir/cgroup.procs"; echo "$BASHPID" > "$cpudir/cgroup.procs"; }
    oom_kills() { awk '/^oom_kill /{print $2}' "$memdir/memory.oom_control"; }
    cleanup()   { rmdir "$memdir" "$cpudir" 2>/dev/null || true; }
    ;;
  v2)
    d="$CG/$name"
    echo "+memory +cpu" > "$CG/cgroup.subtree_control" 2>/dev/null || true
    mkdir "$d"
    echo $((LIMIT_MIB * 1024 * 1024)) > "$d/memory.max"
    echo 0 > "$d/memory.swap.max"
    echo "$((QUOTA_PCT * 1000)) 100000" > "$d/cpu.max"
    join()      { echo "$BASHPID" > "$d/cgroup.procs"; }
    oom_kills() { awk '/^oom_kill /{print $2}' "$d/memory.events"; }
    cleanup()   { rmdir "$d" 2>/dev/null || true; }
    ;;
esac
trap cleanup EXIT

echo "--- memory: allocate 300 MiB in a ${LIMIT_MIB} MiB cgroup"
rc=0
( join; exec "$PY" "$here/alloc.py" ) > "$here/.alloc.out" 2>&1 || rc=$?
tail -1 "$here/.alloc.out"
kills="$(oom_kills)"
echo "exit status: $rc, oom_kill counter: $kills"
[ "$rc" = 137 ] || die "expected the allocator to be killed (status 137), got $rc"
[ "$kills" -ge 1 ] || die "the kernel did not count an OOM kill"
rm -f "$here/.alloc.out"

echo "--- cpu: a busy loop limited to ${QUOTA_PCT}% of one CPU"
share="$( ( join; exec "$PY" "$here/burn.py" 4 ) )"
echo "share of one CPU obtained: $share"
"$PY" -c "import sys; s=float(sys.argv[1]); sys.exit(0 if 0.10 <= s <= 0.35 else 1)" "$share" \
  || die "CPU share $share is outside 0.10-0.35 for a ${QUOTA_PCT}% quota"
echo "OK cgroup-limits ($mode)"
