"""One-sided CUSUM for a slow drop in a noisy series (throughput, tokens/s), next to the fixed threshold it beats."""
import statistics


def cusum_drop(xs, warmup=60, k_sigma=0.5, h_sigma=12.0):
    """Index of the first alarm, or None. Target and sigma come from the first `warmup` samples.
    s_i = max(0, s_{i-1} + (target - x_i) - k); alarm when s_i > h, with k = k_sigma*sigma and h = h_sigma*sigma."""
    base = xs[:warmup]
    target, sigma = statistics.fmean(base), statistics.pstdev(base)
    k, h, s = k_sigma * sigma, h_sigma * sigma, 0.0
    for i, x in enumerate(xs):
        if i < warmup:
            continue
        s = max(0.0, s + (target - x) - k)
        if s > h:
            return i
    return None


def fixed_threshold(xs, warmup=60, drop=0.10):
    """Index of the first sample more than `drop` below the warm-up mean (the usual dashboard alert)."""
    target = statistics.fmean(xs[:warmup])
    return next((i for i, x in enumerate(xs) if i >= warmup and x < (1 - drop) * target), None)


def table(n=1000, n_samples=400, drop_at=200, drop=0.03, sd=0.01):
    """False-alarm rate on healthy series and detection delay after a 3 % drop, for several thresholds h."""
    import random
    def series(seed, d):
        rng = random.Random(seed)
        return [100.0 * (1 - (d if i >= drop_at else 0.0)) * rng.gauss(1, sd) for i in range(n_samples)]
    print(f"{n} healthy and {n} drifting series of {n_samples} samples (noise {sd:.0%}); drop of {drop:.0%} at sample {drop_at}")
    print(f"{'h (sigma)':>10}{'false-alarm series':>20}{'drops found':>13}{'delay median':>14}{'delay p95':>11}")
    for h in (8.0, 12.0, 15.0):
        fa = sum(cusum_drop(series(s, 0.0), h_sigma=h) is not None for s in range(n))
        found = sorted(i - drop_at for i in (cusum_drop(series(s, drop), h_sigma=h) for s in range(n)) if i is not None and i >= drop_at)
        print(f"{h:>10.0f}{fa:>20}{len(found):>13}{statistics.median(found):>14.1f}{found[int(0.95 * (len(found) - 1))]:>11}")
    fixed = sum(fixed_threshold(series(s, drop)) is not None for s in range(n))
    print(f"fixed threshold at -10 % finds {fixed} of {n} drifting series")


if __name__ == "__main__":
    table()
