"""Predict the per-rank memory of DDP and FSDP2 from tensor shapes alone (fp32 AdamW).

Rules (FSDP2 documentation: parameters are DTensors sharded on dim 0 with torch.chunk):
  * DDP: every rank holds the full parameters, the full gradients and the full Adam state
    (exp_avg and exp_avg_sq): 4 + 4 + 8 = 16 bytes per parameter.
  * FSDP2: rank r holds the rows chunk(r) of every tensor, for parameters, gradients and Adam state.
  * Peak unsharded parameters at the entry of a block of the forward pass: the block itself
    (plus the root group, which stays unsharded) with reshard_after_forward=True; every block
    already visited plus the current one when blocks are not resharded.
"""
import math

BYTES_PARAM, BYTES_GRAD, BYTES_ADAM = 4, 4, 8  # fp32 parameters, fp32 gradients, exp_avg + exp_avg_sq


def shard_rows(n0, world, rank):
    """Rows of a tensor with n0 rows held by `rank` under torch.chunk(dim=0): ceil(n0/world) each, then fewer."""
    size = math.ceil(n0 / world)
    return max(0, min(size, n0 - rank * size))


def local_numel(shape, world, rank):
    rest = math.prod(shape[1:]) if len(shape) > 1 else 1
    return shard_rows(shape[0], world, rank) * rest


def predict_rank(shapes, world, rank, mode):
    """Persistent bytes of one rank: dict(param_bytes, grad_bytes, opt_bytes)."""
    if mode == "ddp":
        n = sum(math.prod(s) for s in shapes)
    elif mode == "fsdp":
        n = sum(local_numel(s, world, rank) for s in shapes)
    else:
        raise ValueError(mode)
    return {"param_bytes": n * BYTES_PARAM, "grad_bytes": n * BYTES_GRAD, "opt_bytes": n * BYTES_ADAM}


def predict_peak_unsharded(block_shapes, root_shapes, no_reshard):
    """Unsharded parameter bytes seen at the entry of the last block, for a list of blocks (lists of shapes)."""
    blk = [sum(math.prod(s) for s in b) * BYTES_PARAM for b in block_shapes]
    root = sum(math.prod(s) for s in root_shapes) * BYTES_PARAM
    return root + (sum(blk) if no_reshard else max(blk))
