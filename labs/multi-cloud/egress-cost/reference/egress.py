"""Cost of moving a dataset between providers: egress tiers, storage during the overlap, transfer time.

Money is in USD, volumes in GB of the provider's billing unit, time in hours. Rates come from rates.yaml, where
every entry names its source and the date it was read: the code holds no price.

Egress is billed per month with cumulative tiers: the more you move in a month, the cheaper the marginal GB, and
a free allowance (`free_gb`) comes first. The cost of x GB in a month is a cumulative function F(x):
F(x) = 0 up to free_gb, then the piecewise-linear integral of the tier rates.
"""
import math

import yaml


def load_rates(path):
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _cum(x_gb, tiers, free_gb=0.0):
    """Cumulative monthly cost F(x) of x_gb gigabytes."""
    if x_gb < 0:
        raise ValueError("volume must be >= 0")
    beyond = max(0.0, x_gb - free_gb)
    cost, lower = 0.0, 0.0
    for t in tiers:
        upper = math.inf if t["upto_gb"] is None else float(t["upto_gb"])
        if beyond > lower:
            cost += (min(beyond, upper) - lower) * t["usd_per_gb"]
        lower = upper
        if beyond <= upper:
            break
    return cost


def tiered_cost(gb, tiers, free_gb=0.0, used_gb=0.0):
    """Cost of `gb` more gigabytes in a month where `used_gb` were already billed (tier position, free allowance)."""
    return _cum(used_gb + gb, tiers, free_gb) - _cum(used_gb, tiers, free_gb)


def split_cost(total_gb, months, tiers, free_gb=0.0):
    """Egress cost of `total_gb` moved in equal parts over `months` billing months (tiers restart each month)."""
    if months < 1:
        raise ValueError("months must be >= 1")
    return months * _cum(total_gb / months, tiers, free_gb)


def transfer_hours(gb, gbit_per_s, efficiency=0.8):
    """Wall-clock hours to move `gb` gigabytes over a link of `gbit_per_s` gigabit/s at the given efficiency."""
    if gbit_per_s <= 0 or not 0 < efficiency <= 1:
        raise ValueError("bandwidth must be > 0 and efficiency in (0, 1]")
    return gb * 8.0 / (gbit_per_s * efficiency) / 3600.0


def storage_cost(gb, tiers, months):
    """Storage cost of `gb` gigabytes kept for `months` months (tiers on the stored volume)."""
    return _cum(gb, tiers, 0.0) * months


def move_cost(gb, egress, dst_storage, src_storage=None, overlap_months=1.0, split_months=1,
              gbit_per_s=10.0, efficiency=0.8, used_gb=0.0):
    """Full bill of a move. egress/dst_storage/src_storage are entries of the rate card.

    The copy is paid in three places: egress at the source, storage at the destination, and storage at the source
    while both copies exist (`overlap_months`, until the copy is verified). Time is the link time only.
    """
    if split_months == 1:
        e = tiered_cost(gb, egress["tiers"], egress.get("free_gb_month", 0.0), used_gb)
    else:
        e = split_cost(gb, split_months, egress["tiers"], egress.get("free_gb_month", 0.0))
    d = storage_cost(gb, dst_storage["tiers"], overlap_months)
    s = storage_cost(gb, src_storage["tiers"], overlap_months) if src_storage else 0.0
    hours = transfer_hours(gb, gbit_per_s, efficiency)
    return {"egress": e, "dst_storage": d, "src_storage": s, "total": e + d + s, "hours": hours, "days": hours / 24.0}


def breakeven_gpu_hours(move_total, gpus, price_gap_per_gpu_hour):
    """Hours of use at the cheaper site after which the saving pays for the move (inf if there is no saving)."""
    saving_per_hour = gpus * price_gap_per_gpu_hour
    return math.inf if saving_per_hour <= 0 else move_total / saving_per_hour


def copy_vs_remote_read(gb, epochs, egress, dst_storage, months=1.0, max_epochs=10000):
    """Copy `gb` once to the destination, or re-read it from the remote bucket at every epoch (no cache)?

    Copy: one egress of gb, plus destination storage for `months`. Remote: `epochs` full reads, billed on the same
    month's cumulative tiers (so the free allowance is used once). Returns (cost_copy, cost_remote, k) where k is
    the smallest number of epochs for which the remote reads cost MORE than the copy (None if never up to max_epochs).
    """
    free = egress.get("free_gb_month", 0.0)
    copy = _cum(gb, egress["tiers"], free) + storage_cost(gb, dst_storage["tiers"], months)
    remote = _cum(epochs * gb, egress["tiers"], free)
    k = next((n for n in range(1, max_epochs + 1) if _cum(n * gb, egress["tiers"], free) > copy), None)
    return copy, remote, k
