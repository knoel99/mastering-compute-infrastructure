"""Unit tests of the memory predictor (pure Python, deterministic)."""
from predict import local_numel, predict_peak_unsharded, predict_rank, shard_rows


def test_even_split():
    assert [shard_rows(64, 4, r) for r in range(4)] == [16, 16, 16, 16]


def test_uneven_split_follows_torch_chunk():
    # torch.chunk(torch.arange(10), 4) -> sizes 3, 3, 3, 1
    assert [shard_rows(10, 4, r) for r in range(4)] == [3, 3, 3, 1]
    # 5 rows over 4 ranks -> chunk size 2: sizes 2, 2, 1, 0 (the last rank holds nothing)
    assert [shard_rows(5, 4, r) for r in range(4)] == [2, 2, 1, 0]


def test_rows_are_conserved():
    for n0 in (1, 7, 10, 64, 1000):
        for world in (1, 2, 3, 4, 8):
            assert sum(shard_rows(n0, world, r) for r in range(world)) == n0


def test_local_numel_of_matrix_and_vector():
    assert local_numel((10, 512), 4, 3) == 512
    assert local_numel((10,), 4, 0) == 3


def test_ddp_is_sixteen_bytes_per_parameter_in_fp32_adamw():
    p = predict_rank([(100, 10), (10,)], world=4, rank=2, mode="ddp")
    assert sum(p.values()) == 16 * 1010


def test_fsdp_divides_by_world_when_rows_divide():
    shapes = [(64, 32), (64,)]
    ddp = sum(predict_rank(shapes, 4, 0, "ddp").values())
    fsdp = sum(predict_rank(shapes, 4, 0, "fsdp").values())
    assert fsdp * 4 == ddp


def test_peak_unsharded_with_and_without_reshard():
    blocks = [[(10, 10)], [(20, 10)], [(5, 10)]]
    root = [(3, 3)]
    assert predict_peak_unsharded(blocks, root, no_reshard=False) == (200 + 9) * 4
    assert predict_peak_unsharded(blocks, root, no_reshard=True) == (100 + 200 + 50 + 9) * 4
