#!/usr/bin/env bash
# Sandbox check: the three kernel counters must tell the page-cache story. No root needed, no fio needed.
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
"$PY" -m pytest -q -p no:cacheprovider test_pagecache.py
out="$("$PY" pagecache.py --json)"
"$PY" pagecache.py
echo "$out" | "$PY" -c "
import json, sys
s = {x['stage']: x for x in json.load(sys.stdin)}
size = 256
def check(cond, msg):
    if not cond:
        sys.exit('FAIL: ' + msg)
check(s['after write()']['dirty_kib'] >= 0.5 * size * 1024, 'written pages should be dirty before fsync')
check(s['after write()']['resident_mib'] >= 0.9 * size, 'written pages should be resident')
check(s['after fsync()']['dirty_kib'] < 0.1 * size * 1024, 'fsync should flush the dirty pages')
check(s['after DONTNEED']['resident_mib'] < 0.1 * size, 'DONTNEED should drop the clean pages')
check(s['cold buffered read']['device_read_mib'] >= 0.9 * size, 'cold read should hit the device')
check(s['cold buffered read']['resident_mib'] >= 0.9 * size, 'cold read should fill the cache')
check(s['warm buffered read']['device_read_mib'] < 0.1 * size, 'warm read should not touch the device')
check(s['O_DIRECT read']['device_read_mib'] >= 0.9 * size, 'O_DIRECT read should hit the device')
check(s['O_DIRECT read']['resident_mib'] < 0.1 * size, 'O_DIRECT read should not fill the cache')
print('OK pagecache')
"
bash littles_law.sh
