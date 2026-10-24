#!/usr/bin/env python3
"""Write a tiny .safetensors file and read its header by hand, following the format specification:
8 bytes (little-endian u64) = N, then N bytes of UTF-8 JSON, then the raw tensor bytes."""
import json
import struct
import sys
import tempfile
from pathlib import Path

import torch
from safetensors.torch import save_file

with tempfile.TemporaryDirectory() as d:
    p = Path(d) / "tiny.safetensors"
    save_file({"w": torch.arange(6, dtype=torch.float32).reshape(2, 3), "b": torch.zeros(3, dtype=torch.bfloat16)}, p,
              metadata={"step": "40"})
    raw = p.read_bytes()
    (n,) = struct.unpack("<Q", raw[:8])
    header = json.loads(raw[8:8 + n])
    print(f"file size {len(raw)} bytes; header length N = {n}; data section = {len(raw) - 8 - n} bytes")
    print(json.dumps(header, sort_keys=True))
    assert header["w"]["data_offsets"] == [0, 24] or header["b"]["data_offsets"] == [0, 6]
    assert len(raw) - 8 - n == 24 + 6
sys.exit(0)
