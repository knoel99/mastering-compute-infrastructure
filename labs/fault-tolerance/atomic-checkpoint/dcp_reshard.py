#!/usr/bin/env python3
"""Save a tensor sharded over 2 CPU ranks with torch.distributed.checkpoint (DCP), load it on 4 ranks.

    python3 dcp_reshard.py --dir /tmp/dcp-demo

Launches its own processes (gloo backend, CPU). It shows load-time resharding: the checkpoint is
written by 2 processes and read back by 4, each of which receives a different slice of the tensor.
"""
import argparse
import os
import sys
import tempfile
from pathlib import Path

import torch
import torch.distributed as dist
import torch.distributed.checkpoint as dcp
import torch.multiprocessing as mp
from torch.distributed.device_mesh import init_device_mesh
from torch.distributed.tensor import Shard, distribute_tensor

ROWS, COLS = 8, 3


def worker(rank, world, port, path, phase):
    os.environ.update(MASTER_ADDR="127.0.0.1", MASTER_PORT=str(port))
    dist.init_process_group("gloo", rank=rank, world_size=world)
    mesh = init_device_mesh("cpu", (world,))
    full = torch.arange(ROWS * COLS, dtype=torch.float32).reshape(ROWS, COLS)
    if phase == "save":
        state = {"w": distribute_tensor(full, mesh, [Shard(0)])}
        dcp.save(state, checkpoint_id=path)
    else:
        state = {"w": distribute_tensor(torch.zeros(ROWS, COLS), mesh, [Shard(0)])}
        dcp.load(state, checkpoint_id=path)
        mine = state["w"].to_local()
        assert torch.equal(state["w"].full_tensor(), full), "resharded tensor differs from the original"
        print(f"load rank {rank}/{world}: holds rows {int(mine[0, 0]) // COLS}..{int(mine[-1, 0]) // COLS}", flush=True)
    dist.destroy_process_group()


def free_port():
    import socket
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=None)
    a = ap.parse_args()
    d = Path(a.dir or tempfile.mkdtemp(prefix="dcp-"))
    for phase, world in (("save", 2), ("load", 4)):
        mp.spawn(worker, args=(world, free_port(), str(d), phase), nprocs=world, join=True)
        if phase == "save":
            print("files written by 2 ranks:", sorted(p.name for p in d.iterdir()), flush=True)
    print("OK dcp: saved on 2 ranks, loaded on 4 ranks, tensor identical")
    return 0


if __name__ == "__main__":
    sys.exit(main())
