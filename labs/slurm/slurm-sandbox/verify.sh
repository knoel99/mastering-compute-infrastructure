#!/usr/bin/env bash
# Lab 5.1 check: a real Slurm with accounting runs a batch script, an array and a dependency chain.
set -euo pipefail
cd "$(dirname "$0")"
trap 'bash ./teardown.sh >/dev/null 2>&1 || true' EXIT
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
cat "$out"/hello-"$first"_2.out
echo "OK part A: array of 3 + afterok dependency completed, accounting recorded"

echo "--- Part B: checkpoint on SIGUSR1, then resume"
export CKPT_FILE="$out/ckpt.json"
j1=$(sbatch --parsable --chdir="$PWD/examples" --export=ALL,TOTAL_STEPS=100000 -o "$out/run1.out" examples/checkpoint_on_signal.sbatch)
for _ in $(seq 1 30); do [ "$(squeue -h -j "$j1" -o %T)" = "RUNNING" ] && break; sleep 1; done
sleep 3
scancel --signal=USR1 --batch "$j1"
for _ in $(seq 1 30); do sacct -X -n -j "$j1" --format=State | grep -q COMPLETED && break; sleep 1; done
cat "$out/run1.out"
saved=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['step'])" "$CKPT_FILE")
[ "$saved" -gt 0 ] || { echo "FAIL: no checkpoint written"; exit 1; }
j2=$(sbatch --parsable --chdir="$PWD/examples" --export=ALL,TOTAL_STEPS=$((saved + 5)) -o "$out/run2.out" examples/checkpoint_on_signal.sbatch)
for _ in $(seq 1 30); do sacct -X -n -j "$j2" --format=State | grep -q COMPLETED && break; sleep 1; done
cat "$out/run2.out"
grep -q "start at step $saved" "$out/run2.out"
echo "OK slurm-sandbox: parts A and B"
