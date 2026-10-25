#!/usr/bin/env python3
"""Lab 8.4: the sizing formulas of the storage module, as small tested functions.

Every number printed by `python3 iosizing.py demo` is one used on the course page. The inputs of the demo are
EXAMPLE VALUES chosen for the page (they are not measurements of a product); change them to yours.
"""
from __future__ import annotations

import math
import random
import sys
from collections import OrderedDict

GB = 1e9  # decimal units for bandwidths and capacities, as vendors give them
TB = 1e12
GIB = 2**30


# ---------------------------------------------------------------------------- chapter 1: what must flow

def read_bandwidth(consumers: float, samples_per_s_each: float, bytes_per_sample: float) -> float:
    """Aggregate read rate (bytes/s) the training must be fed with: consumers x rate x sample size."""
    return consumers * samples_per_s_each * bytes_per_sample


def checkpoint_state_bytes(params: float, bytes_per_param: float = 14.0) -> float:
    """Checkpoint size. 14 B/param = 2 (bf16 weights) + 12 (fp32 master copy + two Adam moments); gradients are not saved."""
    return params * bytes_per_param


def checkpoint_write_bandwidth(state_bytes: float, interval_s: float, fraction: float) -> float:
    """Aggregate write rate so that persistence takes at most `fraction` of the checkpoint interval: S / (f * tau)."""
    return state_bytes / (fraction * interval_s)


def transfer_time(nbytes: float, bandwidth: float, latency_s: float = 0.0) -> float:
    """alpha-beta: T = alpha + n / B."""
    return latency_s + nbytes / bandwidth


# ---------------------------------------------------------------------------- chapter 2: striping

def stripes_needed(required_bw: float, per_target_bw: float) -> int:
    """Smallest stripe count whose targets together can deliver `required_bw` (one file, ideal scaling)."""
    return max(1, math.ceil(required_bw / per_target_bw))


def aggregate_bandwidth(clients: int, per_client_bw: float, servers: int, per_server_bw: float) -> float:
    """Aggregate throughput of a parallel file system: the narrower of the client side and the server side."""
    return min(clients * per_client_bw, servers * per_server_bw)


# ---------------------------------------------------------------------------- chapter 3/4: metadata and requests

def metadata_operations(n_files: int, ops_per_file: int = 3, epochs: int = 1) -> int:
    """Metadata operations to read every file once per epoch (open + getattr + close = 3 by default)."""
    return n_files * ops_per_file * epochs


def requests_per_second(bandwidth: float, object_bytes: float) -> float:
    return bandwidth / object_bytes


def prefixes_needed(rps: float, per_prefix_rps: float) -> int:
    return max(1, math.ceil(rps / per_prefix_rps))


# ---------------------------------------------------------------------------- chapter 7: caches

def lru_epoch_hit_ratio(cache_fraction: float) -> float:
    """Hit ratio of an LRU cache when every epoch reads the whole dataset in a fresh random order (mean-field).

    Let x = C / D. Between two uses of an item (position q in epoch e-1, p in epoch e) the cache sees the
    D - q last items of epoch e-1 and the p first items of epoch e. The two groups share p (D - q) / D items on
    average, so the number of distinct items in between is (D - q) + p q / D. With u = p/D and v = q/D uniform:

        hit  <=>  (1 - v) + u v <= x  <=>  v (1 - u) >= 1 - x,

    and for a product of two uniform variables P(V W >= a) = 1 - a + a ln a. Hence h(x) = x + (1 - x) ln (1 - x).
    """
    x = min(max(cache_fraction, 0.0), 1.0)
    if x >= 1.0:
        return 1.0
    return x + (1.0 - x) * math.log(1.0 - x)


def pinned_cache_hit_ratio(cache_fraction: float) -> float:
    """Cache that fills once and never evicts (the policy CoorDL calls MinIO): hit ratio = C / D."""
    return min(max(cache_fraction, 0.0), 1.0)


