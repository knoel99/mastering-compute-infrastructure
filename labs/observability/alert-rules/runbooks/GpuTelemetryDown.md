# GpuTelemetryDown
1. `up == 0` means the scrape failed, not that the GPUs are fine. Check the dcgm-exporter process and the network path.
2. While it is down, GPUHot and GPU health alerts cannot fire for this node: treat the node as unmonitored.
