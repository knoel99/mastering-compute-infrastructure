"""Enumerate the layouts of a training job and rank those that fit in GPU memory.

    python3 scenario.py                       # the 70 B model of chapter 5 on 64 GPUs (8 nodes of 8)
    python3 scenario.py --psi 7e9 --layers 32 --h 4096 --heads 32 --seq 4096 --gpus 8 --batch 64
    IMPL=starter python3 scenario.py          # run your own implementation

Every bandwidth, the peak and the MFU are ASSUMPTIONS given on the command line; the output is a model.
"""
import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / os.environ.get("IMPL", "reference")))
import planner as P  # noqa: E402


def rows(a):
    model = dict(psi=a.psi, layers=a.layers, h=a.h, a=a.heads, s=a.seq)
    cluster = dict(n_gpus=a.gpus, hbm_bytes=a.hbm_gb * 1e9, peak_flops=a.peak_tflops * 1e12,
                   bw_tp=a.bw_tp_gbs * 1e9, bw_dp=a.bw_dp_gbs * 1e9, mfu=a.mfu)
    out = []
    for tp, pp, dp in P.feasible_layouts(a.gpus, a.node, a.layers):
        if a.batch % (dp * a.micro) or a.batch // (dp * a.micro) < pp:
            continue  # need at least one micro-batch per pipeline stage
        for stage in (1, 3):
            if stage == 3 and pp > 1:
                continue  # ZeRO-3 is not combined with pipeline parallelism in this model (a convention, see chapter 5)
            for recompute in ("selective", "full"):
                layout = dict(tp=tp, pp=pp, dp=dp, stage=stage, b=a.micro, global_batch=a.batch, sp=tp > 1, recompute=recompute)
                r = P.evaluate(model, cluster, layout)
                r.update(stage=stage, recompute=recompute)
                out.append(r)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--psi", type=float, default=70e9)
    ap.add_argument("--layers", type=int, default=80)
    ap.add_argument("--h", type=int, default=8192)
    ap.add_argument("--heads", type=int, default=64)
    ap.add_argument("--seq", type=int, default=4096)
    ap.add_argument("--gpus", type=int, default=64)
    ap.add_argument("--node", type=int, default=8)
    ap.add_argument("--batch", type=int, default=512, help="global batch in sequences")
    ap.add_argument("--micro", type=int, default=1)
    ap.add_argument("--hbm-gb", type=float, default=80.0)
    ap.add_argument("--peak-tflops", type=float, default=989.0, help="dense BF16 peak of the GPU (module perf-models)")
    ap.add_argument("--bw-tp-gbs", type=float, default=400.0, help="ASSUMED intra-node bus bandwidth, GB/s")
    ap.add_argument("--bw-dp-gbs", type=float, default=25.0, help="ASSUMED per-GPU inter-node bandwidth, GB/s")
    ap.add_argument("--mfu", type=float, default=0.40, help="ASSUMED MFU used to size the compute time")
    ap.add_argument("--top", type=int, default=8)
    ap.add_argument("--sort", choices=["no_overlap", "dp_hidden"], default="no_overlap")
    a = ap.parse_args()
    allr = rows(a)
    fit = sorted((r for r in allr if r["fits"]), key=lambda r: r["overhead_" + a.sort])
    print(f"{len(allr)} layouts evaluated, {len(fit)} fit in {P.USABLE_FRACTION:.0%} of {a.hbm_gb:.0f} GB; "
          f"compute time per step at MFU {a.mfu:.0%}: {allr[0]['t_compute_s']:.1f} s")
    print("tp pp dp zero recompute  m  state_GB  acts_GB  total_GB  bubble  t_tp_s  t_pp_s  t_dp_s  overhead: no-overlap / dp-hidden")
    for r in fit[: a.top]:
        tp, pp, dp = r["layout"]
        print(f"{tp:>2} {pp:>2} {dp:>2} {r['stage']:>4} {r['recompute']:<9} {r['microbatches']:>3} {r['state_gb']:>8.1f} {r['activations_gb']:>8.1f} "
              f"{r['total_gb']:>8.1f} {r['bubble']:>7.1%} {r['t_tp_s']:>7.2f} {r['t_pp_s']:>7.2f} {r['t_dp_s']:>7.2f} {r['overhead_no_overlap']:>9.1%} {r['overhead_dp_hidden']:>9.1%}")
    if not fit:
        print("no layout fits: add GPUs, shorten the sequence or shrink the micro-batch")


if __name__ == "__main__":
    main()
