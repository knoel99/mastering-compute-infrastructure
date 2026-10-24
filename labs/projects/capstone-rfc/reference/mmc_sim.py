"""Independent check of the M/M/c formulas: event-driven simulation of an M/M/c FIFO queue."""
import heapq
import random


def simulate(servers, arrival_per_h, mean_service_h, n_jobs=60_000, seed=0):
    """Return (mean wait h, P(wait), p90 wait h) over n_jobs arrivals after a warm-up of 10 %."""
    rng = random.Random(seed)
    t = 0.0
    free_at = [0.0] * servers
    heapq.heapify(free_at)
    waits = []
    for _ in range(n_jobs):
        t += rng.expovariate(arrival_per_h)
        start = max(t, free_at[0])
        heapq.heapreplace(free_at, start + rng.expovariate(1.0 / mean_service_h))
        waits.append(start - t)
    waits = waits[n_jobs // 10:]
    waits_sorted = sorted(waits)
    return (sum(waits) / len(waits), sum(1 for w in waits if w > 0) / len(waits), waits_sorted[int(0.9 * len(waits))])
