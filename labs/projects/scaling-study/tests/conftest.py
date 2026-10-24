import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
IMPL = ROOT / os.environ.get("IMPL", "starter")
sys.path.insert(0, str(IMPL))
PY = os.environ.get("PYTHON", sys.executable)


@pytest.fixture(scope="session")
def impl():
    return IMPL


@pytest.fixture(scope="session")
def py():
    return PY
