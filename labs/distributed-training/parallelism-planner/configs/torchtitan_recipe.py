"""A TorchTitan recipe is a Python function that returns a complete configuration (TorchTitan README).

The first function is the example of the README (a Llama 3 8B recipe with 2-way tensor parallelism); the second
sets the parallelism degrees with the field names shown in torchtitan/config/README.md. Linted only
(py_compile): TorchTitan is not installed here, so neither function has been run.
"""
from torchtitan_recipes.models.llama3 import llama3_8b  # noqa: F401  (needs torchtitan)


def llama3_8b_tp2():
    config = llama3_8b()
    config.parallelism.tensor_parallel_degree = 2
    return config


def llama3_8b_fsdp8_tp2():
    config = llama3_8b()
    config.parallelism.data_parallel_shard_degree = 8
    config.parallelism.tensor_parallel_degree = 2
    return config  # NGPU must equal the product of the degrees: 8 x 2 = 16
