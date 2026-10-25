"""Shared pieces of the ddp-gloo lab: a small MLP, a seeded synthetic dataset and helpers.

Everything is deterministic given (seed, step): the *global* batch of a step is generated
from a seeded generator, then each rank takes its own slice of it. A single process that
takes the whole global batch therefore sees exactly the same data as the DDP group.
"""
import torch
from torch import nn

IN_DIM, HIDDEN, DEPTH = 64, 512, 6


def build_model(seed: int = 0) -> nn.Module:
    """MLP with DEPTH hidden layers; about 1.6 M parameters (6.4 MB in fp32)."""
    torch.manual_seed(seed)
    layers, d = [], IN_DIM
    for _ in range(DEPTH):
        layers += [nn.Linear(d, HIDDEN), nn.GELU()]
        d = HIDDEN
    layers.append(nn.Linear(d, 1))
    return nn.Sequential(*layers)


def global_batch(step: int, size: int, seed: int = 0):
    """The whole global batch of `step`: identical on every process, whatever the world size."""
    g = torch.Generator().manual_seed(seed * 1_000_003 + step)
    x = torch.randn(size, IN_DIM, generator=g)
    w = torch.linspace(-1.0, 1.0, IN_DIM)
    y = torch.tanh(x @ w / 8.0).unsqueeze(1) + 0.05 * torch.randn(size, 1, generator=g)
    return x, y


def shard_bounds(total: int, rank: int, world: int, uneven: bool = False):
    """Slice [lo, hi) of the global batch owned by `rank`.

    Even split: total // world samples each (total must be divisible by world).
    Uneven split, the classic 'ragged last batch' bug: every rank but the last takes
    total // world + 4 samples and the last rank gets the remainder (4 samples for 64 on 4 ranks).
    """
    if not uneven:
        assert total % world == 0, "global batch must be divisible by world size"
        per = total // world
        return rank * per, (rank + 1) * per
    per = total // world + 4
    lo = rank * per
    hi = total if rank == world - 1 else (rank + 1) * per
    return lo, hi


def flat_params(model: nn.Module) -> torch.Tensor:
    return torch.cat([p.detach().reshape(-1) for p in model.parameters()])
