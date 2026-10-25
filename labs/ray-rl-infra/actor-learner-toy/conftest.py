import pytest
import ray


@pytest.fixture(scope="session")
def ray_ctx():
    ray.init(num_cpus=4, include_dashboard=False, logging_level="ERROR", log_to_driver=False)
    yield
    ray.shutdown()
