#!/usr/bin/env bash
# Node acceptance runner.
#   Live mode  (needs a GPU node): collects evidence with nvidia-smi, dcgmi, gpu_burn and nccl-tests, then decides.
#   Replay mode (--fixtures DIR) : skips the tools and decides on a directory of recorded or synthetic evidence.
# Exit status: 0 accept, 1 reject, 3 retest, 2 usage error or missing tool.
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
PY="${PYTHON:-python3}"
level=quick
out=""
fixtures=""
burn_seconds="${BURN_SECONDS:-600}"
nccl_bin="${NCCL_ALL_REDUCE_PERF:-all_reduce_perf}"
gpus="${EXPECTED_GPUS:-8}"
# Fields requested from nvidia-smi: UNVERIFIED on a real GPU, check them with `nvidia-smi --help-query-gpu`.
smi_fields="index,uuid,driver_version,persistence_mode,ecc.errors.uncorrected.volatile.total,remapped_rows.pending,remapped_rows.failure,retired_pages.pending,pcie.link.gen.current,pcie.link.width.current"

usage() { echo "usage: $0 [--level quick|full] [--out DIR] [--fixtures DIR]" >&2; exit 2; }
while [ $# -gt 0 ]; do
  case "$1" in
    --level) level="${2:-}"; shift 2 ;;
    --out) out="${2:-}"; shift 2 ;;
    --fixtures) fixtures="${2:-}"; shift 2 ;;
    *) usage ;;
  esac
done
case "$level" in quick|full) ;; *) usage ;; esac

need() { command -v "$1" >/dev/null 2>&1 || { echo "acceptance: required tool '$1' not found (live mode needs a GPU node)" >&2; exit 2; }; }

if [ -n "$fixtures" ]; then
  evidence="$fixtures"
else
  need nvidia-smi
  need dcgmi
  [ "$level" = quick ] || { need gpu_burn; need "$nccl_bin"; }
  evidence="${out:-$(mktemp -d)}"
  mkdir -p "$evidence"
  echo "acceptance: collecting evidence in $evidence (level $level)" >&2
  nvidia-smi --query-gpu="$smi_fields" --format=csv > "$evidence/smi.csv"
  dmesg_start="$(dmesg | wc -l)"
  rc=0
  if [ "$level" = full ]; then dcgmi diag -r 3 -j > "$evidence/dcgm.json" || rc=$?; else dcgmi diag -r 2 -j > "$evidence/dcgm.json" || rc=$?; fi
  echo "$rc" > "$evidence/dcgm.rc"
  if [ "$level" = full ]; then
    gpu_burn "$burn_seconds" > "$evidence/burn.log" 2>&1 || true
    "$nccl_bin" -b 8 -e 1G -f 2 -g "$gpus" -J "$evidence/nccl.json" > "$evidence/nccl.txt" 2>&1 || true
  fi
  dmesg | tail -n +"$((dmesg_start + 1))" | grep -E 'NVRM: Xid' > "$evidence/xid.log" || true
  {
    printf '{"driver": "%s", ' "$(nvidia-smi --query-gpu=driver_version --format=csv,noheader | head -n 1)"
    printf '"cuda_runtime": "%s", ' "${CUDA_RUNTIME_VERSION:-unknown}"
    printf '"fabric_manager": "%s", ' "$(dpkg-query -W -f='${Version}' nvidia-fabricmanager 2>/dev/null || echo unknown)"
    printf '"nvswitch_generation": %s, ' "${NVSWITCH_GENERATION:-0}"
    printf '"fabric_manager_active": %s, ' "$(systemctl is-active --quiet nvidia-fabricmanager && echo true || echo false)"
    printf '"nouveau_loaded": %s}\n' "$(lsmod | grep -q '^nouveau' && echo true || echo false)"
  } > "$evidence/versions.json"
fi

rc=0
"$PY" "$here/run_decision.py" "$evidence" --level "$level" || rc=$?
exit "$rc"
