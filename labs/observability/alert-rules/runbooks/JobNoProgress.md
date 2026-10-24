# JobNoProgress
1. Do not trust GPU utilization here: a hung collective keeps it high. Look at `train_steps_total` and the tensor pipe.
2. Find the rank that never entered the collective (flight recorder dump, or the per-rank log of the last step).
3. Dump stacks of the stuck ranks, then requeue from the last checkpoint. The default NCCL timeout is 10 minutes.
