# NodeSlow
1. The ratio is local compute time over the job median, so the collective wait is already excluded: the node itself is slow.
2. Compare with `gpu_node_sm_clock_min_over_median_ratio` and `DCGM_FI_DEV_GPU_TEMP` on that node.
3. Confirmed straggler: checkpoint, requeue the job without the node, drain the node with a reason starting with `health:`.
