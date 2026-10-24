#!/usr/bin/env bash
# Needs root. On a cgroup v1 or hybrid machine the v1 branch is exercised; on a pure cgroup v2 machine
# the v2 branch is (it has not been run by the author). Lint always runs.
set -euo pipefail
cd "$(dirname "$0")"
bash -n cgroup_lab.sh
if command -v shellcheck >/dev/null; then shellcheck cgroup_lab.sh; else echo "shellcheck not installed: skipped"; fi
"${PYTHON:-python3}" -m py_compile alloc.py burn.py
bash cgroup_lab.sh
