# Lab 15.2 — Demand forecast and commitment (module 15, `finops-capacity`)

From a weekly demand history to a capacity to commit, with its risks. **The demand history is SYNTHETIC** (made-up
model in `forecast.synth_history`: growth, yearly season, noise, training campaigns) and **the prices are FICTIONAL**
(`r` = committed GPU-hour, `o` = on-demand GPU-hour, arbitrary units). Replace the history by your own scheduler
export (lab 15.1) and the prices by dated quotes.

```
starter/forecast.py   provided: synthetic history, trend + season fit, bootstrap scenarios, backtest
starter/commit.py     four functions to write: cost, optimal_commit, best_commit_grid, risk_report
reference/            reference solution (read it after your own attempt); demo.py runs the whole pipeline
tests/                17 tests; IMPL=starter|reference selects the code under test
verify.sh             proves: reference green, starter red
```

```bash
export PYTHON=/path/to/python             # needs numpy and pytest
IMPL=starter $PYTHON -m pytest -q tests    # your work: 10 failures out of 17 at the start
PYTHON=$PYTHON bash verify.sh              # reference green (17), starter red (10 failures)
cd reference && $PYTHON demo.py            # the pipeline; add --cap 20 --penalty 20 for a GPU shortage
cd reference && $PYTHON demo.py --seeds 8  # backtest on 8 synthetic histories
```

The result to understand: committing `L` GPUs for the whole horizon minimizes the mean cost when
`P(D > L) = r/o`, i.e. `L` is the quantile `1 - r/o` of the demand (newsvendor rule). A small discount (r close to o)
means committing only the demand level that is exceeded most of the time; a shortage of on-demand capacity pushes
the commitment up. The test `test_probability_of_exceeding_the_commitment_is_the_price_ratio` checks it by simulation.

Limits, stated on purpose: one flat commitment for the whole year (no ramp, no mix of terms), independent weeks
beyond a 4-week block bootstrap, no cost of capital, no resale of unused commitment, demand measured in GPUs and
not in jobs (no fragmentation, no gang constraint).
