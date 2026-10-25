import os

# Must happen before numba is imported by any test module. On a GPU machine, export
# NUMBA_ENABLE_CUDASIM=0 to run the same tests on the device.
os.environ.setdefault("NUMBA_ENABLE_CUDASIM", "1")
