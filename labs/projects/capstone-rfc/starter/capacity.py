"""Capacity and cost model — TO WRITE (milestones 1 and 2).

Each workload class is an M/M/c queue (Poisson arrivals, exponential service) with c = pool GPUs // GPUs per job
(gang scheduling). The result is an OPTIMISTIC bound on waiting: it ignores bursts, priorities, fragmentation.
Keep these signatures, tests/test_capacity.py and the RFC linter use them. `load` is given.
"""
import math  # noqa: F401

import yaml


def load(path):
    with open(path) as f:
        return yaml.safe_load(f)


def erlang_c(servers, offered_load):
    """P(an arrival must wait) in an M/M/c queue; offered_load = lambda / mu in Erlangs.
    1.0 when unstable (offered_load >= servers) or without servers. Build a^k/k! iteratively (no factorial overflow)."""
    raise NotImplementedError


def wait_stats(servers, arrival_per_h, mean_service_h):
    """(utilisation, P(wait), mean wait h, p90 wait h). Mean wait = P(wait) / (c mu - lambda);
    the tail is P(W > t) = P(wait) exp(-(c mu - lambda) t), so p90 = 0 if P(wait) <= 0.1 else ln(P(wait)/0.1)/(c mu - lambda).
    Unstable queue (utilisation >= 1) or no server: infinite waits, P(wait) = 1."""
    raise NotImplementedError


def young_daly_goodput(job_gpus, gpu_failure_rate, ckpt_min, restart_min, extra_rate_per_job_hour=0.0):
    """Useful-work fraction at the Young-Daly period. Job failure rate per hour = gpus x rate + extra;
    M = 60 / rate (minutes); T* = sqrt(2 C M); goodput = 1 - (C/T* + (T*/2 + R)/M), floored at 0.05."""
    raise NotImplementedError


def evaluate(req, design):
    """design = {"pools": {class: pool}}, pool = {"market": "reserved", "gpus": N} (fixed capacity, M/M/c, paid every
    hour), {"market": "on_demand"} (elastic: wait = req["provision_wait_h"], paid for GPU-hours used) or
    {"market": "spot"} (elastic, plus req["spot_interruptions_per_job_hour"] added to the failure rate).
    service_h = mean_work_hours / goodput ; used_gpu_h = jobs_per_month x gpus_per_job x service_h.
    Return {"classes": {name: {market, servers, goodput, service_h, used_gpu_h, utilisation, p_wait, mean_wait_h,
    p90_wait_h, cost_u, slo_ok}}, "cost_u", "within_budget", "all_slo_ok"}; an SLO is {"metric": "p90_wait_h"|
    "mean_wait_h", "max": hours}. Elastic pools have servers = utilisation = None and p_wait = 0."""
    raise NotImplementedError
