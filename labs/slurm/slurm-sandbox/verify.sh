#!/usr/bin/env bash
# Lab 5.1 check: a real Slurm with accounting runs a batch script, an array and a dependency chain.
set -euo pipefail
cd "$(dirname "$0")"
here="$PWD"
trap 'bash ./teardown.sh --purge-db >/dev/null 2>&1 || true' EXIT
# Start from an empty accounting database: job ids restart at 1 after every setup, so records left by an earlier run
# (same ids, state COMPLETED) would make the wait loop below succeed before the new jobs have even run.
bash ./teardown.sh --purge-db >/dev/null 2>&1 || true
bash ./setup.sh >/dev/null
out="$(mktemp -d)"
cat > "$out/hello.sbatch" <<'SB'
#!/usr/bin/env bash
#SBATCH --job-name=hello
#SBATCH --cpus-per-task=1
#SBATCH --time=00:01:00
set -euo pipefail
echo "task=${SLURM_ARRAY_TASK_ID:-none} host=$(hostname -s) cpus=${SLURM_CPUS_PER_TASK}"
sleep 1
SB
first=$(sbatch --parsable --array=1-3 -o "$out/hello-%A_%a.out" "$out/hello.sbatch")
after=$(sbatch --parsable --dependency=afterok:"$first" --wrap='echo dependency-satisfied' -o "$out/after.out")
for _ in $(seq 1 60); do
  n=$(sacct -X -n -j "$first,$after" --format=State | grep -c COMPLETED || true)
  [ "$n" -ge 4 ] && break
  sleep 1
done
sacct -X -j "$first,$after" --format=JobID%14,JobName%10,State%10,Elapsed
test "$(sacct -X -n -j "$first,$after" --format=State | grep -c COMPLETED)" -eq 4
grep -q "dependency-satisfied" "$out/after.out"
# afterok means the dependent job starts only once every array task has ended (ISO timestamps compare as strings)
last_end=$(sacct -X -n -P -j "$first" --format=End | sort | tail -n 1)
after_start=$(sacct -X -n -P -j "$after" --format=Start)
[[ ! "$after_start" < "$last_end" ]] || { echo "FAIL: dependent job started ($after_start) before the array ended ($last_end)"; exit 1; }
cat "$out"/hello-"$first"_2.out
echo "OK part A: array of 3 + afterok dependency completed, accounting recorded"

echo "--- Part B: checkpoint on SIGUSR1, then resume"
export CKPT_FILE="$out/ckpt.json"
j1=$(cd examples && sbatch --parsable --export=ALL,TOTAL_STEPS=100000 -o "$out/run1.out" checkpoint_on_signal.sbatch)
for _ in $(seq 1 30); do [ "$(squeue -h -j "$j1" -o %T)" = "RUNNING" ] && break; sleep 1; done
# signal only once the trainer has installed its handler (it prints "start at step" right after), then let it run a moment
for _ in $(seq 1 30); do grep -q "start at step" "$out/run1.out" 2>/dev/null && break; sleep 1; done
sleep 2
scancel --signal=USR1 --batch "$j1"
for _ in $(seq 1 30); do sacct -X -n -j "$j1" --format=State | grep -q COMPLETED && break; sleep 1; done
cat "$out/run1.out"
[ -s "$CKPT_FILE" ] || { echo "FAIL: no checkpoint written"; exit 1; }
saved=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['step'])" "$CKPT_FILE")
[ "$saved" -gt 0 ] || { echo "FAIL: no checkpoint written"; exit 1; }
j2=$(cd examples && sbatch --parsable --export=ALL,TOTAL_STEPS=$((saved + 5)) -o "$out/run2.out" checkpoint_on_signal.sbatch)
for _ in $(seq 1 30); do sacct -X -n -j "$j2" --format=State | grep -q COMPLETED && break; sleep 1; done
cat "$out/run2.out"
grep -q "start at step $saved" "$out/run2.out"
# A failing program must make the job fail: submitted from a directory without trainer.py, python3 exits 2.
j3=$(cd "$out" && sbatch --parsable -o "$out/run3.out" "$here/examples/checkpoint_on_signal.sbatch")
for _ in $(seq 1 30); do sacct -X -n -j "$j3" --format=State | grep -qE 'COMPLETED|FAILED' && break; sleep 1; done
sacct -X -j "$j3" --format=JobID,State%10,ExitCode
sacct -X -n -j "$j3" --format=State | grep -q FAILED || { echo "FAIL: a trainer that cannot start must end the job as FAILED"; exit 1; }
echo "OK failure propagation: a crashing trainer ends the job as FAILED"
echo "OK slurm-sandbox: parts A and B"
