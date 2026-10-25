#!/usr/bin/env python3
"""Analytic models of one warp: global-memory sectors, shared-memory bank conflicts,
branch divergence and SM occupancy.

These are MODELS, not measurements: they count what the CUDA documentation says the hardware
does (32-byte sectors for global memory on compute capability >= 6.0, 32 banks of 4 bytes for
shared memory, serialized branch paths, resource-limited residency). No GPU is needed, which is
the point: the Numba CUDA simulator has no warps (see ../numba-cuda-sim/README.md), so
coalescing and divergence cannot be observed there and are modelled here instead.

Usage:
    python3 warpmodel.py report            # the tables quoted in the course
    python3 warpmodel.py occupancy --threads 256 --regs 32 --smem 0
"""
from __future__ import annotations

import argparse
import math
import random
from dataclasses import dataclass
from typing import Callable, Iterable, Sequence

WARP_SIZE = 32
SECTOR_BYTES = 32  # global-memory transaction granularity, compute capability >= 6.0
BANKS = 32  # shared-memory banks, each 4 bytes wide


# ---------------------------------------------------------------- global memory
def sectors_touched(byte_addresses: Iterable[int], elem_bytes: int = 4) -> int:
    """Number of distinct 32-byte sectors needed to serve one warp-wide load or store.

    Every lane reads `elem_bytes` bytes starting at its byte address. An element that straddles
    a sector boundary touches both sectors.
    """
    touched = set()
    for a in byte_addresses:
        for b in range(a, a + elem_bytes):
            touched.add(b // SECTOR_BYTES)
    return len(touched)


def load_efficiency(byte_addresses: Sequence[int], elem_bytes: int = 4) -> float:
    """Useful bytes divided by bytes moved (sectors x 32). 1.0 means perfectly coalesced."""
    useful = len(byte_addresses) * elem_bytes
    return useful / (sectors_touched(byte_addresses, elem_bytes) * SECTOR_BYTES)


def strided_addresses(stride_elems: int, elem_bytes: int = 4, base: int = 0) -> list[int]:
    """Lane k reads element k * stride (a column of a row-major matrix has stride = row length)."""
    return [base + lane * stride_elems * elem_bytes for lane in range(WARP_SIZE)]


def aos_field_addresses(struct_bytes: int, field_offset: int = 0) -> list[int]:
    """Lane k reads one field of struct k in an array of structures."""
    return [lane * struct_bytes + field_offset for lane in range(WARP_SIZE)]


def permuted_addresses(seed: int, n_elems: int = 1 << 20, elem_bytes: int = 4) -> list[int]:
    """Lanes read 32 random elements of a large array (seeded: reproducible)."""
    rng = random.Random(seed)
    return [rng.randrange(n_elems) * elem_bytes for _ in range(WARP_SIZE)]


# ---------------------------------------------------------------- shared memory
def bank_conflict_degree(word_indices: Iterable[int]) -> int:
    """Serialization factor of one warp-wide shared-memory access of 32-bit words.

    Word w lives in bank w % 32. Lanes reading the same word are served by a broadcast and do
    not conflict; lanes reading different words of the same bank are serialized. The returned
    degree is the largest number of distinct words falling in one bank (1 = conflict-free).
    """
    per_bank: dict[int, set[int]] = {}
    for w in word_indices:
        per_bank.setdefault(w % BANKS, set()).add(w)
    return max(len(s) for s in per_bank.values())


def tile_column_read(tile_width: int, pad: int = 0) -> list[int]:
    """Word indices read when lane k reads row k, column 0 of a `float tile[32][tile_width+pad]`."""
    return [lane * (tile_width + pad) for lane in range(WARP_SIZE)]


# ---------------------------------------------------------------- divergence
def divergence_cost(predicate: Sequence[bool], t_then: float, t_else: float) -> float:
    """Time of `if (p) {then} else {else}` for one warp: each non-empty path is executed once."""
    return (t_then if any(predicate) else 0.0) + (t_else if not all(predicate) else 0.0)


def lanes_pred(fn: Callable[[int], bool]) -> list[bool]:
    return [bool(fn(lane)) for lane in range(WARP_SIZE)]


# ---------------------------------------------------------------- occupancy
@dataclass(frozen=True)
class SMLimits:
    """Per-SM resource limits. Defaults: compute capability 8.0 (A100), CUDA Programming Guide,
    section 5.1 (Table 30 and Table 31)."""

    name: str = "CC 8.0"
    max_threads: int = 2048
    max_warps: int = 64
    max_blocks: int = 32
    registers: int = 64 * 1024
    smem_bytes: int = 164 * 1024
    max_regs_per_thread: int = 255


def occupancy(threads_per_block: int, regs_per_thread: int, smem_per_block: int,
              lim: SMLimits = SMLimits()) -> dict:
    """Resident blocks per SM and occupancy. Simplified: ignores the allocation granularity of
    registers and shared memory and the shared memory reserved by the system (real calculators
    round up, so the true value is lower or equal)."""
    if not 1 <= threads_per_block <= 1024:
        raise ValueError("threads per block must be in 1..1024")
    if regs_per_thread > lim.max_regs_per_thread:
        raise ValueError("too many registers per thread")
    warps_per_block = math.ceil(threads_per_block / WARP_SIZE)
    limits = {
        "threads": lim.max_threads // (warps_per_block * WARP_SIZE),
        "blocks": lim.max_blocks,
        "registers": lim.registers // (regs_per_thread * warps_per_block * WARP_SIZE)
        if regs_per_thread else lim.max_blocks,
        "shared memory": lim.smem_bytes // smem_per_block if smem_per_block else lim.max_blocks,
    }
    blocks = min(limits.values())
    limiter = [k for k, v in limits.items() if v == blocks][0]
    warps = blocks * warps_per_block
    return {"blocks_per_sm": blocks, "warps_per_sm": warps, "occupancy": warps / lim.max_warps,
            "limiter": limiter, "by_resource": limits}


# ---------------------------------------------------------------- report
def report() -> str:
    out = []
    out.append("== Global memory: 32 lanes load one float32 each (sector = 32 bytes) ==")
    out.append(f"{'pattern':<42}{'sectors':>8}{'efficiency':>12}")
    rows = [
        ("unit stride (lane k reads a[k])", strided_addresses(1)),
        ("unit stride, base shifted by 4 bytes", strided_addresses(1, base=4)),
        ("stride 2", strided_addresses(2)),
        ("stride 8 (32 bytes)", strided_addresses(8)),
        ("stride 32 (column of 32-wide matrix)", strided_addresses(32)),
        ("AoS, field x of a 16-byte struct", aos_field_addresses(16)),
        ("32 random elements (seed 0)", permuted_addresses(0)),
    ]
    for name, addrs in rows:
        out.append(f"{name:<42}{sectors_touched(addrs):>8}{100 * load_efficiency(addrs):>11.1f}%")
    out.append("")
    out.append("== Shared memory: lane k reads tile[k][0] of float tile[32][W+pad] ==")
    out.append(f"{'layout':<42}{'conflict degree':>16}")
    for name, w, pad in [("W=32, no padding", 32, 0), ("W=32, pad 1", 32, 1),
                         ("W=16, no padding", 16, 0), ("W=33", 33, 0)]:
        out.append(f"{name:<42}{bank_conflict_degree(tile_column_read(w, pad)):>16}")
    out.append(f"{'all lanes read the same word (broadcast)':<42}{bank_conflict_degree([7] * 32):>16}")
    out.append("")
    out.append("== Divergence: if (p) 10 cycles else 10 cycles, for one warp ==")
    for name, fn in [("p = lane % 2 (alternating lanes)", lambda i: i % 2 == 0),
                     ("p = (lane // 16) % 2 == 0 (half warps)", lambda i: (i // 16) % 2 == 0),
                     ("p = same value for all 32 lanes", lambda i: True)]:
        out.append(f"{name:<42}{divergence_cost(lanes_pred(fn), 10, 10):>10.0f} cycles")
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("report")
    oc = sub.add_parser("occupancy")
    oc.add_argument("--threads", type=int, required=True)
    oc.add_argument("--regs", type=int, required=True)
    oc.add_argument("--smem", type=int, default=0)
    args = ap.parse_args()
    if args.cmd == "report":
        print(report())
    else:
        r = occupancy(args.threads, args.regs, args.smem)
        print(f"blocks/SM={r['blocks_per_sm']} warps/SM={r['warps_per_sm']} "
              f"occupancy={100 * r['occupancy']:.1f}% limited by {r['limiter']} {r['by_resource']}")


if __name__ == "__main__":
    main()
