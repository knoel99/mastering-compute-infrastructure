import os
import sys
from pathlib import Path

import pytest

LAB = Path(__file__).resolve().parent.parent
IMPL = LAB / os.environ.get("IMPL", "starter")
sys.path.insert(0, str(LAB))      # model.py, validators (shared)
sys.path.insert(0, str(IMPL))     # admission.py (starter or reference)

from model import GPU, Workload, gpu_request, load_priorities, load_queues  # noqa: E402
from admission import Cluster  # noqa: E402

MANIFESTS = LAB / "manifests"


@pytest.fixture
def queues():
    return load_queues(MANIFESTS)


@pytest.fixture
def prio():
    return load_priorities(MANIFESTS)


@pytest.fixture
def cluster(queues):
    return Cluster(queues)


@pytest.fixture
def wl(prio):
    """wl(name, queue, gpus, priority_class='normal') -> Workload with the lab's cpu/memory ratio."""
    def make(name, queue, gpus, pc="normal"):
        return Workload(name, queue, prio[pc], gpu_request(gpus))
    return make


@pytest.fixture
def gpus():
    """gpus(cluster, queue) -> GPUs in use by the queue."""
    return lambda c, q: c.usage(q)[GPU]
