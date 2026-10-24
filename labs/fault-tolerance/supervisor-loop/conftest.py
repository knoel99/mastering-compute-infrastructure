import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / os.environ.get("IMPL", "reference")))
sys.path.insert(1, str(HERE))
