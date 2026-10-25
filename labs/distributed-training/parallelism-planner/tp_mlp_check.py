"""A real tensor-parallel MLP on gloo: Y = GeLU(X A) B with A split by columns and B split by rows.

    torchrun --standalone --nproc_per_node=2 tp_mlp_check.py

Each rank owns one column block of A and the matching row block of B, so GeLU needs no communication.
Megatron's two conjugate operators are written as autograd functions:
  f  identity in the forward pass, all-reduce in the backward pass (the input gradient is a sum over ranks)
  g  all-reduce in the forward pass, identity in the backward pass (the output is a sum over ranks)
The script checks output and gradients against the dense MLP, and counts the collectives of one step.
"""
import torch
import torch.distributed as dist
import torch.nn.functional as F

CALLS = {"forward": 0, "backward": 0}


class CopyToTP(torch.autograd.Function):  # operator f
    @staticmethod
    def forward(ctx, x):
        return x

    @staticmethod
    def backward(ctx, grad):
        grad = grad.clone()
        dist.all_reduce(grad)
        CALLS["backward"] += 1
        return grad


class ReduceFromTP(torch.autograd.Function):  # operator g
    @staticmethod
    def forward(ctx, x):
        y = x.clone()
        dist.all_reduce(y)
        CALLS["forward"] += 1
        return y

    @staticmethod
    def backward(ctx, grad):
        return grad


def main():
    dist.init_process_group("gloo")
    rank, t = dist.get_rank(), dist.get_world_size()
    h, f, tokens = 64, 256, 32
    torch.manual_seed(0)  # same seed on every rank: every rank can build the dense reference
    A = torch.randn(h, f, dtype=torch.float64) / h**0.5
    B = torch.randn(f, h, dtype=torch.float64) / f**0.5
    X = torch.randn(tokens, h, dtype=torch.float64)
    X_dense = X.clone().requires_grad_()
    A_dense, B_dense = A.clone().requires_grad_(), B.clone().requires_grad_()
    Y_dense = F.gelu(X_dense @ A_dense) @ B_dense
    Y_dense.square().sum().backward()

    cols = f // t
    A_i = A[:, rank * cols:(rank + 1) * cols].clone().requires_grad_()
    B_i = B[rank * cols:(rank + 1) * cols, :].clone().requires_grad_()
    X_tp = X.clone().requires_grad_()
    Y = ReduceFromTP.apply(F.gelu(CopyToTP.apply(X_tp) @ A_i) @ B_i)
    Y.square().sum().backward()

    errs = {
        "output": (Y - Y_dense).abs().max().item(),
        "dA_shard": (A_i.grad - A_dense.grad[:, rank * cols:(rank + 1) * cols]).abs().max().item(),
        "dB_shard": (B_i.grad - B_dense.grad[rank * cols:(rank + 1) * cols, :]).abs().max().item(),
        "dX": (X_tp.grad - X_dense.grad).abs().max().item(),
    }
    assert all(v < 1e-9 for v in errs.values()), errs
    assert CALLS == {"forward": 1, "backward": 1}, CALLS  # one all-reduce each way per MLP block
    if rank == 0:
        print(f"OK tp_mlp_check: {t}-way tensor-parallel MLP equals the dense MLP (max error {max(errs.values()):.1e}, float64); "
              f"collectives per block: {CALLS['forward']} forward + {CALLS['backward']} backward")
    dist.destroy_process_group()


if __name__ == "__main__":
    main()
