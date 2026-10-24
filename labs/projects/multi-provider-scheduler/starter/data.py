"""Synthetic offers and jobs. EVERY NUMBER HERE IS INVENTED: prices are in arbitrary units (u per GPU-hour),
hazards and capacities are made up. Do not read them as the market; replace them with data you collect yourself."""
import random
from dataclasses import dataclass


@dataclass(frozen=True)
class Offer:
    id: str
    provider: str
    region: str
    market: str  # "on_demand" | "spot"
    price: float  # u per GPU-hour
    capacity: int  # GPUs available concurrently
    hazard: float  # interruptions per hour of allocation (0 for on_demand)
    startup_min: int  # minutes from allocation to the first useful minute


@dataclass(frozen=True)
class Job:
    id: str
    arrival_min: int
    gpus: int
    work_min: int  # minutes of useful compute needed, uninterrupted
    deadline_min: int  # absolute minute
    ckpt_cost_min: int = 3
    restart_cost_min: int = 10  # reloading state after an interruption


def default_offers():
    return [
        Offer("a-od", "cloud-a", "r1", "on_demand", 10.0, 64, 0.0, 5),
        Offer("a-spot", "cloud-a", "r1", "spot", 4.0, 64, 0.15, 8),
        Offer("b-spot", "cloud-b", "r2", "spot", 3.0, 32, 0.60, 10),
        Offer("c-od", "cloud-c", "r3", "on_demand", 12.0, 64, 0.0, 3),
    ]


def make_jobs(n=30, seed=0, span_days=3):
    """n jobs arriving uniformly over span_days, 8/16/32 GPUs, 6 to 48 hours of work, deadline 1.5x to 2.5x the work."""
    rng = random.Random(f"jobs-{seed}")
    jobs = []
    for i in range(n):
        work = rng.randint(6 * 60, 48 * 60)
        arrival = rng.randint(0, span_days * 24 * 60)
        slack = rng.uniform(1.5, 2.5)
        jobs.append(Job(f"j{i:02d}", arrival, rng.choice([8, 16, 32]), work, arrival + int(work * slack)))
    return sorted(jobs, key=lambda j: (j.arrival_min, j.id))
