"""Logical resources, heterogeneous pools and `ray status` (chapters 1, 2 and 7 of the course).

Ray resources are LOGICAL: this script declares 2 'GPUs' and 2 'eval_gpu' on a machine that has
none. That is a SIMULATION of a heterogeneous fleet (it exercises Ray's scheduler, not a GPU).
Run standalone: it calls ray.init itself and asserts on the scheduler's answers.
"""
import os
import subprocess
import sys
import time

import ray


def available(key):
    return ray.available_resources().get(key, 0.0)


def wait_for(cond, timeout_s=20.0):
    t0 = time.time()
    while not cond():
        if time.time() - t0 > timeout_s:
            raise TimeoutError("condition not reached")
        time.sleep(0.1)


@ray.remote
class Probe:
    def ping(self):
        return os.getpid()


def main():
    ray.init(num_cpus=8, num_gpus=2, resources={"eval_gpu": 2}, include_dashboard=False,
             logging_level="ERROR", log_to_driver=False)
    total = ray.cluster_resources()
    print(f"declared: CPU={total['CPU']:.0f} GPU={total['GPU']:.0f} eval_gpu={total['eval_gpu']:.0f}")

    # 1. what an actor holds while it RUNS (Ray 2.59.0): 0 CPU by default, 1 CPU as soon as another
    #    resource is requested without an explicit num_cpus. The docs advise setting num_cpus explicitly.
    def held_cpu(**opts):
        actors = [Probe.options(**opts).remote() for _ in range(2)]
        ray.get([x.ping.remote() for x in actors])
        time.sleep(1.0)
        free = available("CPU")
        for x in actors:
            ray.kill(x)
        wait_for(lambda: available("CPU") == 8.0 and available("GPU") == 2.0)
        return free

    free_default = held_cpu()
    free_gpu_only = held_cpu(num_gpus=1)
    free_zero = held_cpu(num_gpus=1, num_cpus=0)
    print(f"2 actors, default options         -> free CPU = {free_default:.0f} of 8")
    print(f"2 actors, num_gpus=1 only         -> free CPU = {free_gpu_only:.0f} of 8")
    print(f"2 actors, num_gpus=1, num_cpus=0  -> free CPU = {free_zero:.0f} of 8")
    assert (free_default, free_gpu_only, free_zero) == (8.0, 6.0, 8.0)

    # 2. heterogeneous pools by logical resource: learner on 'GPU', scorers on 'eval_gpu', simulators on CPU
    learner = Probe.options(num_gpus=1, num_cpus=0).remote()
    scorers = [Probe.options(num_cpus=0, resources={"eval_gpu": 1}).remote() for _ in range(2)]
    sims = [Probe.options(num_cpus=1).remote() for _ in range(4)]
    ray.get([x.ping.remote() for x in [learner, *scorers, *sims]])
    print(f"pools placed: 1 learner, {len(scorers)} scorers, {len(sims)} simulators")

    # 3. an impossible ask stays pending: the second learner wants 2 GPUs, only 1 is free
    greedy = Probe.options(num_gpus=2).remote()
    ref = greedy.ping.remote()
    ready, _ = ray.wait([ref], timeout=2.0)
    assert not ready, "a request for 2 GPUs must stay pending while one GPU is held"
    ray_bin = os.path.join(os.path.dirname(sys.executable), "ray")
    t0, out = time.time(), ""
    while time.time() - t0 < 60:     # demands are reported to `ray status` with a delay: poll, do not sleep blindly
        out = subprocess.run([ray_bin, "status"], capture_output=True, text=True, timeout=60).stdout
        if "'GPU': 2.0" in out:
            break
        time.sleep(1.0)
    print("---- ray status ----")
    print(out.strip())
    print("--------------------")
    assert "'GPU': 2.0" in out, "the pending 2-GPU request must be listed under Pending Demands"
    ray.kill(greedy)
    ray.kill(learner)
    for x in [*scorers, *sims]:
        ray.kill(x)
    wait_for(lambda: available("CPU") == 8.0 and available("GPU") == 2.0)

    # 4. placement groups are atomic: PACK fits on one node; STRICT_SPREAD over 2 nodes cannot,
    #    and a pending group reserves NOTHING
    from ray.util.placement_group import placement_group, remove_placement_group
    pg_pack = placement_group([{"CPU": 1}, {"CPU": 1}], strategy="PACK")
    ray.get(pg_pack.ready(), timeout=20)
    pg_spread = placement_group([{"CPU": 1}, {"CPU": 1}], strategy="STRICT_SPREAD")
    ready, _ = ray.wait([pg_spread.ready()], timeout=3.0)
    time.sleep(1.0)
    free = available("CPU")
    print(f"PACK group ready: True ; STRICT_SPREAD group ready on one node: {bool(ready)} ; free CPU = {free:.0f} of 8")
    assert not ready and free == 6.0, "only the PACK group may hold resources (2 CPU)"
    remove_placement_group(pg_spread)
    remove_placement_group(pg_pack)
    ray.shutdown()
    print("OK resources-demo")


if __name__ == "__main__":
    main()
