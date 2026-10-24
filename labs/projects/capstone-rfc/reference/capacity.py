"""Capacity and cost model for a partitioned GPU platform (one pool per workload class).

Each class is modelled as an M/M/c queue: Poisson arrivals, exponential service, c = pool GPUs // GPUs per job
servers (gang scheduling: a job needs all its GPUs at once). The approximation ignores bursts, priorities and
fragmentation across pools. Waits grow with the variability of arrivals and of service times (Kingman), so the result is
PROBABLY optimistic, but it is not a guaranteed bound (more regular service times would lower the waits): never a promise.
"""
import math

import yaml


def load(path):
    with open(path) as f:
        return yaml.safe_load(f)


def erlang_c(servers, offered_load):
    """Probability that an arrival has to wait in an M/M/c queue (offered_load = lambda / mu, in Erlangs).
    Returns 1.0 when the queue is unstable (offered_load >= servers)."""
    c, a = servers, offered_load
    if c <= 0:
        return 1.0
    if a >= c:
        return 1.0
    # sum in a numerically safe way: terms a^k / k! built iteratively
    term, total = 1.0, 1.0
    for k in range(1, c):
        term *= a / k
        total += term
    top = term * a / c * c / (c - a)  # a^c / c! * c / (c - a)
    return top / (total + top)


def wait_stats(servers, arrival_per_h, mean_service_h):
    """(utilisation, P(wait), mean wait h, p90 wait h) for an M/M/c queue; infinite waits when unstable."""
    if servers <= 0:
        return 1.0, 1.0, math.inf, math.inf
    mu = 1.0 / mean_service_h
    a = arrival_per_h / mu
    rho = a / servers
    if rho >= 1.0:
        return rho, 1.0, math.inf, math.inf
    pw = erlang_c(servers, a)
    rate = servers * mu - arrival_per_h  # decay rate of the waiting-time tail
    mean = pw / rate
    p90 = 0.0 if pw <= 0.10 else math.log(pw / 0.10) / rate
    return rho, pw, mean, p90


def young_daly_goodput(job_gpus, gpu_failure_rate, ckpt_min, restart_min, extra_rate_per_job_hour=0.0):
    """Fraction of time a job of `job_gpus` GPUs spends on useful work at the Young-Daly checkpoint period.
    Job failure rate = gpus x rate + extra (spot interruptions); M = 1 / rate hours; T* = sqrt(2 C M);
    goodput = 1 - (C/T + (T/2 + R)/M), floored at 5 %. Without any failure (rate 0) there is nothing to checkpoint: 1.0.
    First-order model: reliable while T*/M is small; pessimistic when failures are frequent (T*/M above about 0.3)."""
    rate_per_h = job_gpus * gpu_failure_rate + extra_rate_per_job_hour
    if rate_per_h <= 0.0:
        return 1.0
    mtbf_min = 60.0 / rate_per_h
    t = math.sqrt(2.0 * ckpt_min * mtbf_min)
    waste = ckpt_min / t + (t / 2.0 + restart_min) / mtbf_min
    return max(0.05, 1.0 - waste)


def evaluate(req, design):
    """design = {"pools": {class: pool}} with pool one of
         {"market": "reserved", "gpus": N}   fixed capacity, M/M/c queue, you pay for the capacity every hour;
         {"market": "on_demand"}              elastic: wait = provision_wait_h, you pay for GPU-hours used;
         {"market": "spot"}                   elastic and interruptible: extra failure rate, pay for GPU-hours used.
    Returns per-class rows plus the monthly cost, the budget verdict and the SLO verdicts."""
    hours = req["hours_per_month"]
    rows, total_cost, all_ok = {}, 0.0, True
    for name, spec in req["classes"].items():
        pool = design["pools"][name]
        market = pool["market"]
        extra = req["spot_interruptions_per_job_hour"] if market == "spot" else 0.0
        goodput = young_daly_goodput(spec["gpus_per_job"], req["gpu_failure_rate_per_gpu_hour"],
                                     req["checkpoint_cost_min"], req["restart_cost_min"], extra)
        service_h = spec["mean_work_hours"] / goodput
        used_gpu_h = spec["jobs_per_month"] * spec["gpus_per_job"] * service_h
        price = req["prices_u_per_gpu_hour"][market]
        if market == "reserved":
            servers = pool["gpus"] // spec["gpus_per_job"]
            rho, pw, mean, p90 = wait_stats(servers, spec["jobs_per_month"] / hours, service_h)
            cost = pool["gpus"] * hours * price
        else:
            servers, rho, pw = None, None, 0.0
            mean = p90 = req["provision_wait_h"]
            cost = used_gpu_h * price
        slo = spec["slo"]
        ok = {"p90_wait_h": p90, "mean_wait_h": mean}[slo["metric"]] <= slo["max"]
        all_ok &= ok
        total_cost += cost
        rows[name] = {"market": market, "servers": servers, "goodput": goodput, "service_h": service_h,
                      "used_gpu_h": used_gpu_h, "utilisation": rho, "p_wait": pw, "mean_wait_h": mean,
                      "p90_wait_h": p90, "cost_u": cost, "slo_ok": ok}
    return {"classes": rows, "cost_u": total_cost, "within_budget": total_cost <= req["budget_per_month_u"],
            "all_slo_ok": all_ok}
