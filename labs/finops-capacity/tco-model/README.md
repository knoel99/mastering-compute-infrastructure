# Lab 15.3 — Parametric TCO model (module 15, `finops-capacity`)

A tested Python tool that compares the cost of one **useful** GPU-hour under five regimes: owned hardware,
long-term rental, one-year reservation, on-demand and spot.

**Every price in `assumptions.yaml` is FICTIONAL** (arbitrary units `u`). The only published figure is the maximum
power of an 8-GPU node (10.2 kW, NVIDIA DGX H100 user guide, read 2026-10-24). Replace the values with your own
dated quotes before drawing any conclusion about a real purchase.

```
assumptions.yaml  fictional inputs, one place for every hypothesis
decision_matrix.py weighted decision matrix + robustness to the weights (FICTIONAL example of chapter 8; `python3 decision_matrix.py`)
starter/tco.py    seven functions to write (annuity, capex, power, spot waste, cost per useful hour, break-even, sensitivity)
reference/tco.py  reference solution (read it after your own attempt)
tests/            24 tests; IMPL=starter|reference selects the code under test
verify.sh         proves: reference green, starter red
```

```bash
export PYTHON=/path/to/python            # needs pytest and pyyaml
IMPL=starter $PYTHON -m pytest -q tests   # your work: 18 failures out of 24 at the start
PYTHON=$PYTHON bash verify.sh             # reference green (24), starter red (18 failures)
$PYTHON reference/tco.py assumptions.yaml --breakeven --sensitivity
```

Model in one line: a fixed-cost option (owned, committed) costs `yearly / (8760 * u * g)` per useful GPU-hour, where
`u` (`utilization` in the code, written `a` on the module page) is the fraction of hours allocated and `g` the goodput
of allocated hours; on-demand costs `rate / g`; spot costs `rate / (g * (1 - W))` with `W = sqrt(2C/M) + R/M`, where
`C` is the blocking cost of a checkpoint (the `δ` of module 10), `M` the mean time between interruptions and `R` the
restart cost (Young-Daly first order, module 10 chapter 2, applied in the `resilient-trainer` project).

Limits, stated on purpose: no taxes, no inflation, no volume discounts, no capacity limit on spot or on-demand (a
real GPU shortage makes both unavailable in volume), no data-transfer cost, one hardware generation.
