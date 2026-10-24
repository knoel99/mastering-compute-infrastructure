#!/usr/bin/env python3
"""What does each part of the checkpoint protect? Leave one out and look at the first wrong step.

Reference: 60 uninterrupted steps. Experiment: train 30 steps with a checkpoint every 10, "crash"
(drop the Trainer object), resume from the checkpoint at step 30 and train to 60. A complete
checkpoint reproduces the reference losses exactly; each omission breaks them from step 30 on.
"""
import argparse
import json
import sys
import tempfile
from pathlib import Path

import trainer


def losses_of(tr, lo, hi):
    return [tr.losses[s] for s in range(lo, hi)]


def experiment(omit, steps=60, crash_at=30, ckpt_every=10, seed=0):
    with tempfile.TemporaryDirectory() as ref_dir, tempfile.TemporaryDirectory() as exp_dir:
        ref = trainer.run(ref_dir, steps, ckpt_every=10_000, seed=seed, log=False)
        trainer.run(exp_dir, steps, ckpt_every, seed=seed, omit=omit, stop_after=crash_at, log=False)  # first life
        second = trainer.run(exp_dir, steps, ckpt_every, seed=seed, omit=omit, log=False)  # second life, resumed
        a, b = losses_of(ref, crash_at, steps), losses_of(second, crash_at, steps)
        diffs = [abs(x - y) for x, y in zip(a, b)]
        first = next((crash_at + i for i, d in enumerate(diffs) if d != 0.0), None)
        return {"omit": list(omit) or "nothing", "first_divergent_step": first, "max_abs_loss_diff": max(diffs),
                "final_digest_equal": ref.digest() == second.digest()}


def main(argv=None):
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    rows = [experiment(o) for o in ([], ["optimizer"], ["scheduler"], ["rng"], ["cursor"])]
    print(f"{'omitted':<12} {'first wrong step':>16} {'max |dloss|':>12} {'same final state':>17}")
    for r in rows:
        o = r["omit"] if isinstance(r["omit"], str) else r["omit"][0]
        print(f"{o:<12} {str(r['first_divergent_step']):>16} {r['max_abs_loss_diff']:12.3e} {str(r['final_digest_equal']):>17}")
    return rows


if __name__ == "__main__":
    main()
    sys.exit(0)
