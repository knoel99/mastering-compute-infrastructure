"""Starter for the egress-cost lab: write the seven functions below (same names and signatures as reference/).

Read ../README.md first. Tests: IMPL=starter python -m pytest -q tests  (they all fail until you write the code).
Money in USD, volumes in GB (the provider's billing unit), time in hours. A rate card entry has
`tiers` = [{"upto_gb": cumulative breakpoint on the volume beyond the free allowance, or None, "usd_per_gb": rate}].
"""
import math  # noqa: F401  (you will need math.inf)

import yaml


def load_rates(path):
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def tiered_cost(gb, tiers, free_gb=0.0, used_gb=0.0):
    """Cost of `gb` more gigabytes in a month where `used_gb` were already billed.

    Hint: write the cumulative cost F(x) first (zero up to free_gb, then the integral of the tier rates), and return
    F(used_gb + gb) - F(used_gb).
    """
    raise NotImplementedError("TODO")


def split_cost(total_gb, months, tiers, free_gb=0.0):
    """Egress cost of total_gb moved in equal parts over `months` months (the tiers and the free allowance restart)."""
    raise NotImplementedError("TODO")


def transfer_hours(gb, gbit_per_s, efficiency=0.8):
    """Hours to move gb gigabytes over a gbit_per_s link at the given efficiency. Reject non-positive bandwidth."""
    raise NotImplementedError("TODO")


def storage_cost(gb, tiers, months):
    """Storage cost of gb gigabytes kept for `months` months; tiers apply to the stored volume (no free allowance)."""
    raise NotImplementedError("TODO")


def move_cost(gb, egress, dst_storage, src_storage=None, overlap_months=1.0, split_months=1,
              gbit_per_s=10.0, efficiency=0.8, used_gb=0.0):
    """Dict with egress, dst_storage, src_storage, total, hours, days. See reference/ for the exact meaning."""
    raise NotImplementedError("TODO")


def breakeven_gpu_hours(move_total, gpus, price_gap_per_gpu_hour):
    """Hours at the cheaper site after which the saving pays for the move; math.inf when there is no saving."""
    raise NotImplementedError("TODO")


def copy_vs_remote_read(gb, epochs, egress, dst_storage, months=1.0, max_epochs=10000):
    """(cost of copying once, cost of `epochs` remote reads in the same month, smallest epochs where remote > copy).

    Copy = one egress of gb + destination storage for `months`; remote = cumulative egress of epochs * gb (the free
    allowance is used once). Return None for the third item if no epoch count up to max_epochs makes remote dearer.
    """
    raise NotImplementedError("TODO")
