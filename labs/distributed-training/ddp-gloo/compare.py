"""Compare the final parameter vectors of two runs: python3 compare.py a.json b.json"""
import sys

import torch


def compare(path_a, path_b):
    a = torch.load(path_a.replace(".json", ".pt"), weights_only=True)
    b = torch.load(path_b.replace(".json", ".pt"), weights_only=True)
    diff = (a - b).abs()
    scale = max(float(a.abs().max()), 1e-12)
    return {"bitwise_equal": bool(torch.equal(a, b)), "max_abs_diff": float(diff.max()),
            "max_rel_diff_to_max_abs_param": float(diff.max()) / scale}


if __name__ == "__main__":
    r = compare(sys.argv[1], sys.argv[2])
    print("bitwise_equal=%s max_abs_diff=%.3e max_rel_diff=%.3e" %
          (r["bitwise_equal"], r["max_abs_diff"], r["max_rel_diff_to_max_abs_param"]))
