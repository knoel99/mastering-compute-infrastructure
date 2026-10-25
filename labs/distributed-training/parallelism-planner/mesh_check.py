"""Check mesh.py against PyTorch's own DeviceMesh on 4 gloo processes.

    torchrun --standalone --nproc_per_node=4 mesh_check.py
"""
import torch.distributed as dist
from torch.distributed.device_mesh import init_device_mesh

from mesh import Mesh


def main():
    mesh = init_device_mesh("cpu", (2, 2), mesh_dim_names=("dp", "tp"))
    rank = dist.get_rank()
    mine = Mesh(("dp", "tp"), (2, 2))
    for name in ("dp", "tp"):
        theirs = dist.get_process_group_ranks(mesh.get_group(name))
        assert sorted(theirs) == mine.group(rank, name), (rank, name, theirs, mine.group(rank, name))
    if rank == 0:
        print("OK mesh_check: Mesh.group agrees with torch DeviceMesh; tp group of rank 0 =",
              mine.group(0, "tp"), "dp group of rank 0 =", mine.group(0, "dp"))
    dist.destroy_process_group()


if __name__ == "__main__":
    main()
