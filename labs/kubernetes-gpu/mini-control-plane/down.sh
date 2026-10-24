#!/usr/bin/env bash
# Stop every process started by up.sh (by exact process name, never by pattern).
set -euo pipefail
cd "$(dirname "$0")"
# shellcheck source=lib.sh
. ./lib.sh
cp_down
echo "stopped"
