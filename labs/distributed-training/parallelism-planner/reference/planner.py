"""Memory and communication calculator to choose a parallelism layout (tp, pp, dp, ZeRO stage).

This is a MODEL, not a measurement: every formula is taken from a source named in its docstring,
and every bandwidth, peak or MFU is an input that the caller must supply and justify.
Units: bytes, seconds, FLOP. "GB" below means 1e9 bytes, as in the ZeRO paper and in GPU data sheets.
"""
import math

GB = 1e9
# Extra compute time of activation recomputation, as a fraction of a step. Source: Table 4 of Korthikanti et al. 2022
# (one transformer layer of a 22 B model on A100: +39 % with full recomputation, +7 % with selective recomputation).
# These are ONE measurement on one model and one GPU: replace them with your own.
RECOMPUTE_COST = {"none": 0.0, "selective": 0.07, "full": 0.39}
USABLE_FRACTION = 0.9  # share of HBM the model may use; the rest is a margin for the CUDA context, fragmentation, buffers (assumption)


# ---------------------------------------------------------------- model state (ZeRO, Rajbhandari et al. 2020)
def zero_state_bytes(psi, dp, stage, bytes_param=2, bytes_grad=2, bytes_opt=12):
    """Bytes of parameters + gradients + optimizer state held by ONE data-parallel rank.

    Mixed-precision Adam: 2 (bf16 weights) + 2 (bf16 gradients) + 12 (fp32 copy, momentum, variance) = 16 bytes/param.
    Stage 0: nothing sharded. Stage 1: optimizer state / dp. Stage 2: + gradients / dp. Stage 3: + parameters / dp.
    """
    if stage not in (0, 1, 2, 3):
        raise ValueError("ZeRO stage must be 0, 1, 2 or 3")
    if dp < 1:
        raise ValueError("dp must be >= 1")
    if stage == 0:
        return (bytes_param + bytes_grad + bytes_opt) * psi
    if stage == 1:
        return (bytes_param + bytes_grad) * psi + bytes_opt * psi / dp
    if stage == 2:
        return bytes_param * psi + (bytes_grad + bytes_opt) * psi / dp
    return (bytes_param + bytes_grad + bytes_opt) * psi / dp


def model_state_bytes(psi, tp, pp, dp, stage, **kw):
    """Model state per GPU: parameters are first split evenly by tensor and pipeline parallelism (an
    approximation: embeddings and the head are not exactly 1/(tp*pp)), then sharded by ZeRO across dp."""
    return zero_state_bytes(psi / (tp * pp), dp, stage, **kw)


# ---------------------------------------------------------------- activations (Korthikanti et al. 2022, Table 2 and Eq. 5)
def activation_bytes_per_layer(s, b, h, a, t=1, sequence_parallel=False, recompute="none"):
    """Bytes of activations stored per transformer layer, 16-bit activations.

    s sequence length, b micro-batch size, h hidden size, a attention heads, t tensor-parallel size.
    recompute: "none", "selective" (drops the 5*a*s/h attention term) or "full" (keeps only the layer input: 2*s*b*h).
    """
    if recompute not in ("none", "selective", "full"):
        raise ValueError("recompute must be none, selective or full")
    if recompute == "full":
        return 2.0 * s * b * h
    linear_part = 34.0 / t if sequence_parallel else 10.0 + 24.0 / t
    attention_part = 0.0 if recompute == "selective" else 5.0 * a * s / (h * t)
    return s * b * h * (linear_part + attention_part)


def activation_bytes_first_stage(layers, per_layer_bytes, p, m=None, v=1):
    """Activation bytes on the most loaded pipeline stage (the first one) under 1F1B.

    The first stage has layers/p layers and keeps p micro-batches in flight, hence layers worth of activations
    whatever p is (Eq. 5). With fewer micro-batches than stages (m < p) only m are in flight. The interleaved schedule
    with v chunks per device multiplies the total by 1 + (p-1)/(p*v).
    """
    in_flight = p if m is None else min(p, m)
    stored = layers / p * in_flight
    if v > 1:
        stored *= 1.0 + (p - 1.0) / (p * v)
    return stored * per_layer_bytes


# ---------------------------------------------------------------- pipeline (Narayanan et al. 2021)
def pipeline_bubble_fraction(p, m, v=1):
    """Idle time of a pipeline flush divided by the ideal compute time: (p-1)/(v*m)."""
    if m < 1 or v < 1 or p < 1:
        raise ValueError("p, m, v must be >= 1")
    return (p - 1.0) / (v * m)


# ---------------------------------------------------------------- communication (alpha-beta model, see module perf-models)
def ring_allreduce_seconds(nbytes, p, bandwidth, alpha=0.0):
    """T = 2(p-1)*alpha + 2(p-1)/p * n/B  for a ring all-reduce of n bytes over p ranks."""
    if p <= 1:
        return 0.0
    return 2 * (p - 1) * alpha + 2.0 * (p - 1) / p * nbytes / bandwidth


def dp_comm_seconds(psi_local, dp, stage, bandwidth, bytes_param=2, bytes_grad=2, alpha=0.0):
    """Data-parallel communication per optimizer step for psi_local parameters on this rank.

    Stages 0-2: gradient reduce-scatter + parameter all-gather = one all-reduce volume (2*psi elements).
    Stage 3 adds a second parameter all-gather (forward and backward): 3*psi elements, 1.5x (ZeRO paper, section 7).
    """
    if dp <= 1:
        return 0.0
    gathers = 1 if stage < 3 else 2
    nbytes = (bytes_grad + gathers * bytes_param) * psi_local
    return (dp - 1) / dp * nbytes / bandwidth + 2 * (dp - 1) * alpha