def simulate_epoch_hit_ratio(n_items: int, cache_items: int, epochs: int, policy: str, seed: int = 0) -> float:
    """Simulate `policy` ('lru' or 'pinned') under random-permutation epochs; hit ratio over epochs 2..N."""
    rng = random.Random(seed)
    cache: OrderedDict[int, None] = OrderedDict()
    hits = total = 0
    for e in range(epochs):
        order = list(range(n_items))
        rng.shuffle(order)
        for i in order:
            hit = i in cache
            if e > 0:
                hits += hit
                total += 1
            if policy == "lru":
                if hit:
                    cache.move_to_end(i)
                else:
                    cache[i] = None
                    if len(cache) > cache_items:
                        cache.popitem(last=False)
            elif policy == "pinned":
                if not hit and len(cache) < cache_items:
                    cache[i] = None
            else:
                raise ValueError(policy)
    return hits / total


def seen_probability(nodes: int, epoch: int) -> float:
    """Probability that a shard assigned at random to a node at `epoch` was already assigned to it before."""
    return 1.0 - (1.0 - 1.0 / nodes) ** (epoch - 1)


def required_hit_ratio(target_bw: float, cache_bw: float, backend_bw: float) -> float:
    """Hit ratio needed for the harmonic mix of cache and backend speeds to reach `target_bw`."""
    return (1.0 / backend_bw - 1.0 / target_bw) / (1.0 / backend_bw - 1.0 / cache_bw)


def effective_read_bandwidth(hit_ratio: float, cache_bw: float, backend_bw: float) -> float:
    """Average rate when a fraction `hit_ratio` of the bytes comes from the cache: harmonic mix of the two speeds."""
    return 1.0 / (hit_ratio / cache_bw + (1.0 - hit_ratio) / backend_bw)


# ---------------------------------------------------------------------------- chapter 8: capacity and retention

def retained_checkpoint_bytes(state_bytes: float, run_steps: int, interval_steps: int, keep_last: int,
                              keep_every: int) -> float:
    """Storage held at the end of a run with rotation: the K latest checkpoints plus one every `keep_every` checkpoints."""
    n = run_steps // interval_steps
    long_term = n // keep_every
    return (min(keep_last, n) + long_term) * state_bytes


def peak_checkpoint_bytes(state_bytes: float, keep_last: int) -> float:
    """Peak usage during rotation: the new checkpoint is written and validated before the oldest is deleted."""
    return (keep_last + 1) * state_bytes


def free_space_ok(free_bytes: float, state_bytes: float, margin: float = 0.10) -> bool:
    """True if a new checkpoint (plus a safety margin) fits in the free space of the quota or file system."""
    return free_bytes >= state_bytes * (1.0 + margin)


def monthly_cost(nbytes: float, price_per_tb_month: float, copies: float = 1.0) -> float:
    """Cost per month for `nbytes` stored `copies` times at a price per decimal TB-month (read the price page the same day)."""
    return nbytes / TB * copies * price_per_tb_month


# ---------------------------------------------------------------------------- latency, concurrency, checkpoints

def half_performance_size(alpha_s: float, bandwidth: float) -> float:
    """n_1/2 = alpha * B: the request size that reaches half of the peak bandwidth (alpha-beta model)."""
    return alpha_s * bandwidth


def request_efficiency(nbytes: float, alpha_s: float, bandwidth: float) -> float:
    """Fraction of the peak bandwidth a single request of `nbytes` achieves: (n/B) / (alpha + n/B)."""
    return (nbytes / bandwidth) / (alpha_s + nbytes / bandwidth)


def in_flight(rate_per_s: float, latency_s: float) -> float:
    """Little's law: requests in flight = rate x mean latency."""
    return rate_per_s * latency_s


def sync_overhead(persist_s: float, interval_s: float) -> float:
    """Fraction of time lost when the training loop waits for the whole write."""
    return persist_s / interval_s


def async_overhead(snapshot_s: float, persist_s: float, interval_s: float) -> float:
    """Two-phase checkpoint: the snapshot blocks, and so does any part of the previous write that outlasts the interval."""
    return (snapshot_s + max(0.0, persist_s - interval_s)) / interval_s


