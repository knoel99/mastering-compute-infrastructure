"""Predict how DistributedDataParallel groups gradients into buckets.

Rule (read from torch.nn.parallel.distributed and checked against DDP's own log in train.py):
tensors are visited in the order their gradients become ready (roughly the reverse of
model.parameters()); a tensor is appended to the current bucket, and the bucket is closed
as soon as its size reaches the limit. So a bucket may exceed the limit by its last tensor.
The very first bucket uses a 1 MiB limit when the user does not pass bucket_cap_mb,
otherwise it uses the same limit as the others (torch 2.14 behaviour, see README).
"""
import argparse

MiB = 1024 * 1024
DEFAULT_CAP_MB = 25
DEFAULT_FIRST_BUCKET_BYTES = 1 * MiB


def predict_buckets(sizes_in_ready_order, cap_mb=None):
    """Return the list of bucket sizes in bytes for tensors given in gradient-ready order."""
    cap = int((DEFAULT_CAP_MB if cap_mb is None else cap_mb) * MiB)
    first_cap = DEFAULT_FIRST_BUCKET_BYTES if cap_mb is None else cap
    buckets, cur, limit = [], 0, first_cap
    for s in sizes_in_ready_order:
        cur += s
        if cur >= limit:
            buckets.append(cur)
            cur, limit = 0, cap
    if cur:
        buckets.append(cur)
    return buckets


def param_bytes_ready_order(model):
    """Parameter sizes in bytes, reversed: gradients become ready from the last layer to the first."""
    return [p.numel() * p.element_size() for p in model.parameters()][::-1]


if __name__ == "__main__":
    from common import build_model

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cap-mb", type=float, default=None, help="DDP bucket_cap_mb (default: DDP default)")
    a = ap.parse_args()
    b = predict_buckets(param_bytes_ready_order(build_model()), a.cap_mb)
    print(f"{len(b)} buckets:", ", ".join(str(x) for x in b), f"(total {sum(b)} bytes)")
