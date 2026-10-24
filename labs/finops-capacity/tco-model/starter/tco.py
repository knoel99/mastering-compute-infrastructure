#!/usr/bin/env python3
"""Parametric TCO model: owned hardware vs committed rental vs on-demand vs spot.

Money is in arbitrary units (u). Every input lives in a YAML file; the values shipped with the lab
are FICTIONAL examples (see ../assumptions.yaml).

  utilization u : fraction of the year's GPU-hours allocated to jobs, on capacity you pay for
                  whether or not it is used (owned or committed).
  goodput g     : fraction of allocated GPU-hours that produce useful progress.

  cost per useful GPU-hour = yearly cost / (HOURS * u * g)   for fixed-cost options (owned, committed)
                           = hourly rate / g                  for pay-per-use options (on-demand)
                           = hourly rate / (g * (1 - W))      for spot, W = waste from interruptions
"""
import argparse
import copy
import json
import math
import sys

import yaml

HOURS = 8760.0
PAY_PER_USE = ("on_demand", "spot")


def load(path):
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def get_path(d, dotted):
    for key in dotted.split("."):
        d = d[key]
    return d


def set_path(d, dotted, value):
    keys = dotted.split(".")
    for key in keys[:-1]:
        d = d[key]
    d[keys[-1]] = value


def annuity_factor(rate, years):
    """Yearly payment per unit of principal that repays a loan of `years` years at `rate`."""
    raise NotImplementedError("TODO: implement annuity_factor (see the docstring and tests/)")


def annualized_capex(price, life_years, residual_frac, cost_of_capital):
    """Yearly cost of owning an asset: (price - present value of the resale value) as an annuity."""
    raise NotImplementedError("TODO: implement annualized_capex (see the docstring and tests/)")


def owned_components(a, utilization):
    """Yearly cost of one owned GPU, as a dict with the keys amortization, support, staff, facility, energy.

    amortization: annualized (node price * (1 + fabric_storage_frac)) with resale value and cost of capital;
    support: support_frac_per_year * node price; staff: per 100 GPUs; facility: reserved kW * price per kW-month * 12;
    energy: node draw (idle..busy, interpolated on utilization) * PUE * price per kWh * HOURS. All divided per GPU."""
    raise NotImplementedError("TODO: implement owned_components (see the docstring and tests/)")


def waste_fraction(mtbi_hours, checkpoint_minutes, restart_minutes):
    """Young-Daly first-order waste at the best checkpoint interval: W = sqrt(2C/M) + R/M."""
    raise NotImplementedError("TODO: implement waste_fraction (see the docstring and tests/)")


def options(a):
    return ["owned"] + list(a["committed"]) + ["on_demand", "spot"]


def cost_per_useful_hour(a, option, utilization, goodput):
    """Cost of one useful GPU-hour with `option`, at the given utilization and goodput."""
    raise NotImplementedError("TODO: implement cost_per_useful_hour (see the docstring and tests/)")


def breakeven_utilization(a, fixed_option, variable_option, goodput=1.0, lo=0.01, tol=1e-6):
    """Utilization above which `fixed_option` beats `variable_option`; None if it never does,
    `lo` if it already does at `lo`."""
    raise NotImplementedError("TODO: implement breakeven_utilization (see the docstring and tests/)")


SENSITIVITY_PARAMS = [
    "owned.node_price_u", "owned.life_years", "owned.residual_frac", "owned.cost_of_capital",
    "owned.support_frac_per_year", "owned.staff_u_per_year_per_100_gpus", "owned.pue",
    "owned.energy_u_per_kwh", "owned.fabric_storage_frac",
]


def sensitivity(a, utilization, goodput, rel=0.2, params=SENSITIVITY_PARAMS):
    """One-at-a-time +/- rel change of each parameter; rows sorted by decreasing swing of the owned cost."""
    raise NotImplementedError("TODO: implement sensitivity (see the docstring and tests/)")


def table(a, utilizations, goodput):
    rows = []
    for u in utilizations:
        costs = {o: cost_per_useful_hour(a, o, u, goodput) for o in options(a)}
        best = min(costs, key=costs.get)
        rows.append({"utilization": u, "costs": costs, "best": best})
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("assumptions")
    ap.add_argument("--utilization", type=float, nargs="+", default=[0.3, 0.5, 0.7, 0.9])
    ap.add_argument("--goodput", type=float, default=0.9)
    ap.add_argument("--breakeven", action="store_true")
    ap.add_argument("--sensitivity", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    a = load(args.assumptions)
    rows = table(a, args.utilization, args.goodput)
    out = {"goodput": args.goodput, "table": rows}
    if args.breakeven:
        # a break-even exists against pay-per-use options only: two fixed-cost options keep the same ranking at any utilization
        out["breakeven"] = {v: breakeven_utilization(a, "owned", v, args.goodput) for v in PAY_PER_USE}
        mid = args.utilization[len(args.utilization) // 2]
        out["yearly_per_gpu"] = {"owned (u=%.2f)" % mid: sum(owned_components(a, mid).values())}
        out["yearly_per_gpu"].update({k: v["u_per_gpu_hour"] * HOURS for k, v in a["committed"].items()})
    if args.sensitivity:
        out["sensitivity"] = sensitivity(a, args.utilization[len(args.utilization) // 2], args.goodput)
    if args.json:
        json.dump(out, sys.stdout, indent=1)
        print()
        return 0
    names = options(a)
    print("cost per useful GPU-hour (u), goodput=%.2f   [FICTIONAL inputs]" % args.goodput)
    print("%6s " % "util" + " ".join("%12s" % n for n in names) + "  best")
    for r in rows:
        print("%6.2f " % r["utilization"] + " ".join("%12.2f" % r["costs"][n] for n in names) + "  " + r["best"])
    if args.breakeven:
        for v, u in out["breakeven"].items():
            print("breakeven owned vs %-12s: %s" % (v, "never" if u is None else "u* = %.3f" % u))
        for k, v in out["yearly_per_gpu"].items():
            print("yearly cost per GPU, %-18s: %9.0f" % (k, v))
    if args.sensitivity:
        print("sensitivity of the owned cost (+/-20%%) at u=%.2f" % args.utilization[len(args.utilization) // 2])
        for r in out["sensitivity"]:
            print("  %-40s %8.2f .. %8.2f  swing %.2f" % (r["param"], r["low"], r["high"], r["swing"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
