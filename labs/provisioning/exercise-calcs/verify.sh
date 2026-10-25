#!/usr/bin/env bash
# Re-computes every number that the exercise solutions of the provisioning module quote (instant, standard library only).
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
export PYTHONDONTWRITEBYTECODE=1
run() { "$PY" calc.py "$@"; }
expect() { local out="$1" pattern="$2"; if ! grep -qF -- "$pattern" <<<"$out"; then echo "FAIL: '$pattern' not in:"; echo "$out"; exit 1; fi; }

out="$(run llama)"; echo "$out"
expect "$out" 'sum of counts      : 419'
expect "$out" 'Faulty GPU: 148/419 = 35.3 % but the table prints 30.1 %'
out="$(run mttf --ref-gpus 8 --ref-days 47.7 --gpus 1024 --measured-hours 7.9)"; echo "$out"
expect "$out" '1/N prediction     : 1024 GPUs -> 8.94 h'
out="$(run rolling --nodes 64 --batch 8 --walltime-h 24 --reboot-h 0.25)"; echo "$out"
expect "$out" 'worst case total   : 194.00 h = 8.08 days'
out="$(run dcgm --nodes 32 --minutes 35 --parallel 32)"; echo "$out"
expect "$out" 'at most 35.0 min'
out="$(run dcgm --nodes 32 --minutes 35 --parallel 1)"; echo "$out"
expect "$out" 'at most 1120.0 min = 18.67 h'
out="$(run busbw --ranks 8 --size-gib 4 --ms 36 --baseline 200)"; echo "$out"
expect "$out" 'factor 2(n-1)/n    : n=8 -> 1.750'
out="$(run spares --nodes 256 --rate-per-1000-node-days 2.5 --repair-days 10 --quantile 0.95)"; echo "$out"
expect "$out" 'mean 6.40'
expect "$out" 'keep 11 spare nodes'
out="$(run spares --nodes 256 --rate-per-1000-node-days 2.5 --repair-days 21 --quantile 0.95)"; echo "$out"
expect "$out" 'mean 13.44'
expect "$out" 'keep 20 spare nodes'
out="$(run rolling --nodes 120 --batch 12 --walltime-h 48 --reboot-h 0.3333)"; echo "$out"
expect "$out" 'worst case total   : 483.33 h = 20.14 days'
out="$(run rolling --nodes 120 --batch 24 --walltime-h 48 --reboot-h 0.3333)"; echo "$out"
expect "$out" 'worst case total   : 241.67 h = 10.07 days'
out="$(run busbw --ranks 8 --size-gib 4 --ms 41 --baseline 200)"; echo "$out"
expect "$out" 'busbw = algbw * f  : 183.3 GB/s  (92 % of the baseline 200.0)'
run compat --driver 570 --cuda 12.9
if run compat --driver 570 --cuda 13.0; then echo "FAIL: driver 570 must not satisfy CUDA 13"; exit 1; fi
out="$(run mig --request 3g.20gb=3 --request 2g.10gb=4 --request 1g.5gb=6)"; echo "$out"
expect "$out" 'minimum            : 4 GPU(s)'
expect "$out" 'idle in total      : 5/28 compute slices (17.9 %), 6/32 memory slices (18.8 %)'
out="$(run mig --request 4g.20gb=3 --request 3g.20gb=1 --request 2g.10gb=3)"; echo "$out"
expect "$out" 'lower bounds       : compute 21/7 -> 3 GPU(s), memory 22/8 -> 3 GPU(s)'
expect "$out" 'minimum            : 4 GPU(s)'
out="$(run mig --request 4g.20gb=3 --request 3g.20gb=1 --request 2g.10gb=2 --request 1g.5gb=2)"; echo "$out"
expect "$out" 'minimum            : 3 GPU(s)'
echo "OK exercise-calcs: every figure quoted in the solutions is recomputed above"
