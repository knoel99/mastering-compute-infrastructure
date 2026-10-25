"""Assertions of the ddp-gloo lab on the JSON files written by train.py: python3 check_ddp.py DIR"""
import json
import sys
from pathlib import Path

import torch

from buckets import param_bytes_ready_order, predict_buckets
from common import build_model
from compare import compare


def load(d, name):
    return json.loads((Path(d) / f"{name}.json").read_text())


def main(d):
    single, a, b, c, u = (load(d, n) for n in ("single", "ddp", "ddp_repeat", "ddp_cap1", "ddp_uneven"))
    sizes = param_bytes_ready_order(build_model())

    # 1. DDP(4) is the same optimisation as one process on the whole global batch, up to rounding
    eq = compare(f"{d}/single.json", f"{d}/ddp.json")
    assert eq["max_abs_diff"] < 1e-5, f"DDP and single process diverge: {eq}"
    assert a["max_abs_diff_to_rank0"] == 0.0, "replicas must hold identical parameters"
    # 2. the same DDP run twice gives the same bits (gloo ring order is fixed)
    rep = compare(f"{d}/ddp.json", f"{d}/ddp_repeat.json")
    assert rep["bitwise_equal"], f"two identical DDP runs differ: {rep}"
    # 3. the communication hook saw one all-reduce per bucket, except the first iteration (a single bucket)
    nb = len(a["ddp_rebuilt_bucket_sizes"])
    assert a["hook_calls"] == 1 + (a["steps"] - 1) * nb, (a["hook_calls"], nb)
    assert a["hook_bytes"] == a["steps"] * a["ddp_total_param_bytes"]
    # 4. our bucket predictor reproduces DDP's own log, for the default cap and for an explicit cap
    assert predict_buckets(sizes, None) == a["ddp_rebuilt_bucket_sizes"], (predict_buckets(sizes, None), a["ddp_rebuilt_bucket_sizes"])
    assert predict_buckets(sizes, 1) == c["ddp_rebuilt_bucket_sizes"], (predict_buckets(sizes, 1), c["ddp_rebuilt_bucket_sizes"])
    # 5. a ragged split of the global batch changes the result far beyond rounding
    bad = compare(f"{d}/single.json", f"{d}/ddp_uneven.json")
    assert bad["max_abs_diff"] > 1e-4, f"uneven split should visibly change the result: {bad}"

    exposed = a["step_s_sync_median"] - a["step_s_no_sync_median"]
    print(f"OK ddp-gloo: DDP(4) vs single process max|dw|={eq['max_abs_diff']:.1e} (rel {eq['max_rel_diff_to_max_abs_param']:.1e}); "
          f"repeat run bitwise equal; buckets {a['ddp_rebuilt_bucket_sizes']} predicted = measured")
    print(f"   ragged batch split: max|dw|={bad['max_abs_diff']:.1e}; hook calls={a['hook_calls']} for {a['steps']} steps")
    print(f"   timing (informative, not asserted): step {1e3 * a['step_s_sync_median']:.1f} ms with sync, "
          f"{1e3 * a['step_s_no_sync_median']:.1f} ms without, exposed communication {1e3 * exposed:.1f} ms, "
          f"isolated all-reduce of the same buckets {1e3 * a['isolated_allreduce_s_per_step']:.1f} ms")


if __name__ == "__main__":
    torch.set_num_threads(1)
    main(sys.argv[1])
