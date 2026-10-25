#!/usr/bin/env python3
"""Quorum availability of a consensus cluster (Raft, etcd): exact formula and Monte Carlo check.

A cluster of n members commits a write once a majority q = n // 2 + 1 has stored it, so it
tolerates f = (n - 1) // 2 member failures. If each member is up with probability a,
INDEPENDENTLY of the others, the probability that a quorum is up is the binomial tail

    P(n, a) = sum_{k=q}^{n} C(n, k) * a**k * (1 - a)**(n - k)

Independence is an assumption, not a fact: members that share a rack, a power feed or a
switch fail together. The `racks` command models this with failure domains: a domain is up
with probability r, and a member is up when its domain is up and the member itself is up.

Usage (from this directory):
    python3 quorum.py table --a 0.99 0.999
    python3 quorum.py racks --a 0.999 --r 0.9995 --layout 5 --layout 2,2,1 --layout 1,1,1
    python3 quorum.py check --trials 100000 --seed 2026
"""
import argparse
import math
import random
import sys
from itertools import product

MINUTES_PER_30_DAYS = 30 * 24 * 60  # 43 200, the month used for error budgets in chapter 4


def quorum(n: int) -> int:
    """Votes needed for a majority of n members."""
    if n < 1:
        raise ValueError("a cluster has at least one member")
    return n // 2 + 1


def tolerated(n: int) -> int:
    """Member failures a cluster of n members survives without losing quorum."""
    return n - quorum(n)


def p_at_least(m: int, q: int, a: float) -> float:
    """Probability that at least q of m independent members (each up with probability a) are up."""
    if q > m:
        return 0.0
    return sum(math.comb(m, k) * a**k * (1 - a) ** (m - k) for k in range(q, m + 1))


def p_quorum(n: int, a: float) -> float:
    """Probability that a cluster of n independent members keeps its quorum."""
    return p_at_least(n, quorum(n), a)


def p_quorum_domains(layout, a: float, r: float) -> float:
    """Exact quorum probability when members are grouped in failure domains.

    layout: number of members in each domain, e.g. (2, 2, 1) for five members on three racks.
    Each domain is up with probability r (independently); a member is up with probability a
    given that its domain is up, and down if its domain is down.
    """
    n = sum(layout)
    q = quorum(n)
    total = 0.0
    for states in product((True, False), repeat=len(layout)):
        weight = math.prod(r if up else 1 - r for up in states)
        reachable = sum(c for c, up in zip(layout, states) if up)
        total += weight * p_at_least(reachable, q, a)
    return total


def simulate(layout, a: float, r: float, trials: int, rng: random.Random) -> float:
    """Monte Carlo estimate of the quorum probability (same model as p_quorum_domains)."""
    n = sum(layout)
    q = quorum(n)
    ok = 0
    for _ in range(trials):
        up = 0
        for count in layout:
            if rng.random() < r:
                up += sum(1 for _ in range(count) if rng.random() < a)
        if up >= q:
            ok += 1
    return ok / trials


def cmd_table(args) -> int:
    print("members  quorum  tolerated  " + "  ".join(f"P(quorum) a={a:<7g} U (min/30 d)" for a in args.a))
    for n in range(1, args.max_members + 1):
        cells = []
        for a in args.a:
            p = p_quorum(n, a)
            cells.append(f"{p:.9f}  {1 - p:.2e} ({(1 - p) * MINUTES_PER_30_DAYS:9.4f})")
        print(f"{n:7d}  {quorum(n):6d}  {tolerated(n):9d}  " + "  ".join(cells))
    print("U = 1 - P(quorum), the fraction of time without quorum if members fail independently;")
    print("minutes per 30-day month in parentheses (43 200 minutes, as in chapter 4).")
    return 0


def parse_layout(text: str):
    layout = tuple(int(x) for x in text.split(","))
    if not layout or any(c < 1 for c in layout):
        raise argparse.ArgumentTypeError(f"bad layout {text!r}: use e.g. 5 or 2,2,1")
    return layout


def cmd_racks(args) -> int:
    print(f"member availability a = {args.a:g}, failure-domain availability r = {args.r:g}")
    for layout in args.layout:
        n = sum(layout)
        p_ind = p_quorum(n, args.a)
        p_dom = p_quorum_domains(layout, args.a, args.r)
        label = "+".join(str(c) for c in layout)
        print(f"layout {label:<7} ({n} members, {len(layout)} domain(s)): P(quorum) = {p_dom:.9f}, "
              f"U = {1 - p_dom:.2e} ({(1 - p_dom) * MINUTES_PER_30_DAYS:.4f} min/30 d); "
              f"independent members only: U = {1 - p_ind:.2e}")
    return 0


# Cases where the unavailability is large enough to be measured by simulation: the formula
# is the same for a = 0.99 or 0.999, where a Monte Carlo run would see almost no failure.
CHECK_CASES = [
    ((3,), 0.9, 1.0),
    ((5,), 0.9, 1.0),
    ((5,), 0.8, 1.0),
    ((4,), 0.8, 1.0),
    ((3,), 0.6, 1.0),
    ((5,), 0.9, 0.95),
    ((2, 2, 1), 0.9, 0.95),
    ((1, 1, 1), 0.9, 0.95),
]


def cmd_check(args) -> int:
    rng = random.Random(args.seed)
    failures = 0
    print(f"Monte Carlo check: {args.trials} trials per case, seed {args.seed}, tolerance {args.sigmas:g} standard errors")
    for layout, a, r in CHECK_CASES:
        exact = p_quorum_domains(layout, a, r)
        if r == 1.0:
            assert abs(exact - p_quorum(sum(layout), a)) < 1e-12
        est = simulate(layout, a, r, args.trials, rng)
        se = math.sqrt(exact * (1 - exact) / args.trials)
        ok = abs(est - exact) <= args.sigmas * se
        failures += not ok
        label = "+".join(str(c) for c in layout)
        print(f"layout {label:<6} a={a:<4g} r={r:<5g} exact {exact:.5f}  simulated {est:.5f}  "
              f"|diff| {abs(est - exact):.5f} <= {args.sigmas * se:.5f}  {'ok' if ok else 'FAIL'}")
    if failures:
        print(f"{failures} case(s) outside tolerance")
        return 1
    print("formula and simulation agree")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("table", help="exact quorum probabilities for 1..N members")
    t.add_argument("--a", type=float, nargs="+", default=[0.99, 0.999], help="member availability")
    t.add_argument("--max-members", type=int, default=7)
    t.set_defaults(func=cmd_table)
    k = sub.add_parser("racks", help="quorum probability with failure domains (racks, power feeds)")
    k.add_argument("--a", type=float, default=0.999, help="member availability given its domain is up")
    k.add_argument("--r", type=float, default=0.9995, help="failure-domain availability")
    k.add_argument("--layout", type=parse_layout, action="append", required=True, help="members per domain, e.g. 2,2,1")
    k.set_defaults(func=cmd_racks)
    c = sub.add_parser("check", help="compare the formula with a seeded Monte Carlo simulation")
    c.add_argument("--trials", type=int, default=100000)
    c.add_argument("--seed", type=int, default=2026)
    c.add_argument("--sigmas", type=float, default=4.0)
    c.set_defaults(func=cmd_check)
    args = ap.parse_args(argv)
    for a in (args.a if isinstance(getattr(args, "a", None), list) else [getattr(args, "a", 0.5)]):
        if not 0.0 <= a <= 1.0:
            ap.error("availabilities are probabilities between 0 and 1")
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
