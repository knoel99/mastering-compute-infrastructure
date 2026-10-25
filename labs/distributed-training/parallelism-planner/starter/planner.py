"""STARTER of the parallelism planner: implement the functions marked TODO.

Read the docstrings of reference/planner.py ONLY after your attempt. Each function names its source:
ZeRO (Rajbhandari et al. 2020), Korthikanti et al. 2022 (activations), Narayanan et al. 2021 (pipeline, tensor),
and the alpha-beta model of the module perf-models. Run:  IMPL=starter python -m pytest -q tests
"""
import math

GB = 1e9
RECOMPUTE_COST = {"none": 0.0, "selective": 0.07, "full": 0.39}  # given: Table 4 of Korthikanti et al. (one measurement)
USABLE_FRACTION = 0.9  # given: keep 10 % of HBM as margin (assumption)


def zero_state_bytes(psi, dp, stage, bytes_param=2, bytes_grad=2, bytes_opt=12):
    """TODO bytes per rank of params + grads + optimizer state for ZeRO stage 0..3 (ValueError otherwise)."""
    raise NotImplementedError


def model_state_bytes(psi, tp, pp, dp, stage, **kw):
    """TODO split psi by tp*pp, then apply zero_state_bytes over dp."""
    raise NotImplementedError


def activation_bytes_per_layer(s, b, h, a, t=1, sequence_parallel=False, recompute="none"):
    """TODO Table 2 of Korthikanti et al.: none / selective / full recomputation, with tensor and sequence parallelism."""
    raise NotImplementedError


def activation_bytes_first_stage(layers, per_layer_bytes, p, m=None, v=1):
    """TODO first pipeline stage under 1F1B: layers/p layers times min(p, m) micro-batches in flight; interleaving v>1 scales by 1+(p-1)/(p*v)."""
    raise NotImplementedError


def pipeline_bubble_fraction(p, m, v=1):
    """TODO (p-1)/(v*m); ValueError when p, m or v is below 1."""
    raise NotImplementedError


def ring_allreduce_seconds(nbytes, p, bandwidth, alpha=0.0):
    """Given: T = 2(p-1)*alpha + 2(p-1)/p * n/B (module perf-models)."""
    if p <= 1:
        return 0.0
    return 2 * (p - 1) * alpha + 2.0 * (p - 1) / p * nbytes / bandwidth


def dp_comm_seconds(psi_local, dp, stage, bandwidth, bytes_param=2, bytes_grad=2, alpha=0.0):
    """TODO gradient reduce-scatter + parameter all-gather; one extra parameter all-gather for stage 3."""
    raise NotImplementedError


def tp_comm_seconds(layers_local, s, b, h, t, bandwidth, bytes_act=2, alpha=0.0):
    """TODO 4 all-reduces of s*b*h*bytes_act per layer and per micro-batch."""
    raise NotImplementedError


def pp_comm_seconds(m, s, b, h, tp, sequence_parallel, bandwidth, bytes_act=2):
    """TODO m micro-batches x 2 transfers (activation forward, gradient backward) of s*b*h*bytes_act, divided by tp with sequence parallelism."""
    raise NotImplementedError


def feasible_layouts(n_gpus, gpus_per_node, layers):
    """TODO (tp, pp, dp) with tp*pp*dp = n_gpus, tp dividing gpus_per_node, pp dividing layers; sorted by (tp, pp)."""
    raise NotImplementedError


def evaluate(model, cluster, layout):
    """TODO combine the functions above (see the reference for the exact input dictionaries and returned keys)."""
    raise NotImplementedError
