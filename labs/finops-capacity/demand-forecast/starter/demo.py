#!/usr/bin/env python3
"""End-to-end demo on SYNTHETIC data: history -> fit -> scenarios -> commitment and risk."""
import argparse
import json
import sys

import numpy as np

import commit
import forecast


def run(seed=0, weeks_history=104, horizon=52, n_scen=2000, r=2.6, o=4.0, cap=None, penalty=0.0):
    d = forecast.synth_history(weeks_history, seed=seed)
    fit = forecast.fit_trend_season(d)
    sc = forecast.scenarios(fit, horizon, n_scen, seed=seed + 1)
    if cap is None and penalty == 0.0:
        L = commit.optimal_commit(sc, r, o)
    else:
        L, _ = commit.best_commit_grid(sc, r, o, cap, penalty)
    rep = commit.risk_report(L, sc, r, o, cap, penalty)
    rep["saving_vs_all_on_demand"] = 1.0 - rep["mean_cost"] / rep["all_on_demand_mean_cost"]
    rep["critical_ratio"] = 1.0 - r / o
    rep["growth_per_year_fitted"] = forecast.growth_per_year(fit)
    rep["demand_next_year_mean_gpus"] = float(sc.mean())
    rep["demand_next_year_p10_p90"] = [float(np.quantile(sc, 0.1)), float(np.quantile(sc, 0.9))]
    for name, level in (("commit_mean", sc.mean()), ("commit_peak", sc.max())):
        rep[name + "_mean_cost"] = float(commit.cost(level, sc, r, o, cap, penalty).mean())
    rep["backtest"] = forecast.backtest(d, split=78, seed=seed)
    return rep


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--r", type=float, default=2.6, help="committed price per GPU-hour (FICTIONAL)")
    ap.add_argument("--o", type=float, default=4.0, help="on-demand price per GPU-hour (FICTIONAL)")
    ap.add_argument("--cap", type=float, default=None, help="max on-demand GPUs obtainable at once")
    ap.add_argument("--penalty", type=float, default=0.0, help="cost of one unserved GPU-hour")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--seeds", type=int, default=0, help="backtest on this many synthetic histories and summarize")
    a = ap.parse_args(argv)
    if a.seeds:
        rows = [forecast.backtest(forecast.synth_history(104, seed=s), 78, seed=s) for s in range(a.seeds)]
        wins = sum(r["mae_model"] < r["mae_naive"] for r in rows)
        cov = sorted(r["coverage_10_90"] for r in rows)
        print("backtest on %d SYNTHETIC histories: model beats naive in %d, 10-90%% band coverage min %.0f %% median %.0f %% max %.0f %%"
              % (a.seeds, wins, 100 * cov[0], 100 * cov[len(cov) // 2], 100 * cov[-1]))
        return 0
    rep = run(seed=a.seed, r=a.r, o=a.o, cap=a.cap, penalty=a.penalty)
    if a.json:
        json.dump(rep, sys.stdout, indent=1)
        print()
        return 0
    print("SYNTHETIC history, FICTIONAL prices (u per GPU-hour): r=%.2f o=%.2f cap=%s penalty=%.2f" % (a.r, a.o, a.cap, a.penalty))
    print("fitted growth: %+.0f %%/year   next-year demand: mean %.0f GPUs, p10-p90 %.0f-%.0f"
          % (100 * rep["growth_per_year_fitted"], rep["demand_next_year_mean_gpus"], *rep["demand_next_year_p10_p90"]))
    print("critical ratio 1-r/o = %.3f -> commit %.0f GPUs" % (rep["critical_ratio"], rep["commit_gpus"]))
    print("P(week above commitment)=%.3f  unused commitment=%.1f %%  P(some unmet demand)=%.3f"
          % (rep["p_week_above_commit"], 100 * rep["unused_commit_frac"], rep["p_scenario_with_unmet"]))
    print("mean yearly cost: %.0f (all on-demand %.0f, saving %.1f %%)  p95 %.0f"
          % (rep["mean_cost"], rep["all_on_demand_mean_cost"], 100 * rep["saving_vs_all_on_demand"], rep["p95_cost"]))
    print("commit the mean: %.0f   commit the peak: %.0f" % (rep["commit_mean_mean_cost"], rep["commit_peak_mean_cost"]))
    b = rep["backtest"]
    print("backtest 78/26 weeks: MAE model %.1f vs naive %.1f GPUs, 10-90%% band covers %.0f %% of weeks"
          % (b["mae_model"], b["mae_naive"], 100 * b["coverage_10_90"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
