#!/usr/bin/env python3
"""Toy LLM inference engine: static vs continuous batching, reserved vs paged KV cache.

Everything runs in SIMULATED time: no GPU, no wall clock, no randomness outside a fixed-seed LCG.
One engine step = one forward pass of the whole running batch, which gives every running sequence
one new token. Its duration follows the memory roofline of chapter 9 (weights + KV read once per
step, over the HBM bandwidth) plus a compute term for the prompt tokens prefilled in that step.

Policies
  static      request-level batching: a batch is formed when the engine is idle and runs until its
              LAST sequence finishes; finished sequences leave their slot empty.
  continuous  iteration-level batching (Orca, OSDI 2022): after every step, finished sequences leave
              and waiting requests join while a slot and enough KV cache are free.
KV accounting
  reserve     a request reserves prompt + max_tokens slots at admission (contiguous allocation).
  paged       a request holds ceil(tokens / block) blocks and grows one block at a time (PagedAttention);
              when a block is missing, the youngest running sequence is preempted and recomputed later.

Usage:
  python3 sim.py                 # offline workload (all requests at t=0), three engines compared
  python3 sim.py --sweep         # online workload, SLO attainment and goodput vs arrival rate
"""
import argparse
import math
from collections import deque
from dataclasses import dataclass


@dataclass(frozen=True)
class Engine:
    max_seqs: int = 32                 # slots per step (vLLM: max_num_seqs)
    kv_budget_tokens: int = 16384      # KV cache capacity in tokens (toy value, far below a real GPU)
    block: int = 16                    # tokens per KV block (paged accounting)
    max_tokens: int = 1024             # generation cap (what "reserve" sets aside)
    weights_bytes: float = 16.38e9     # Qwen3-8B in BF16 (chapter 9, example 9.2)
    kv_bytes_per_token: int = 147456   # 2 x 36 layers x 8 KV heads x 128 x 2 bytes
    mem_bw: float = 3.35e12            # H100 SXM HBM bandwidth, bytes/s (NVIDIA product page)
    prefill_s_per_token: float = 16.6e-6  # 2 x 8.19e9 FLOP / 989e12 FLOP/s, a lower bound


@dataclass(frozen=True)
class Request:
    rid: int
    arrival: float   # seconds (simulated)
    prompt: int      # prompt tokens
    output: int      # tokens to generate


def lcg(seed):
    """Deterministic uniform numbers in [0, 1): same sequence on every machine and Python version."""
    x = seed % 2**31
    while True:
        x = (1103515245 * x + 12345) % 2**31
        yield x / 2**31


def workload(n=64, seed=1, rate=None, prompt=(64, 512), out_min=16, out_max=1024):
    """n requests; output lengths log-uniform in [out_min, out_max] (a long tail, like CoT rollouts).
    rate=None: all arrive at t=0 (offline rollouts); otherwise Poisson arrivals at `rate` req/s."""
    u = lcg(seed)
    t, reqs = 0.0, []
    for i in range(n):
        p = prompt[0] + int(next(u) * (prompt[1] - prompt[0] + 1))
        o = int(round(out_min * (out_max / out_min) ** next(u)))
        if rate:
            t += -math.log(1.0 - next(u)) / rate
        reqs.append(Request(i, t, p, o))
    return reqs


def percentile(values, q):
    """Nearest-rank percentile (deterministic, no interpolation)."""
    v = sorted(values)
    return v[max(0, math.ceil(q / 100 * len(v)) - 1)]


def simulate(reqs, eng=Engine(), policy="continuous", kv="paged"):
    if policy not in ("static", "continuous") or kv not in ("reserve", "paged"):
        raise ValueError("policy: static|continuous ; kv: reserve|paged")
    if max(r.prompt for r in reqs) + eng.max_tokens > eng.kv_budget_tokens:
        raise ValueError("a single request does not fit in the KV budget")
    if any(r.output > eng.max_tokens for r in reqs):
        raise ValueError("output longer than max_tokens")

    def held(s):          # KV slots a running sequence holds after this step
        if kv == "reserve":
            return s["req"].prompt + eng.max_tokens
        return math.ceil((s["req"].prompt + s["gen"] + 1) / eng.block) * eng.block

    pending = deque(sorted(reqs, key=lambda r: (r.arrival, r.rid)))
    queue, running = deque(), []
    gen = {r.rid: 0 for r in reqs}
    first, done = {}, {}
    clock, steps, preemptions, useful, slot_steps, max_running, max_kv = 0.0, 0, 0, 0, 0, 0, 0
    running_sum = 0
    while pending or queue or running:
        while pending and pending[0].arrival <= clock:
            queue.append(pending.popleft())
        if not running and not queue:
            clock = pending[0].arrival
            continue
        prefill = 0
        if policy == "continuous" or not running:
            while queue and len(running) < eng.max_seqs:
                cand = {"req": queue[0], "gen": gen[queue[0].rid]}
                if sum(held(s) for s in running) + held(cand) > eng.kv_budget_tokens:
                    break
                queue.popleft()
                running.append(cand)
                prefill += cand["req"].prompt + cand["gen"]   # a recomputed sequence re-prefills its output too
        if kv == "paged":   # the next token needs a block: preempt the youngest sequence (recompute later)
            # Admission above never exceeds the budget, so a victim is always a sequence admitted in an
            # earlier step: its KV is dropped and it re-prefills prompt + generated tokens when readmitted.
            while sum(held(s) for s in running) > eng.kv_budget_tokens:
                victim = running.pop()
                preemptions += 1
                queue.appendleft(victim["req"])
        if not running:     # cannot happen with a valid budget, kept as a guard against a silent stall
            raise RuntimeError("no sequence fits in the KV budget")
        kv_used = sum(held(s) for s in running)
        max_kv = max(max_kv, kv_used)
        ctx = sum(s["req"].prompt + s["gen"] for s in running)
        dt = (eng.weights_bytes + ctx * eng.kv_bytes_per_token) / eng.mem_bw + prefill * eng.prefill_s_per_token
        clock += dt
        steps += 1
        slot_steps += eng.max_seqs
        useful += len(running)
        running_sum += len(running)
        max_running = max(max_running, len(running))
        still = []
        for s in running:
            s["gen"] += 1
            gen[s["req"].rid] = s["gen"]
            first.setdefault(s["req"].rid, clock)
            if s["gen"] == s["req"].output:
                done[s["req"].rid] = clock
            else:
                still.append(s)
        running = still
    ttft = [first[r.rid] - r.arrival for r in reqs]
    tpot = [(done[r.rid] - first[r.rid]) / (r.output - 1) for r in reqs if r.output > 1]
    return {
        "policy": policy, "kv": kv, "requests": len(done), "steps": steps,
        "useful_tokens": useful, "makespan_s": clock, "tokens_per_s": useful / clock,
        "slot_util": useful / slot_steps, "mean_running": running_sum / steps, "max_running": max_running,
        "max_kv_tokens": max_kv, "preemptions": preemptions,
        "ttft_p50_ms": 1e3 * percentile(ttft, 50), "ttft_p95_ms": 1e3 * percentile(ttft, 95),
        "tpot_p50_ms": 1e3 * percentile(tpot, 50), "tpot_p95_ms": 1e3 * percentile(tpot, 95),
        "_ttft": ttft, "_tpot": tpot,
    }


