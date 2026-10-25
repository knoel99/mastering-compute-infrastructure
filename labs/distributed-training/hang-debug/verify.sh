#!/usr/bin/env bash
# Sandbox check of lab 9.3: reproduce two kinds of hang on 4 gloo processes and locate the culprit rank.
# Honours $PYTHON (needs torch CPU). Takes about 60 s; the CPU is mostly idle (ranks wait for each other).
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1  # keep the lab directory free of __pycache__
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
export OMP_NUM_THREADS=1 GLOO_SOCKET_IFNAME=lo
tmp="$(mktemp -d)"
agent=""
cleanup() {
  if [ -n "$agent" ] && kill -0 "$agent" 2>/dev/null; then kill "$agent"; fi  # only the torchrun this script started
  rm -rf "$tmp"
}
trap cleanup EXIT
run4() { "$PY" -m torch.distributed.run --standalone --nproc_per_node=4 train_hang.py "$@"; }
expect_fail() { # expect_fail LOG args...: the run must fail (a hang ends in a timeout), its output goes to LOG
  local log="$1"; shift
  if run4 "$@" >"$log" 2>&1; then echo "FAIL: this run should have failed: $*"; exit 1; fi
}

# 1. the bug as the user sees it: the loop seems to progress, then every rank times out
expect_fail "$tmp/skip.log" --bug skip --timeout 5
grep -q "rank 0 step 8 done" "$tmp/skip.log"           # steps after the bug "succeeded": silent corruption
if grep -q "rank 0 step 9 done" "$tmp/skip.log"; then echo "FAIL: step 9 should never complete"; exit 1; fi
grep -q "Timed out waiting" "$tmp/skip.log"
echo "OK 1 skip bug: loop looked healthy up to step 8, then 'Timed out waiting' on every rank"

# 2. first tool: TORCH_DISTRIBUTED_DEBUG=DETAIL checks every collective across ranks (plain collectives only)
TORCH_DISTRIBUTED_DEBUG=DETAIL expect_fail "$tmp/detail.log" --bug skip --timeout 30
grep -q "Detected mismatch between collectives on ranks" "$tmp/detail.log"
grep -q "OpType=BARRIER" "$tmp/detail.log"
echo "OK 2 DETAIL: mismatch reported at once (rank 2 in BARRIER while the others are in ALLREDUCE)"

# 3. second tool: the collective journal shows WHICH step was skipped
expect_fail "$tmp/skip_j.log" --bug skip --timeout 5 --journal-dir "$tmp/j_skip"
"$PY" analyze_journal.py "$tmp/j_skip" | tee "$tmp/skip_report.txt"
grep -q "first divergence at seq 4" "$tmp/skip_report.txt"
grep -q "rank(s) \[2\]" "$tmp/skip_report.txt"
grep -q "tag='step=5'" "$tmp/skip_report.txt"
echo "OK 3 journal: rank 2 skipped the collective of step 4 (its seq 4 is the collective of step 5)"

# 4. a rank blocked outside the collectives: journal says "nothing in flight", the Python stack says where
expect_fail "$tmp/stuck.log" --bug stuck --timeout 5 --journal-dir "$tmp/j_stuck" --stacks-dir "$tmp/stacks"
"$PY" analyze_journal.py "$tmp/j_stuck" | tee "$tmp/stuck_report.txt"
grep -q "ranks \[0, 1, 3\] wait in seq 4" "$tmp/stuck_report.txt"
grep -q "blocked outside the collectives" "$tmp/stuck_report.txt"
grep -q "all_reduce" "$tmp/stacks/rank0.txt"
grep -q "train_hang.py" "$tmp/stacks/rank2.txt"
if grep -q "all_reduce" "$tmp/stacks/rank2.txt"; then echo "FAIL: rank 2 should not be inside a collective"; exit 1; fi
echo "OK 4 stuck bug: ranks 0,1,3 wait in seq 4, rank 2 has nothing in flight; its stack is outside all_reduce"

# 4b. the production way: signal a hung job. faulthandler.register(SIGUSR1) writes the stacks even though the main thread is blocked
"$PY" -m torch.distributed.run --standalone --nproc_per_node=4 train_hang.py --bug stuck --timeout 60 \
  --stacks-dir "$tmp/stacks_usr1" --stack-after 1000 >"$tmp/usr1.log" 2>&1 &
agent=$!
for _ in $(seq 1 60); do  # wait (at most 30 s) until rank 2 reports that it is blocked
  if grep -q "blocks while loading" "$tmp/usr1.log"; then break; fi
  sleep 0.5
done
grep -q "blocks while loading" "$tmp/usr1.log"
sleep 2  # let the other ranks enter the all-reduce
for _ in $(seq 1 20); do  # signal again (a dump is appended each time) until rank 0's stack shows the collective: no timing assertion
  for pid in $(pgrep -P "$agent"); do kill -USR1 "$pid"; done  # our own torchrun's workers, found by parent PID
  sleep 0.5
  if grep -q "all_reduce" "$tmp/stacks_usr1/rank0.txt"; then break; fi
done
grep -q "all_reduce" "$tmp/stacks_usr1/rank0.txt"
grep -q "train_hang.py" "$tmp/stacks_usr1/rank2.txt"
if grep -q "all_reduce" "$tmp/stacks_usr1/rank2.txt"; then echo "FAIL: rank 2 should not be in a collective"; exit 1; fi
kill "$agent"  # stop our torchrun (it terminates its workers)
status=0
wait "$agent" || status=$?
agent=""
echo "OK 4b kill -USR1: stacks of the hung ranks written without stopping them (torchrun stopped by PID, status $status)"

# 5. monitored_barrier names the missing rank when it is placed before the collective
expect_fail "$tmp/stuck_m.log" --bug stuck --monitored --timeout 5
grep -q "Rank 2 failed to pass monitoredBarrier" "$tmp/stuck_m.log"
echo "OK 5 monitored_barrier: rank 0 reports 'Rank 2 failed to pass monitoredBarrier'"

# 5b. DETAIL also names the missing rank, because its wrapper runs a monitored_barrier before every collective
TORCH_DISTRIBUTED_DEBUG=DETAIL expect_fail "$tmp/stuck_d.log" --bug stuck --timeout 5
grep -q "failed to pass monitoredBarrier" "$tmp/stuck_d.log"
echo "OK 5b DETAIL on the stuck bug: the wrapper's monitored_barrier names the missing rank"

# 6. the fixed program
run4 --bug none --timeout 5 >"$tmp/none.log" 2>&1
test "$(grep -o "final barrier passed" "$tmp/none.log" | wc -l)" -eq 4  # ranks print concurrently: count matches, not lines
echo "OK 6 fixed program: exit status 0, the 4 ranks pass the final barrier"
echo "OK hang-debug"
