import os

# Must be set before triton is imported. Unset it (or set 0) on a GPU machine to compile for the device.
os.environ.setdefault("TRITON_INTERPRET", "1")