def epoch_times(dataset: float, nodes: int, need_per_node: float, backend_total: float, cache_per_node: float,
                epochs: int, assignment: str) -> list[float]:
    """Seconds per epoch when every node reads dataset/nodes bytes per epoch and caches what it reads.

    assignment 'sticky': a node always gets the same shards, so from epoch 2 its share is in its cache.
    assignment 'random': shards are reassigned at random each epoch; a node has already seen a given shard
    with probability 1 - (1 - 1/nodes)^(k-1) at epoch k, bounded by what its cache can hold.
    The cache is never evicted (the 'pinned' policy). Rates are capped by `need_per_node` and, for misses,
    by the node's share of the backend bandwidth.
    """
    share = dataset / nodes
    backend_per_node = backend_total / nodes
    out = []
    for k in range(1, epochs + 1):
        if assignment == "sticky":
            hit = 0.0 if k == 1 else min(1.0, cache_per_node / share)
        elif assignment == "random":
            hit = min(1.0 - (1.0 - 1.0 / nodes) ** (k - 1), cache_per_node / dataset)
        else:
            raise ValueError(assignment)
        rate = need_per_node if hit >= 1.0 else min(need_per_node, backend_per_node / (1.0 - hit))
        out.append(share / rate)
    return out


# ---------------------------------------------------------------------------- demo

