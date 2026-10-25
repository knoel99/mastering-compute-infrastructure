"""Read the example configurations of configs/ and check what can be checked without the frameworks.

    python3 check_configs.py

Nothing here runs Megatron-LM, DeepSpeed or TorchTitan: the files are parsed (bash -n and shlex for the launch
command, json for DeepSpeed, ast for the TorchTitan recipes) and their arithmetic is verified.
"""
import ast
import json
import re
import shlex
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent / "configs"


def megatron(path, gpus):
    subprocess.run(["bash", "-n", str(path)], check=True)
    text = re.sub(r"\\\n", " ", path.read_text())
    cmd = next(line for line in text.splitlines() if "pretrain_gpt.py" in line)
    tokens = shlex.split(cmd.split("pretrain_gpt.py", 1)[1])
    flags = {}
    for i, tok in enumerate(tokens):
        if tok.startswith("--"):
            nxt = tokens[i + 1] if i + 1 < len(tokens) and not tokens[i + 1].startswith("--") else True
            flags[tok] = nxt
    tp, pp, cp = (int(flags[f]) for f in ("--tensor-model-parallel-size", "--pipeline-model-parallel-size", "--context-parallel-size"))
    mp = tp * pp * cp
    assert gpus % mp == 0, f"{gpus} GPUs not divisible by tp*pp*cp = {mp}"
    dp = gpus // mp
    mbs, gbs = int(flags["--micro-batch-size"]), int(flags["--global-batch-size"])
    assert gbs % (dp * mbs) == 0, "global batch must be a multiple of dp * micro-batch"
    m = gbs // (dp * mbs)
    assert m >= pp, "need at least one micro-batch per pipeline stage"
    return dict(tp=tp, pp=pp, cp=cp, dp=dp, microbatches=m, bubble=(pp - 1) / m, tokens=gbs * int(flags["--seq-length"]))


def deepspeed(path, gpus):
    cfg = json.loads(path.read_text())
    assert cfg["train_batch_size"] == cfg["train_micro_batch_size_per_gpu"] * cfg["gradient_accumulation_steps"] * gpus, \
        "DeepSpeed: train_batch_size = micro-batch per GPU x accumulation steps x number of GPUs"
    return dict(stage=cfg["zero_optimization"]["stage"], batch=cfg["train_batch_size"])


def torchtitan(path):
    tree = ast.parse(path.read_text())  # syntax only
    return [n.name for n in tree.body if isinstance(n, ast.FunctionDef)]


if __name__ == "__main__":
    m = megatron(HERE / "megatron_llama3_70b_64gpu.sh", gpus=64)
    print("megatron:", m)
    assert (m["tp"], m["pp"], m["cp"], m["dp"]) == (4, 4, 2, 2) and m["microbatches"] == 256
    d = deepspeed(HERE / "deepspeed_zero3.json", gpus=64)
    print("deepspeed:", d)
    t = torchtitan(HERE / "torchtitan_recipe.py")
    print("torchtitan recipes (syntax only):", t)
    print("OK check_configs")
