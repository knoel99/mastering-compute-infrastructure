"""Assertions of the fsdp-memory lab: python3 check_memory.py DIR  (DIR holds ddp.json, fsdp.json, fsdp_nr.json, eq.json)"""
import json
import math
import sys
from pathlib import Path

from fsdp_memory import N_BLOCKS, build
from predict import predict_peak_unsharded, predict_rank

MiB = 2**20


def load(d, name):
    return json.loads((Path(d) / name).read_text())


def main(d):
    model = build()
    blocks = [[tuple(p.shape) for p in b.parameters()] for b in model[:N_BLOCKS]]
    root = [tuple(p.shape) for p in model[N_BLOCKS].parameters()]
    shapes = [s for b in blocks for s in b] + root
    total = sum(math.prod(s) for s in shapes)
    out = {}
    for name, mode, no_reshard in (("ddp.json", "ddp", False), ("fsdp.json", "fsdp", False), ("fsdp_nr.json", "fsdp", True)):
        recs = load(d, name)
        assert len(recs) == 4 and all(r["total_params"] == total for r in recs)
        for r in recs:  # measured = predicted, exactly (integer arithmetic on tensor sizes)
            pred = predict_rank(shapes, r["world"], r["rank"], mode)
            for k, v in pred.items():
                assert r[k] == v, (name, r["rank"], k, r[k], v)
            if mode == "fsdp":
                assert r["peak_unsharded_param_bytes"] == predict_peak_unsharded(blocks, root, no_reshard), (name, r["peak_unsharded_param_bytes"])
        out[name] = recs
    ddp, fsdp, nr = out["ddp.json"], out["fsdp.json"], out["fsdp_nr.json"]
    assert ddp[0]["persistent_bytes"] == 16 * total  # 4 + 4 + 8 bytes per parameter
    ratio = ddp[0]["persistent_bytes"] / max(r["persistent_bytes"] for r in fsdp)
    assert 3.9 <= ratio <= 4.0001, ratio
    assert sum(r["param_bytes"] for r in fsdp) == 4 * total  # the shards tile the parameters exactly
    assert ddp[0]["peak_unsharded_param_bytes"] == 4 * total  # DDP never shards
    assert nr[0]["peak_unsharded_param_bytes"] > 4 * fsdp[0]["peak_unsharded_param_bytes"]
    rss = {n: sum(r["peak_rss_delta_kib"] for r in recs) / 4 / 1024 for n, recs in out.items()}
    assert rss["ddp.json"] > 1.15 * rss["fsdp.json"], rss  # loose: RSS includes initialisation and allocator slack

    eq = load(d, "eq.json")
    for r in eq:
        assert r["max_abs_param_diff"] < 1e-5, r["max_abs_param_diff"]
        for nd, nf, nl in zip(r["norm_ddp"], r["norm_fsdp"], r["local_shard_norm_fsdp"]):
            assert abs(nd - nf) / nd < 1e-3
            assert nl < 0.8 * nf  # a local-shard norm is far below the global norm
    for i in range(len(eq[0]["norm_fsdp"])):
        agg = math.sqrt(sum(r["local_shard_norm_fsdp"][i] ** 2 for r in eq))
        assert abs(agg - eq[0]["norm_fsdp"][i]) / agg < 1e-3  # sqrt of the sum of local squares = global norm

    print(f"OK fsdp-memory: {total} parameters; per-rank persistent MiB: DDP {ddp[0]['persistent_bytes'] / MiB:.1f}, "
          f"FSDP {[round(r['persistent_bytes'] / MiB, 2) for r in fsdp]} (measured = predicted, ratio {ratio:.2f})")
    print(f"   peak unsharded params MiB: DDP {ddp[0]['peak_unsharded_param_bytes'] / MiB:.1f}, FSDP reshard "
          f"{fsdp[0]['peak_unsharded_param_bytes'] / MiB:.1f}, FSDP no reshard {nr[0]['peak_unsharded_param_bytes'] / MiB:.1f}")
    print(f"   mean peak RSS growth MiB (informative): " + ", ".join(f"{n[:-5]} {v:.0f}" for n, v in rss.items()))
    print(f"   FSDP vs DDP after 3 steps: max|dw|={max(r['max_abs_param_diff'] for r in eq):.1e}; "
          f"global grad norm step 0: DDP {eq[0]['norm_ddp'][0]:.4f}, FSDP {eq[0]['norm_fsdp'][0]:.4f}, local shard of rank 0 {eq[0]['local_shard_norm_fsdp'][0]:.4f}")


if __name__ == "__main__":
    main(sys.argv[1])
