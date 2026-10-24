#!/usr/bin/env python3
"""Checkpoint interval model — TO WRITE (milestone 5).

Notation (seconds): C = cost of one checkpoint, M = mean time between failures,
R = restart cost, T = compute time between two checkpoints.
"""
import sys


def young_daly(c, mtbf):
    """Return the period T* that minimises the first-order waste."""
    raise NotImplementedError


def waste_fraction(t, c, mtbf, restart):
    """First-order waste: time spent checkpointing plus expected rework and restart, per unit of time."""
    raise NotImplementedError


def simulate(t, c, mtbf, restart, horizon, seed=0):
    """Monte Carlo goodput = useful compute / wall time with exponential failures.

    A failure loses the compute done since the last *completed* checkpoint and costs `restart`.
    A failure during a checkpoint loses that checkpoint too.
    """
    raise NotImplementedError


def main():
    raise NotImplementedError("print the Young-Daly period and a model-vs-simulation table")


if __name__ == "__main__":
    sys.exit(main())