def attainment(res, ttft_slo_s, tpot_slo_s):
    """Share of requests that meet BOTH the TTFT and the TPOT objectives (DistServe's SLO attainment)."""
    ok = sum(1 for a, b in zip(res["_ttft"], res["_tpot"]) if a <= ttft_slo_s and b <= tpot_slo_s)
    return ok / len(res["_ttft"])


ENGINES = [("static", "reserve"), ("continuous", "reserve"), ("continuous", "paged")]


def offline_table(n=64, seed=1, eng=Engine()):
    reqs = workload(n=n, seed=seed)
    rows = [simulate(reqs, eng, p, k) for p, k in ENGINES]
    print(f"offline workload: {n} requests at t=0, seed {seed}, {sum(r.output for r in reqs)} output tokens ; "
          f"max_seqs={eng.max_seqs}, KV budget={eng.kv_budget_tokens} tokens")
    print(f"{'policy':>10} {'kv':>8} {'steps':>6} {'time s':>7} {'tok/s':>7} {'slot use':>8} "
          f"{'mean run':>8} {'max run':>7} {'preempt':>7}")
    for r in rows:
        print(f"{r['policy']:>10} {r['kv']:>8} {r['steps']:>6} {r['makespan_s']:>7.2f} {r['tokens_per_s']:>7.0f} "
              f"{r['slot_util']:>8.2f} {r['mean_running']:>8.1f} {r['max_running']:>7} {r['preemptions']:>7}")
    return rows


def sweep(rates=(4, 8, 12, 16, 20, 24), n=400, seed=3, ttft_slo=0.5, tpot_slo=0.02, target=0.9, eng=Engine()):
    print(f"online workload: {n} requests, Poisson arrivals, seed {seed} ; SLO TTFT <= {ttft_slo*1e3:.0f} ms "
          f"and TPOT <= {tpot_slo*1e3:.0f} ms ; attainment target {target:.0%}")
    print(f"{'rate':>5} {'policy':>10} {'kv':>8} {'tok/s':>7} {'TTFT p95':>9} {'TPOT p95':>9} {'attain':>7}")
    best = {}
    for rate in rates:
        reqs = workload(n=n, seed=seed, rate=rate)
        for p, k in ENGINES:
            r = simulate(reqs, eng, p, k)
            a = attainment(r, ttft_slo, tpot_slo)
            if a >= target:
                best[(p, k)] = max(best.get((p, k), 0), rate)
            print(f"{rate:>5} {p:>10} {k:>8} {r['tokens_per_s']:>7.0f} {r['ttft_p95_ms']:>7.0f}ms "
                  f"{r['tpot_p95_ms']:>7.1f}ms {a:>7.2f}")
    for p, k in ENGINES:
        print(f"goodput ({p}, {k}): {best.get((p, k), 0)} req/s on 1 simulated GPU (highest swept rate meeting the target)")
    return best


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--sweep", action="store_true", help="online SLO / goodput sweep instead of the offline table")
    ap.add_argument("--n", type=int, default=None)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--max-seqs", type=int, default=Engine.max_seqs)
    ap.add_argument("--kv-budget", type=int, default=Engine.kv_budget_tokens)
    ap.add_argument("--ttft-slo-ms", type=float, default=500.0)
    ap.add_argument("--tpot-slo-ms", type=float, default=20.0)
    ap.add_argument("--rates", type=float, nargs="+", default=[4, 8, 12, 16, 20, 24])
    a = ap.parse_args()
    eng = Engine(max_seqs=a.max_seqs, kv_budget_tokens=a.kv_budget)
    if a.sweep:
        sweep(rates=a.rates, n=a.n or 400, seed=a.seed or 3, ttft_slo=a.ttft_slo_ms / 1e3,
              tpot_slo=a.tpot_slo_ms / 1e3, eng=eng)
    else:
        offline_table(n=a.n or 64, seed=a.seed or 1, eng=eng)


if __name__ == "__main__":
    main()