def demo(out=sys.stdout) -> dict[str, float]:
    r: dict[str, float] = {}
    p = lambda k, v, unit="": (r.__setitem__(k, v), print(f"{k:34s} {v:16.4g} {unit}", file=out))
    print("# chapter 1 - example values: 256 GPUs", file=out)
    p("ex1.tokens_bw_B_per_s", read_bandwidth(256, 8000, 2), "B/s (tokenised text, 2 B per token, 8000 tokens/s/GPU)")
    p("ex1.images_bw_GB_per_s", read_bandwidth(256, 3000, 110e3) / GB, "GB/s (3000 img/s/GPU, 110 kB per image)")
    p("ex1.video_bw_GB_per_s", read_bandwidth(256, 20, 2e6) / GB, "GB/s (20 clips/s/GPU, 2 MB per clip)")
    p("ex1.image_opens_per_s", 256 * 3000, "opens/s if every image is a file")
    s70 = checkpoint_state_bytes(70e9)
    p("ex1.ckpt_70B_GB", s70 / GB, "GB (14 B per parameter)")
    p("ex1.ckpt_bw_30min_10pct_GB_s", checkpoint_write_bandwidth(s70, 1800, 0.10) / GB, "GB/s (interval 30 min, 10 % of it)")
    p("ex1.restore_120s_GB_s", s70 / 120 / GB, "GB/s (read the whole state in 120 s)")
    print("# chapter 2 - striping", file=out)
    p("ex2.stripes_for_6GB_s", stripes_needed(6 * GB, 1.5 * GB), "targets (6 GB/s wanted, 1.5 GB/s per target)")
    p("ex2.agg_bw_GB_s", aggregate_bandwidth(64, 20 * GB / 8, 12, 15 * GB) / GB, "GB/s (64 clients x 2.5, 12 servers x 15)")
    print("# chapter 3 - metadata and object requests", file=out)
    p("ex3.metadata_ops_per_epoch", metadata_operations(10_000_000), "ops (10 M files, 3 ops each)")
    p("ex3.metadata_ops_shards", metadata_operations(10_000_000 // 1000), "ops (the same data in shards of 1000 samples)")
    rps = requests_per_second(20 * GB, 8 * 2**20)
    p("ex3.get_rps_8MiB_20GBs", rps, "GET/s (20 GB/s with 8 MiB ranges)")
    p("ex3.get_rps_128KiB_20GBs", requests_per_second(20 * GB, 128 * 2**10), "GET/s (20 GB/s with 128 KiB objects)")
    p("ex3.prefixes_128KiB", prefixes_needed(requests_per_second(20 * GB, 128 * 2**10), 5500), "prefixes")
    p("ex3.requests_per_TB_100kB", TB / 100e3, "GET per TB read as 100 kB objects")
    p("ex3.requests_per_TB_16MiB", TB / (16 * 2**20), "GET per TB read as 16 MiB ranges")
    p("ex3.request_ratio", (TB / 100e3) / (TB / (16 * 2**20)), "x fewer requests with 16 MiB ranges")
    p("ex3.prefixes_5500", prefixes_needed(rps, 5500), "prefixes (5500 GET/s each, documented minimum)")
    print("# chapter 6 - checkpoint memory budget", file=out)
    p("ex6.state_per_gpu_GB", s70 / 1024 / GB, "GB per GPU (980 GB over 1024 GPUs)")
    p("ex6.staging_per_node_GB", s70 / 1024 * 8 / GB, "GB per 8-GPU node for one snapshot in flight")
    print("# chapter 7 - caches", file=out)
    p("ex7.required_hit_for_3GB_s", required_hit_ratio(3 * GB, 6 * GB, 1 * GB), "(cache 6 GB/s, backend 1 GB/s, target 3 GB/s)")
    p("ex7.seen_n4_epoch3", seen_probability(4, 3), "(random shard assignment, 4 nodes)")
    p("ex7.seen_n32_epoch2", seen_probability(32, 2), "(32 nodes)")
    p("ex7.seen_n32_epoch10", seen_probability(32, 10), "(32 nodes)")
    for x in (0.25, 0.5, 0.75):
        p(f"ex7.lru_hit_c{int(x*100)}", lru_epoch_hit_ratio(x), "(analytic LRU, random epochs)")
        p(f"ex7.pinned_hit_c{int(x*100)}", pinned_cache_hit_ratio(x), "(cache that never evicts)")
    sim_lru = simulate_epoch_hit_ratio(2000, 1000, 6, "lru")
    sim_pin = simulate_epoch_hit_ratio(2000, 1000, 6, "pinned")
    p("ex7.sim_lru_c50", sim_lru, "(simulated, 2000 items, cache 1000, 6 epochs, seed 0)")
    p("ex7.sim_pinned_c50", sim_pin, "(simulated, same)")
    p("ex7.eff_bw_pinned_c50_GB_s", effective_read_bandwidth(0.5, 6 * GB, 1 * GB) / GB, "GB/s (cache 6 GB/s, backend 1 GB/s, 50 % hits)")
    p("ex7.eff_bw_lru_c50_GB_s", effective_read_bandwidth(lru_epoch_hit_ratio(0.5), 6 * GB, 1 * GB) / GB, "GB/s (same cache, LRU about 15 % hits)")
    print("# chapter 8 - capacity", file=out)
    n_keep = retained_checkpoint_bytes(s70, run_steps=100_000, interval_steps=500, keep_last=3, keep_every=10)
    p("ex8.retained_TB", n_keep / TB, "TB (200 checkpoints, keep last 3 + one in 10)")
    p("ex8.no_rotation_TB", 200 * s70 / TB, "TB (keep everything)")
    p("ex8.peak_keep3_TB", peak_checkpoint_bytes(s70, 3) / TB, "TB (peak during rotation, keep last 3)")
    p("ex8.free_needed_TB", s70 * 1.10 / TB, "TB of free space needed before writing (10 % margin)")
    return r


def exercises(out=sys.stdout) -> dict[str, float]:
    """The numbers of the solutions of the course page (inputs are stated in each exercise)."""
    r: dict[str, float] = {}
    p = lambda k, v, unit="": (r.__setitem__(k, v), print(f"{k:34s} {v:16.6g} {unit}", file=out))
    print("# exercise 1", file=out)
    p("e1.text_MB_s", read_bandwidth(512, 12000, 2) / 1e6, "MB/s")
    p("e1.images_GB_s", read_bandwidth(512, 2500, 120e3) / GB, "GB/s")
    p("e1.ratio", read_bandwidth(512, 2500, 120e3) / read_bandwidth(512, 12000, 2), "x")
    print("# exercise 2", file=out)
    s180 = checkpoint_state_bytes(180e9)
    p("e2.state_TB", s180 / TB, "TB")
    p("e2.write_GB_s", checkpoint_write_bandwidth(s180, 1200, 0.05) / GB, "GB/s (20 min, 5 %)")
    p("e2.restore_GB_s", s180 / 300 / GB, "GB/s (300 s)")
    p("e2.fraction_at_25GB_s", s180 / (25 * GB * 1200), "fraction of the interval")
    p("e2.persist_s_at_25GB_s", s180 / (25 * GB), "s")
    print("# exercise 3 (BeeGFS stripe 4 x 1 MiB, file of 10 MiB)", file=out)
    chunks = [sum(1 for k in range(10) if k % 4 == t) for t in range(4)]
    p("e3.chunks_target0_1", chunks[0], f"chunks on targets 0,1 ; targets 2,3 hold {chunks[2]}")
    print("# exercise 4", file=out)
    p("e4.stripes_exact", 12 / 2.5, "")
    p("e4.stripes_needed", stripes_needed(12 * GB, 2.5 * GB), "targets")
    p("e4.stripes_margin20", stripes_needed(12 * GB * 1.2, 2.5 * GB), "targets (20 % margin)")
    p("e4.default_shortfall", 12 / 2.5, "x too slow with stripe_count = 1")
    p("e4.agg_GB_s", aggregate_bandwidth(64, 3 * GB, 32, 2.5 * GB) / GB, "GB/s (64 clients x 3 GB/s, 32 targets x 2.5 GB/s)")
    p("e4.clients_needed", math.ceil(12 * GB * 1.2 / (3 * GB)), "clients at 3 GB/s to drive 14.4 GB/s")
    print("# exercise 5", file=out)
    rps = requests_per_second(20 * GB, 100e3)
    p("e5.rps_100kB", rps, "GET/s")
    p("e5.prefixes_100kB", prefixes_needed(rps, 5500), "prefixes")
    p("e5.rps_8MiB", requests_per_second(20 * GB, 8 * 2**20), "GET/s")
    p("e5.prefixes_8MiB", prefixes_needed(requests_per_second(20 * GB, 8 * 2**20), 5500), "prefixes")
    print("# exercise 6 (alpha = 5 ms, B = 1 GB/s, 20 kB samples)", file=out)
    p("e6.n_half_MB", half_performance_size(0.005, 1 * GB) / 1e6, "MB")
    for rows in (50, 1000, 100_000):
        n = rows * 20e3
        p(f"e6.rows{rows}_group_MB", n / 1e6, "MB")
        p(f"e6.rows{rows}_efficiency", request_efficiency(n, 0.005, 1 * GB), "")
        p(f"e6.rows{rows}_amplification", rows, "x (bytes read per useful byte, random access)")
        p(f"e6.rows{rows}_samples_per_s_per_conn", 1.0 / transfer_time(n, 1 * GB, 0.005), "samples/s per connection, random access")
    print("# exercise 7 (alpha = 20 ms, 100 MB/s per connection, 1.39 GB/s wanted)", file=out)
    want = 30 * TB / (6 * 3600)
    p("e7.wanted_GB_s", want / GB, "GB/s (30 TB per 6 h epoch)")
    for name, size in (("100kB", 100e3), ("16MiB", 16 * 2**20)):
        t = transfer_time(size, 100e6, 0.020)
        per_conn = size / t
        rate_req = want / size
        p(f"e7.{name}_per_conn_MB_s", per_conn / 1e6, "MB/s per connection")
        p(f"e7.{name}_connections", want / per_conn, "connections (= rate x latency, Little)")
        p(f"e7.{name}_get_per_s", rate_req, "GET/s")
        p(f"e7.{name}_prefixes", prefixes_needed(rate_req, 5500), "prefixes")
    print("# exercise 9 (state 1.2 TB, blocks 240 s)", file=out)
    p("e9.effective_GB_s", 1.2e12 / 240 / GB, "GB/s")
    p("e9.sync_overhead_30min", sync_overhead(240, 1800), "")
    p("e9.async_overhead_30min", async_overhead(3, 240, 1800), "")
    p("e9.async_overhead_5min", async_overhead(3, 240, 300), "")
    p("e9.async_overhead_3min", async_overhead(3, 240, 180), "")
    p("e9.sync_overhead_5min", sync_overhead(240, 300), "")
    p("e9.min_bw_for_3min_GB_s", 1.2e12 / 180 / GB, "GB/s so that the write fits in a 180 s interval")
    print("# exercise 10 (40 TB, 32 nodes, 3 GB/s per node, 40 GB/s backend, 30.72 TB cache per node)", file=out)
    cache = 8 * 3.84 * TB
    p("e10.cache_TB", cache / TB, "TB per node (8 x 3.84 TB)")
    x = cache / (40 * TB)
    p("e10.cache_fraction", x, "of the dataset")
    p("e10.lru_hit_single_node", lru_epoch_hit_ratio(x), "if one node read the whole dataset each epoch")
    p("e10.full_speed_epoch_s", 40 * TB / 32 / (3 * GB), "s")
    st = epoch_times(40 * TB, 32, 3 * GB, 40 * GB, cache, 20, "sticky")
    rd = epoch_times(40 * TB, 32, 3 * GB, 40 * GB, cache, 20, "random")
    for k in (1, 2, 5, 10, 20):
        p(f"e10.epoch{k}_random_s", rd[k - 1], "s")
    p("e10.epoch2_sticky_s", st[1], "s")
    p("e10.total20_random_s", sum(rd), "s")
    p("e10.total20_sticky_s", sum(st), "s")
    p("e10.total20_ratio", sum(rd) / sum(st), "x")
    print("# exercise 11 (120 M files, 3 metadata ops each, 50 000 ops/s assumed)", file=out)
    ops = metadata_operations(120_000_000)
    p("e11.ops_per_epoch", ops, "ops")
    p("e11.metadata_time_h", ops / 50_000 / 3600, "h per epoch")
    p("e11.shards", 120_000_000 / 1000, "shards of 1000 samples")
    p("e11.ops_shards", metadata_operations(120_000), "ops")
    p("e11.ops_shards_s", metadata_operations(120_000) / 50_000, "s")
    p("e11.data_TB", 120e6 * 110e3 / TB, "TB (110 kB per file)")
    p("e11.convert_min_5GB_s", 120e6 * 110e3 / (5 * GB) / 60, "min to read once at 5 GB/s")
    p("e11.convert_bound_h", max(ops / 50_000 / 3600, 120e6 * 110e3 / (5 * GB) / 3600), "h: the conversion pays the metadata bill once more")
    print("# exercise 12", file=out)
    s70 = checkpoint_state_bytes(70e9)
    keep = retained_checkpoint_bytes(s70, 100_000, 500, 3, 10)
    p("e12.ckpt_TB", keep / TB, "TB retained")
    p("e12.hot_TB", keep / TB + 20 + 2, "TB hot (checkpoints + tokenised 20 + logs 2)")
    p("e12.cold_TB", 60.0, "TB raw (cold)")
    p("e12.cost_units_all_hot", (keep / TB + 20 + 2 + 60), "TB x price per TB-month if everything were hot")
    p("e12.cost_units_tiered", (keep / TB + 20 + 2) + 60 * 0.25, "TB-equivalents if raw sits at a quarter of the price")
    p("e12.rotation_saving_TB", (200 * s70 - keep) / TB, "TB saved by the rotation")
    p("e12.peak_TB", peak_checkpoint_bytes(s70, 3) / TB, "TB peak of the checkpoints during rotation")
    p("e12.quota_TB", (keep / TB + 20 + 2 + s70 / TB) * 1.15, "TB quota: (hot + one extra checkpoint) x 1.15")
    p("e12.files_ckpt", 1024 * (3 + 200 // 10), "files held by 1024 ranks x 23 checkpoints")
    return r


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo()
    elif len(sys.argv) > 1 and sys.argv[1] == "exercises":
        exercises()
    else:
        print(__doc__)
        print("usage: python3 iosizing.py demo")
