"""Part C: tell a SYSTEM regression from a MODEL regression by joining system metrics and run metrics in MLflow.

Three simulated 2-hour runs of the same configuration (seeded; the physics below is an assumption, not a measurement):
  baseline  nothing wrong
  thermal   at step 600 one GPU's SM clock falls to 65 %: tokens/s drops, loss per STEP is unchanged
  lrbug     at step 600 the learning rate is 3x too high: tokens/s unchanged, loss per STEP departs from the baseline
Metrics go through the real MLflow tracking API (SQLite backend in a temporary directory). The verdict compares each run to the baseline.

    python3 regress.py      (needs `pip install mlflow-skinny sqlalchemy alembic`; prints SKIPPED and exits 0 when MLflow is absent)
"""
import math
import random
import sys
import tempfile

import drift

STEPS, BREAK = 1200, 600
T0, COMP = 100.0, 0.8          # tokens/s per GPU-step unit and the share of a step spent computing (assumed)


def make_run(kind, seed):
    rng = random.Random(seed)
    rows = []
    for step in range(STEPS):
        clock = 1.0
        lr_factor = 1.0
        if step >= BREAK and kind == "thermal":
            clock = 0.65                                   # the slowest GPU sets the pace of a synchronous step
        if step >= BREAK and kind == "lrbug":
            lr_factor = 3.0
        tps = T0 / ((1 - COMP) + COMP / clock) * rng.gauss(1, 0.01)
        loss = 2.0 + 6.0 / (1 + step / 80.0)               # the deterministic part of the curve
        if lr_factor > 1:
            loss += 0.4 * math.log(lr_factor) * (step - BREAK) / 100.0   # slow loss degradation
        rows.append((step, tps, loss + rng.gauss(0, 0.01), 1980.0 * clock * rng.gauss(1, 0.002)))
    return rows


def log_run(mlflow, name, rows, params):
    with mlflow.start_run(run_name=name) as run:
        mlflow.log_params(params)
        mlflow.set_tags({"git_commit": "0123abc", "dataset": "corpus-v7"})
        from mlflow.entities import Metric
        batch = [Metric(key, value, 0, step) for step, tps, loss, clock in rows
                 for key, value in (("tokens_per_second", tps), ("loss", loss), ("sm_clock_min_mhz", clock))]
        client = mlflow.tracking.MlflowClient()
        for i in range(0, len(batch), 1000):                       # log_batch accepts up to 1000 metrics per call
            client.log_batch(run.info.run_id, metrics=batch[i:i + 1000])
        return run.info.run_id


def history(client, run_id, key):
    return [m.value for m in sorted(client.get_metric_history(run_id, key), key=lambda m: m.step)]


def verdict(client, base_id, run_id):
    tps, base_tps = history(client, run_id, "tokens_per_second"), history(client, base_id, "tokens_per_second")
    loss, base_loss = history(client, run_id, "loss"), history(client, base_id, "loss")
    clk = history(client, run_id, "sm_clock_min_mhz")
    i = drift.cusum_drop(tps)
    fixed = drift.fixed_threshold(tps)
    tps_delta = sum(tps[BREAK + 50:]) / len(tps[BREAK + 50:]) / (sum(base_tps[BREAK + 50:]) / len(base_tps[BREAK + 50:])) - 1
    loss_gap = sum(loss[-100:]) / 100 - sum(base_loss[-100:]) / 100       # same STEPS compared: loss per step
    clk_delta = sum(clk[BREAK + 50:]) / len(clk[BREAK + 50:]) / (sum(history(client, base_id, "sm_clock_min_mhz")[BREAK + 50:]) / len(clk[BREAK + 50:])) - 1
    kind = ("SYSTEM (throughput moved, loss per step did not; slowest SM clock moved too)"
            if abs(tps_delta) > 0.05 and abs(loss_gap) < 0.05 and abs(clk_delta) > 0.05 else
            "MODEL or DATA (loss per step moved, throughput did not)" if abs(loss_gap) >= 0.05 and abs(tps_delta) <= 0.05 else
            "no regression" if abs(tps_delta) <= 0.05 and abs(loss_gap) < 0.05 else "MIXED: investigate")
    return dict(cusum_step=i, fixed_step=fixed, tps_delta=tps_delta, loss_gap=loss_gap, clk_delta=clk_delta, kind=kind)


def main():
    try:
        import mlflow
        from mlflow.tracking import MlflowClient
    except ImportError:
        print("SKIPPED part C: mlflow not installed (pip install mlflow-skinny sqlalchemy alembic)")
        return 0
    with tempfile.TemporaryDirectory() as tmp:
        mlflow.set_tracking_uri(f"sqlite:///{tmp}/mlflow.db")   # the file store is in maintenance mode in MLflow 3.17
        mlflow.set_experiment("regression-triage")
        client = MlflowClient()
        params = {"lr": 3e-4, "global_batch": 1024, "seed": 1}
        ids = {k: log_run(mlflow, k, make_run(k, seed), params) for k, seed in (("baseline", 1), ("thermal", 2), ("lrbug", 3))}
        out = {}
        for k in ("thermal", "lrbug"):
            out[k] = verdict(client, ids["baseline"], ids[k])
            r = out[k]
            print(f"{k:<8} tokens/s {r['tps_delta']:+.1%}  loss gap at equal step {r['loss_gap']:+.3f}  "
                  f"slowest clock {r['clk_delta']:+.1%}  CUSUM alarm at step {r['cusum_step']}  "
                  f"-10 % threshold alarm at step {r['fixed_step']}\n         verdict: {r['kind']}")
        ok = out["thermal"]["kind"].startswith("SYSTEM") and out["lrbug"]["kind"].startswith("MODEL")
        print("OK part C: both regressions classified correctly" if ok else "FAIL part C")
        return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