def tp_comm_seconds(layers_local, s, b, h, t, bandwidth, bytes_act=2, alpha=0.0):
    """Tensor-parallel communication for ONE micro-batch on one stage: 4 all-reduces of s*b*h activations per layer
    (2 in the forward pass, 2 in the backward pass; Narayanan et al. 2021, section 3.2)."""
    return layers_local * 4 * ring_allreduce_seconds(s * b * h * bytes_act, t, bandwidth, alpha)


def pp_comm_seconds(m, s, b, h, tp, sequence_parallel, bandwidth, bytes_act=2):
    """Pipeline point-to-point traffic for one step on one stage boundary: m micro-batches, each sending its activation
    forward and its gradient backward (2 transfers of s*b*h*bytes_act). With sequence parallelism each tensor-parallel
    rank holds 1/tp of the activation, so each sends 1/tp of it (an assumption, close to Megatron's scatter/gather)."""
    share = tp if sequence_parallel else 1
    return m * 2 * (s * b * h * bytes_act / share) / bandwidth


# ---------------------------------------------------------------- layouts
def feasible_layouts(n_gpus, gpus_per_node, layers):
    """All (tp, pp, dp) with tp*pp*dp = n_gpus, tp dividing the node size (tensor parallelism stays inside a node)
    and pp dividing the number of layers. Sorted by (tp, pp)."""
    out = []
    for tp in range(1, gpus_per_node + 1):
        if gpus_per_node % tp:
            continue
        for pp in range(1, layers + 1):
            if layers % pp or n_gpus % (tp * pp):
                continue
            out.append((tp, pp, n_gpus // (tp * pp)))
    return sorted(out, key=lambda x: (x[0], x[1]))


def evaluate(model, cluster, layout):
    """Evaluate one layout. Inputs:

    model   = dict(psi, layers, h, a, s)                      parameters, layers, hidden, heads, sequence length
    cluster = dict(n_gpus, hbm_bytes, peak_flops, bw_tp, bw_dp, mfu)   mfu is an ASSUMPTION used to size compute time
              optional: bw_pp (default bw_dp), usable_fraction (default 0.9), recompute_cost (default RECOMPUTE_COST)
    layout  = dict(tp, pp, dp, stage, b, global_batch, sp, recompute, v)  global_batch in sequences
    Returns a dict with memory per GPU, bubble, communication times and two overheads (fractions of the compute time):
    overhead_no_overlap (nothing overlaps: an upper bound) and overhead_dp_hidden (data-parallel traffic fully hidden).
    What it does NOT model: kernel efficiency lost on small matrices, stage imbalance, latency terms, memory
    fragmentation, overlap. Treat the result as a filter and a lower bound on overhead, never as a ranking to obey.
    """
    tp, pp, dp = layout["tp"], layout["pp"], layout["dp"]
    if tp * pp * dp != cluster["n_gpus"]:
        raise ValueError("tp*pp*dp must equal the number of GPUs")
    if model["layers"] % pp:
        raise ValueError("pp must divide the number of layers")
    per_pipeline = layout["global_batch"] / dp
    if per_pipeline % layout["b"] or per_pipeline < layout["b"]:
        raise ValueError("global_batch must be a multiple of dp * micro-batch size")
    m = int(per_pipeline // layout["b"])
    s, h, a, layers = model["s"], model["h"], model["a"], model["layers"]
    state = model_state_bytes(model["psi"], tp, pp, dp, layout["stage"])
    per_layer = activation_bytes_per_layer(s, layout["b"], h, a, tp, layout.get("sp", tp > 1), layout.get("recompute", "none"))
    acts = activation_bytes_first_stage(layers, per_layer, pp, m, layout.get("v", 1))
    tokens = layout["global_batch"] * s
    t_compute = 6.0 * model["psi"] * tokens / (cluster["n_gpus"] * cluster["peak_flops"] * cluster["mfu"])
    t_tp = m * tp_comm_seconds(layers // pp, s, layout["b"], h, tp, cluster["bw_tp"])
    t_dp = dp_comm_seconds(model["psi"] / (tp * pp), dp, layout["stage"], cluster["bw_dp"])
    sp = layout.get("sp", tp > 1)
    t_pp = pp_comm_seconds(m, s, layout["b"], h, tp, sp, cluster.get("bw_pp", cluster["bw_dp"])) if pp > 1 else 0.0
    bubble = pipeline_bubble_fraction(pp, m, layout.get("v", 1))
    recompute_cost = cluster.get("recompute_cost", RECOMPUTE_COST)[layout.get("recompute", "none")]
    return {
        "layout": (tp, pp, dp), "microbatches": m, "state_gb": state / GB, "activations_gb": acts / GB,
        "total_gb": (state + acts) / GB,
        "fits": state + acts <= cluster.get("usable_fraction", USABLE_FRACTION) * cluster["hbm_bytes"],
        "bubble": bubble, "t_compute_s": t_compute, "t_tp_s": t_tp, "t_pp_s": t_pp, "t_dp_s": t_dp,
        "recompute_cost": recompute_cost,
        "overhead_no_overlap": bubble + (t_tp + t_pp + t_dp) / t_compute + recompute_cost,
        # best case: the data-parallel traffic is entirely hidden behind compute (it often is, see chapter 6)
        "overhead_dp_hidden": bubble + (t_tp + t_pp) / t_compute + recompute_cost,
    }
