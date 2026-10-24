# JobWaitSLOFastBurn
1. The share of jobs waiting more than the SLO threshold is burning the error budget faster than allowed.
2. Split the queue by reason class (`slurm_jobs`): capacity waits count against the platform, user and admin waits do not.
3. Look for drained nodes (`slurm_node_drain_info`) and for a large job that blocks backfill.
