#!/usr/bin/env bash
# Launch command of the example "LLaMA-3 70B on 64 GPUs" of the Megatron Core parallelism guide
# (docs.nvidia.com/megatron-core/developer-guide/latest/user-guide/parallelism-guide.html).
# NOT executed here: it needs Megatron-LM and 64 GPUs. Two additions to the guide's example: the multi-node
# arguments (--nnodes, rendezvous), taken from the torchrun documentation (the guide shows only --nproc_per_node=8),
# and --sequence-parallel and --use-distributed-optimizer, which the same guide recommends elsewhere
# ("always enable when using TP", "recommended for all multi-GPU training").
set -euo pipefail
HEAD_NODE="${HEAD_NODE:?set HEAD_NODE to the host running the rendezvous}"

torchrun --nnodes=8 --nproc_per_node=8 \
  --rdzv_backend=c10d --rdzv_endpoint="${HEAD_NODE}:29500" --rdzv_id="${JOB_ID:-demo}" \
  pretrain_gpt.py \
  --tensor-model-parallel-size 4 \
  --pipeline-model-parallel-size 4 \
  --context-parallel-size 2 \
  --sequence-parallel \
  --use-distributed-optimizer \
  --num-layers 80 \
  --hidden-size 8192 \
  --num-attention-heads 64 \
  --seq-length 8192 \
  --micro-batch-size 1 \
  --global-batch-size 512 \
  --bf16
