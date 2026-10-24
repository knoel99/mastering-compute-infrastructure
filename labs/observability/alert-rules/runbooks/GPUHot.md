# GPUHot
1. Is it one GPU or the whole node? Compare `DCGM_FI_DEV_GPU_TEMP` across the node and its rack neighbours.
2. One GPU: check `DCGM_FI_DEV_SM_CLOCK` (throttling) and the job's step time; drain the node after the job if the clock is low.
3. Whole rack: facility problem (cooling); tell the datacentre team before draining anything.
