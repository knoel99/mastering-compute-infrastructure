import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / os.environ.get("IMPL", "starter")))
sys.path.insert(0, str(ROOT))  # mesh.py is shared by both implementations
