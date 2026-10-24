import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
IMPL = os.environ.get("IMPL", "reference")
sys.path.insert(0, str(HERE / IMPL))
ASSUMPTIONS = HERE / "assumptions.yaml"
