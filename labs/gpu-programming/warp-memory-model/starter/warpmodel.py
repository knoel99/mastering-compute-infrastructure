"""STARTER: implement the four functions below, then run  WARPMODEL_MODULE=starter.warpmodel pytest.

The reference solution is ../warpmodel.py (read it only after trying). Rules:
  * global memory, compute capability >= 6.0: a warp-wide access costs one transaction per distinct
    32-byte sector touched (an element that straddles a boundary touches both sectors);
  * shared memory: 32 banks, word w is in bank w % 32; same word = broadcast (no conflict);
    different words in the same bank are serialized;
  * divergence: each non-empty side of an if/else is executed once, one after the other;
  * occupancy: resident blocks per SM = min over threads, blocks, registers, shared memory.
"""
from __future__ import annotations

import math  # noqa: F401  (you will need it)
from dataclasses import dataclass
from typing import Iterable, Sequence

WARP_SIZE = 32
SECTOR_BYTES = 32
BANKS = 32


def sectors_touched(byte_addresses: Iterable[int], elem_bytes: int = 4) -> int:
    raise NotImplementedError("count distinct 32-byte sectors")


def bank_conflict_degree(word_indices: Iterable[int]) -> int:
    raise NotImplementedError("largest number of DISTINCT words in one bank")


def divergence_cost(predicate: Sequence[bool], t_then: float, t_else: float) -> float:
    raise NotImplementedError("sum of the non-empty paths")


@dataclass(frozen=True)
class SMLimits:
    name: str = "CC 8.0"
    max_threads: int = 2048
    max_warps: int = 64
    max_blocks: int = 32
    registers: int = 64 * 1024
    smem_bytes: int = 164 * 1024
    max_regs_per_thread: int = 255


def occupancy(threads_per_block: int, regs_per_thread: int, smem_per_block: int,
              lim: SMLimits = SMLimits()) -> dict:
    raise NotImplementedError("return blocks_per_sm, warps_per_sm, occupancy, limiter, by_resource")
