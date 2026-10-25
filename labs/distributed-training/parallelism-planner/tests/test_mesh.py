"""Tests of the rank arithmetic (the module is given, not part of the exercise)."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from mesh import Mesh  # noqa: E402

LLAMA3_FIG5 = Mesh(("dp", "pp", "cp", "tp"), (2, 2, 2, 2))  # 16 GPUs, Figure 5 of the Llama 3 paper


def test_figure_5_of_llama3():
    # "GPU0 and GPU1 same TP group, GPU0 and GPU2 same CP group, GPU0 and GPU4 same PP group, GPU0 and GPU8 same DP group"
    assert LLAMA3_FIG5.group(0, "tp") == [0, 1]
    assert LLAMA3_FIG5.group(0, "cp") == [0, 2]
    assert LLAMA3_FIG5.group(0, "pp") == [0, 4]
    assert LLAMA3_FIG5.group(0, "dp") == [0, 8]


def test_coords_roundtrip():
    m = Mesh(("dp", "pp", "tp"), (4, 2, 8))
    for r in range(m.world):
        c = dict(zip(m.names, m.coords(r)))
        assert m.rank(**c) == r


def test_groups_partition_the_world():
    m = Mesh(("dp", "pp", "tp"), (4, 2, 8))
    for name in m.names:
        seen = {tuple(m.group(r, name)) for r in range(m.world)}
        assert sorted(x for g in seen for x in g) == list(range(m.world))


def test_tensor_parallel_stays_in_a_node_when_innermost():
    m = Mesh(("dp", "pp", "tp"), (8, 2, 4))
    assert m.node_span("tp", 8) == 1
    assert m.node_span("dp", 8) == 8  # data parallelism crosses nodes
    outer_tp = Mesh(("tp", "pp", "dp"), (4, 2, 8))
    assert outer_tp.node_span("tp", 8) > 1  # the same sizes in the wrong order put TP across nodes


def test_bad_arguments():
    with pytest.raises(ValueError):
        Mesh(("a", "a"), (2, 2))
    with pytest.raises(ValueError):
        LLAMA3_FIG5.coords(16)
