"""Availability and service-credit arithmetic, and what an outage costs a gang-scheduled training job."""


def monthly_availability(node_downtime_hours, nodes, days=30):
    """Availability measured per node-hour: 1 - (sum of node downtime) / (nodes * hours in the month)."""
    return 1.0 - node_downtime_hours / (nodes * days * 24.0)


def credit_percent(availability_pct, tiers, cap=None):
    """Credit (% of the monthly fee) for an availability in percent.

    tiers: list of (threshold_pct, credit_pct); the credit of the lowest threshold that availability is below applies,
    e.g. [(99.5, 5), (99.0, 10)] -> below 99.0 gives 10, below 99.5 gives 5, else 0."""
    credit = 0.0
    for threshold, pct in sorted(tiers):
        if availability_pct < threshold:
            credit = pct
            break
    return credit if cap is None else min(credit, cap)


def credit_value(monthly_fee, credit_pct):
    return monthly_fee * credit_pct / 100.0


def lost_training_value(gpus_in_job, hours_lost, price_per_gpu_hour):
    """Value of GPU-hours that cannot make progress: a gang job stops as a whole when one node is missing."""
    return gpus_in_job * hours_lost * price_per_gpu_hour
