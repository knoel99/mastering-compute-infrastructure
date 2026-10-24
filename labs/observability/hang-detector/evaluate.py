"""Evaluate detectors on simulated runs: detection rate, false-alarm rate, detection delay.

    python3 evaluate.py            # comparison table + window sweep, 150 healthy + 150 hang + 100 crash runs of 6 h
    python3 evaluate.py --quick    # 40 + 40 + 20 runs
"""
import statistics
import sys

import detectors as D
import sim


def first_alarm(det, obs, after=0.0):
    """First scrape at or after `after` where the detector alarms. The detector sees every scrape from the start,
    so that its state (a stall clock, a phase) is the one it would have in production."""
    for o in obs:
        if det.update(o) and o.t >= after:
            return o.t
    return None


def run_set(factories, seeds, fault, hours):
    """-> {name: list of (alarm_time or None, fault_time or None)}"""
    out = {n: [] for n in factories}
    for seed in seeds:
        obs, tf = sim.simulate(seed, hours=hours, fault=fault)
        for name, make in factories.items():
            out[name].append((first_alarm(make(), obs, after=tf or 0.0), tf))
    return out


def summarize(healthy, hang, crash, hours):
    def pct(xs):
        return 100.0 * sum(xs) / len(xs)
    delays = sorted(a - tf for a, tf in hang if a is not None and a >= tf)
    healthy_hours = len(healthy) * hours
    return {
        "hang_found_pct": pct([a is not None and a >= tf for a, tf in hang]),
        "crash_found_pct": pct([a is not None and a >= tf for a, tf in crash]),
        "healthy_alarm_pct": pct([a is not None for a, _ in healthy]),
        "healthy_alarms": sum(a is not None for a, _ in healthy),
        "healthy_hours": healthy_hours,
        "delay_median": statistics.median(delays) if delays else None,
        "delay_p95": delays[int(0.95 * (len(delays) - 1))] if delays else None,
    }


def evaluate(factories, n_healthy=150, n_hang=150, n_crash=100, hours=6.0):
    h = run_set(factories, range(1000, 1000 + n_healthy), None, hours)
    g = run_set(factories, range(2000, 2000 + n_hang), "hang", hours)
    c = run_set(factories, range(3000, 3000 + n_crash), "crash", hours)
    return {n: summarize(h[n], g[n], c[n], hours) for n in factories}


def fmt(v, spec="{:.0f}"):
    return "-" if v is None else spec.format(v)


def main(argv):
    quick = "--quick" in argv
    size = dict(n_healthy=40, n_hang=40, n_crash=20) if quick else {}
    table = {
        "UtilLow 300 s": lambda: D.UtilLow(300),
        "TensorIdle 300 s": lambda: D.TensorIdle(300),
        "StepStall 300 s": lambda: D.StepStall(300),
        "StepStall 600 s": lambda: D.StepStall(600),
        "Heartbeat 60 s": lambda: D.Heartbeat(60),
        "PhaseAware 240 s": lambda: D.PhaseAware(240),
        "PhaseAware 240 s + Heartbeat 60 s": lambda: D.AnyOf(D.PhaseAware(240), D.Heartbeat(60)),
    }
    res = evaluate(table, **size)
    hh = next(iter(res.values()))["healthy_hours"]
    print(f"Comparison ({hh:.0f} healthy run-hours; hang and crash runs of 6 h; SIMULATED, assumptions in sim.py)")
    print(f"{'detector':<36}{'hangs found %':>14}{'crashes found %':>17}{'healthy runs alarmed %':>24}{'delay median s':>16}")
    for n, r in res.items():
        print(f"{n:<36}{r['hang_found_pct']:>14.0f}{r['crash_found_pct']:>17.0f}{r['healthy_alarm_pct']:>24.1f}{fmt(r['delay_median']):>16}")
    sweep = {}
    for w in (30, 60, 120, 240, 480, 900):
        sweep[f"StepStall {w}"] = (lambda w=w: D.StepStall(w))
        sweep[f"PhaseAware {w}"] = (lambda w=w: D.PhaseAware(w))
    res2 = evaluate(sweep, **size)
    print("\nWindow sweep (alarms on healthy runs fall with the window, the delay grows with it)")
    print(f"{'detector':<20}{'false-alarm runs / 100 run-h':>30}{'delay median s':>16}{'delay p95 s':>13}{'hangs found %':>15}")
    for n, r in res2.items():
        print(f"{n:<20}{100 * r['healthy_alarms'] / r['healthy_hours']:>30.2f}{fmt(r['delay_median']):>16}{fmt(r['delay_p95']):>13}{r['hang_found_pct']:>15.0f}")
    z = [r for r in res2.values() if r["healthy_alarms"] == 0]
    if z:
        print(f"\nZero false alarms only bounds the rate: about 3 / {hh:.0f} h = {3 / hh:.4f} per run-hour at 95 % (rule of three).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
