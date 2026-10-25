#!/usr/bin/env bash
#SBATCH --job-name=nccl-allreduce
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=8
#SBATCH --gpus-per-node=8
#SBATCH --exclusive
#SBATCH --time=00:30:00
#SBATCH --output=nccl-allreduce-%j.out
#
# Run nccl-tests all_reduce_perf on 2 nodes x 8 GPUs under Slurm (one MPI rank per GPU).
# GPU LAB, UNVERIFIED HERE: this script is linted (bash -n, shellcheck) but was never run on GPUs by the author.
#
# Prerequisites (your site): nccl-tests built with MPI=1 (see its README), and an srun that can start MPI ranks
# (PMIx or PMI2: check `srun --mpi=list`).
#
#   export NCCL_TESTS_DIR=/path/to/nccl-tests      # directory that contains build/all_reduce_perf
#   export MIN_AVG_BUSBW_GBS=17                     # optional: "Avg bus bandwidth" printed by a past run of the SAME sweep (see below)
#   sbatch run_all_reduce.sbatch [extra nccl-tests options, e.g. -a 3]
#
# Afterwards:  python3 parse_nccl_tests.py nccl-allreduce-<jobid>.out --expect-busbw 45   # plateau expected (datasheet or past run)
set -euo pipefail

NCCL_TESTS_DIR="${NCCL_TESTS_DIR:?set NCCL_TESTS_DIR to the nccl-tests checkout (it must contain build/all_reduce_perf)}"
BIN="${NCCL_TESTS_DIR}/build/all_reduce_perf"
[ -x "$BIN" ] || { echo "error: $BIN not found or not executable" >&2; exit 2; }

# NCCL logging: one file per host and process (%h, %p are documented in the NCCL user guide for NCCL_DEBUG_FILE).
export NCCL_DEBUG="${NCCL_DEBUG:-INFO}"
export NCCL_DEBUG_SUBSYS="${NCCL_DEBUG_SUBSYS:-INIT,NET,GRAPH,TUNING}"
export NCCL_DEBUG_FILE="${NCCL_DEBUG_FILE:-nccl-${SLURM_JOB_ID:-local}.%h.%p.log}"

# nccl-tests reads NCCL_TESTS_MIN_BW: the program returns a failure status when the "Avg bus bandwidth" it prints
# is below 0.9 times this value (src/common.cu of nccl-tests). That average covers EVERY size of the sweep, small
# messages included, so it is far below the plateau (about a third of it on the synthetic fixtures): never put the
# datasheet plateau here. Use the average printed by a past run of the same sweep, or a single-size run (-b 4G -e 4G).
# Unset means: no bandwidth check by nccl-tests (the parser does the plateau check afterwards).
if [ -n "${MIN_AVG_BUSBW_GBS:-}" ]; then
  export NCCL_TESTS_MIN_BW="$MIN_AVG_BUSBW_GBS"
fi

echo "# job ${SLURM_JOB_ID:-?} nodes: ${SLURM_JOB_NODELIST:-?}"

# -b/-e/-f: sizes from 8 B to 16 GiB, doubling.  -g 1: one GPU per rank.  -c 1: check the result once per size.
srun --mpi="${SRUN_MPI:-pmix}" --ntasks-per-node=8 --gpus-per-task=1 --gpu-bind=closest \
  "$BIN" -b 8 -e 16G -f 2 -g 1 -c 1 "$@"
