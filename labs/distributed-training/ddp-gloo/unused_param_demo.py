"""The classic DDP error: a parameter that gets no gradient.

    torchrun --standalone --nproc_per_node=2 unused_param_demo.py            # fails
    torchrun --standalone --nproc_per_node=2 unused_param_demo.py --fix      # find_unused_parameters=True

The model has two heads but the loss only uses the second one, so head `a` never receives a
gradient. DDP waits for every parameter before it launches its last bucket, so the *second*
iteration raises "Expected to have finished reduction in the prior iteration".
Run it with TORCH_DISTRIBUTED_DEBUG=INFO to get the names of the offending parameters.
"""
import argparse
import sys
from datetime import timedelta

import torch
import torch.distributed as dist
from torch import nn
from torch.nn.parallel import DistributedDataParallel as DDP


class TwoHeads(nn.Module):
    def __init__(self):
        super().__init__()
        self.a = nn.Linear(10, 10, bias=False)
        self.b = nn.Linear(10, 1, bias=False)

    def forward(self, x):
        return self.a(x), self.b(x)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fix", action="store_true")
    a = ap.parse_args()
    dist.init_process_group("gloo", timeout=timedelta(seconds=30))
    rank = dist.get_rank()
    model = DDP(TwoHeads(), find_unused_parameters=a.fix)
    x = torch.randn(4, 10)
    try:
        for step in range(3):
            _, out_b = model(x)
            out_b.sum().backward()  # head `a` is never used by the loss
        print(f"rank {rank}: 3 steps completed")
    except RuntimeError as e:
        print(f"rank {rank}: RuntimeError at step {step}", flush=True)
        if rank == 0:
            print("\n".join("    " + line for line in str(e).splitlines()), flush=True)
        sys.exit(1)
    dist.destroy_process_group()


if __name__ == "__main__":
    main()
