#!/usr/bin/env bash
# Start the mini control plane (first run downloads about 300 MB into $K8S_MINI_CACHE).
set -euo pipefail
cd "$(dirname "$0")"
# shellcheck source=lib.sh
. ./lib.sh
cp_up
kc version | head -3
