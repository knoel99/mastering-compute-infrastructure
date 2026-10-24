#!/usr/bin/env bash
# Live proof on a REAL Slurm (single-node sandbox of the Slurm module, needs root and the apt packages listed there):
# submits jobs of two accounts with different endings, exports `sacct -X -P`, runs showback.py with --unit cpu
# (the sandbox has no GPU: CPUs stand in for GPUs) and checks our allocated hours against Slurm's own CPUTimeRAW.
#   CAPTURE=1 bash verify-live.sh   also rewrites fixtures/real_sandbox_sacct.txt (the fixture used by verify.sh)
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
SB="$HERE/../../slurm/slurm-sandbox"
PY="${PYTHON:-python3}"
[ "$(id -u)" -eq 0 ] || { echo "FAIL: needs root (the sandbox writes /etc/slurm)" >&2; exit 2; }
command -v sbatch >/dev/null || { echo "FAIL: install slurm-wlm first (see labs/slurm/slurm-sandbox)" >&2; exit 2; }
WORK="$(mktemp -d)"
cleanup() { bash "$SB/teardown.sh" >/dev/null 2>&1 || true; rm -rf "$WORK"; }
trap cleanup EXIT

cd "$WORK"   # sbatch --wrap writes slurm-<jobid>.out in the current directory: keep it out of the lab folder
bash "$SB/setup.sh" >/dev/null
for acct in teama teamb; do
  sacctmgr -i add account "$acct" parent=research >/dev/null 2>&1 || true
  sacctmgr -i add user root account="$acct" >/dev/null 2>&1 || true
done
CPUS="$(sinfo -h -o %c | head -1)"

# teama: three 2-CPU jobs (the third waits when the node has 4 CPUs); teamb: one failure, one cancellation, two short jobs
for _ in 1 2 3; do sbatch -q normal -A teama -J ta --cpus-per-task=2 --wrap='sleep 4' >/dev/null; done
sbatch -A teamb -J tb-fail --cpus-per-task=1 --wrap='sleep 3; exit 3' >/dev/null
for _ in 1 2; do sbatch -A teamb -J tb-ok --cpus-per-task=1 --wrap='sleep 3' >/dev/null; done
LONG="$(sbatch --parsable -A teamb -J tb-cancel --cpus-per-task=1 --wrap='sleep 120')"
for _ in $(seq 1 60); do [ "$(squeue -h -j "$LONG" -t RUNNING | wc -l)" -eq 1 ] && break; sleep 1; done
sleep 3
scancel "$LONG"

FIELDS=JobID,Account,User,Partition,State,Submit,Start,End,ElapsedRaw,AllocTRES,NNodes,CPUTimeRAW
for _ in $(seq 1 90); do
  [ "$(squeue -h | wc -l)" -eq 0 ] && [ "$(sacct -X -P -n --format=State | grep -Ec 'RUNNING|PENDING|COMPLETING')" -eq 0 ] && break
  sleep 1
done
sacct -X -P --format="$FIELDS" > "$WORK/trace.txt"
{ echo "# REAL capture: Slurm $(sinfo --version | cut -d' ' -f2) single-node sandbox, $CPUS CPUs, $(date -u +%F); CPUs stand in for GPUs"; cat "$WORK/trace.txt"; } > "$WORK/trace_commented.txt"
[ "${CAPTURE:-0}" = "1" ] && cp "$WORK/trace_commented.txt" "$HERE/fixtures/real_sandbox_sacct.txt"

"$PY" "$HERE/reference/showback.py" "$WORK/trace_commented.txt" --unit cpu --capacity "$CPUS" --rate 1.0 | tee "$WORK/report.txt"
"$PY" - "$WORK/trace_commented.txt" "$HERE/reference" <<'PYEOF'
import sys
sys.path.insert(0, sys.argv[2])
import showback as sb
rows = sb.parse_rows(open(sys.argv[1], encoding="utf-8"))
ours = sb.usage_by_account(rows, "cpu")
bad = 0
for acct, v in sorted(ours.items()):
    theirs = sum(float(r["CPUTimeRAW"]) for r in rows if r["Account"] == acct)
    ok = abs(v["alloc_h"] * 3600 - theirs) < 1e-6
    bad += not ok
    print("%s: showback %.0f cpu-s, sacct CPUTimeRAW %.0f cpu-s %s" % (acct, v["alloc_h"] * 3600, theirs, "OK" if ok else "MISMATCH"))
states = sorted({r["State"].split()[0] for r in rows})
print("states seen:", ",".join(states))
sys.exit(1 if bad or "FAILED" not in states or "CANCELLED" not in states else 0)
PYEOF
echo "OK live: showback matches Slurm accounting"
