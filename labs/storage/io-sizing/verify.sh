#!/usr/bin/env bash
# Sandbox check for lab 8.4: unit tests (deterministic, seeded simulations with tolerances) and the demo output.
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
"$PY" -m pytest -q -p no:cacheprovider test_iosizing.py
out="$("$PY" iosizing.py demo)"
echo "$out"
ex="$("$PY" iosizing.py exercises)"
echo "$ex"
printf '%s\n%s\n' "$out" "$ex" | "$PY" -c "
import re, sys
vals = {}
for line in sys.stdin:
    m = re.match(r'(ex?\d+\.\S+)\s+(\S+)', line)
    if m:
        vals[m.group(1)] = float(m.group(2))
def check(cond, msg):
    if not cond:
        sys.exit('FAIL: ' + msg)
check(abs(vals['ex1.ckpt_70B_GB'] - 980) < 1e-6, '70e9 parameters x 14 bytes = 980 GB')
check(abs(vals['ex7.sim_lru_c50'] - vals['ex7.lru_hit_c50']) < 0.05, 'simulated LRU hit ratio close to x + (1 - x) ln (1 - x)')
check(abs(vals['ex7.sim_pinned_c50'] - 0.5) < 0.05, 'simulated pinned cache hit ratio close to C/D')
check(vals['ex7.eff_bw_pinned_c50_GB_s'] > 1.3 * vals['ex7.eff_bw_lru_c50_GB_s'], 'a cache that never evicts beats LRU at 50 % size')
check(abs(vals['ex7.required_hit_for_3GB_s'] - 0.8) < 1e-9 and abs(vals['ex3.request_ratio'] - 167.8) < 0.1, 'example 7.1 and 3.6 values')
check(abs(vals['e2.write_GB_s'] - 42) < 1e-6 and abs(vals['e4.stripes_needed'] - 5) < 1e-9, 'exercise 2 and 4 values')
check(abs(vals['e4.agg_GB_s'] - 80) < 1e-6 and vals['e4.clients_needed'] == 5, 'exercise 4 aggregate and clients')
check(abs(vals['e12.quota_TB'] - 29.8) < 0.1, 'exercise 12 quota of the work file system')
check(vals['e10.total20_random_s'] > 1.5 * vals['e10.total20_sticky_s'], 'sticky shard assignment must beat random assignment')
check(abs(vals['e11.ops_shards'] * 1000 - vals['e11.ops_per_epoch']) < 1e-6, 'shards of 1000 samples divide the metadata operations by 1000')
print('OK io-sizing: 70B checkpoint = %.0f GB, LRU %.0f %% vs pinned %.0f %% hits at cache = 50 %% of data' % (
    vals['ex1.ckpt_70B_GB'], 100 * vals['ex7.sim_lru_c50'], 100 * vals['ex7.sim_pinned_c50']))
"
