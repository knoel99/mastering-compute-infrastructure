"""Ray Train on CPU: 2 workers, gloo, one failure tolerated (chapter 3).

SIMULATION of a GPU job: use_gpu=False and the 'model' is a linear layer. What is real: Ray Train's
worker group (Ray actors in a placement group), torch.distributed initialisation, checkpoint
report/restore, and the failure policy. A worker is killed once, on purpose, in the first run.
"""
import os
import tempfile

import ray
import ray.train
import torch
from ray.train import Checkpoint, FailureConfig, RunConfig, ScalingConfig
from ray.train.torch import TorchTrainer, prepare_model


def train_loop(config):
    ctx = ray.train.get_context()
    model = prepare_model(torch.nn.Linear(4, 1))
    opt = torch.optim.SGD(model.parameters(), lr=0.1)
    start = 0
    ckpt = ray.train.get_checkpoint()
    if ckpt:
        with ckpt.as_directory() as d:
            state = torch.load(os.path.join(d, "state.pt"))
        model.module.load_state_dict(state["model"])
        start = state["epoch"] + 1
    g = torch.Generator().manual_seed(ctx.get_world_rank())
    for epoch in range(start, config["epochs"]):
        x = torch.randn(32, 4, generator=g)
        loss = ((model(x) - x.sum(dim=1, keepdim=True)) ** 2).mean()
        opt.zero_grad()
        loss.backward()                      # DDP all-reduces the gradients here
        opt.step()
        if epoch == config["die_at"] and ctx.get_world_rank() == 1 and not os.path.exists(config["marker"]):
            open(config["marker"], "w").close()
            os._exit(1)                      # kill one worker process, once
        with tempfile.TemporaryDirectory() as d:
            torch.save({"model": model.module.state_dict(), "epoch": epoch}, os.path.join(d, "state.pt"))
            ray.train.report({"loss": loss.item(), "epoch": epoch, "start": start},
                             checkpoint=Checkpoint.from_directory(d) if ctx.get_world_rank() == 0 else None)


def main():
    ray.init(num_cpus=4, include_dashboard=False, logging_level="ERROR", log_to_driver=False)
    with tempfile.TemporaryDirectory() as store, tempfile.TemporaryDirectory() as mk:
        trainer = TorchTrainer(
            train_loop,
            train_loop_config={"epochs": 6, "die_at": 3, "marker": os.path.join(mk, "died")},
            scaling_config=ScalingConfig(num_workers=2, use_gpu=False),
            run_config=RunConfig(storage_path=store, failure_config=FailureConfig(max_failures=2)),
        )
        result = trainer.fit()
        print("final metrics:", {k: result.metrics[k] for k in ("epoch", "start")}, "error:", result.error)
        assert result.error is None and result.metrics["epoch"] == 5
        assert result.metrics["start"] >= 1, "the run must have resumed from a checkpoint after the kill"
    ray.shutdown()
    print("OK train-demo")


if __name__ == "__main__":
    main()
