#!/usr/bin/env python3
"""Topology-aware placement in miniature: in which domain can a gang of N nodes be co-located?

Mirrors the documented semantics of Kueue Topology-Aware Scheduling annotations (v0.20):
  * required  : all pods must fit inside ONE domain of the given level, otherwise the workload waits;
  * preferred : try that level, then go up level by level; if even the top level is too small, the workload is
                admitted spread over several domains.
Levels here: rack (leaf) < block < cluster. `free` maps block -> rack -> free whole nodes.
"""
LEVELS = ["rack", "block", "cluster"]


def capacity(free: dict, level: str) -> list:
    """Free nodes of every domain of `level`."""
    if level == "rack":
        return [n for racks in free.values() for n in racks.values()]
    if level == "block":
        return [sum(racks.values()) for racks in free.values()]
    return [sum(sum(r.values()) for r in free.values())]


def place(free: dict, need: int, level: str, mode: str = "required"):
    """Return (level used, domain capacity) or None if the workload must wait. mode: required | preferred."""
    start = LEVELS.index(level)
    for lv in LEVELS[start:] if mode == "preferred" else [level]:
        fitting = [c for c in capacity(free, lv) if c >= need]
        if fitting:
            return lv, min(fitting)          # best fit: the smallest domain that holds the gang
    return None


if __name__ == "__main__":
    free = {"block-0": {"rack-0": 5, "rack-1": 3}, "block-1": {"rack-2": 6, "rack-3": 2}}
    for need in (6, 8, 12, 17):
        print(f"need {need:>2} nodes | required=rack: {place(free, need, 'rack')} | preferred=rack: {place(free, need, 'rack', 'preferred')}"
              f" | required=block: {place(free, need, 'block')}")
