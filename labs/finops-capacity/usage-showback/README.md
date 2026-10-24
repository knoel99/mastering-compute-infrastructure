# Lab 15.1 — From the scheduler export to a showback report (module 15, `finops-capacity`)

Turns the job accounting of a cluster (`sacct -X -P`) into what a FinOps review needs: GPU-hours per team, utilization of
the fleet, hours lost in abnormal job endings, queue waits, and the **full cost of the fleet allocated to the teams**
(direct cost + a share of the idle capacity), so that nothing disappears between the invoice and the teams.

Two kinds of data, both labelled:

* `fixtures/synthetic_sacct.txt` is **SYNTHETIC** (made up by `gen_trace.py`: 4 teams, 64 GPUs, 28 days, strict-FIFO
  scheduling, seeded). It carries `gres/gpu` in `AllocTRES` as a GPU cluster would. The cost rate (2.08 u per GPU-hour) is
  FICTIONAL: it is the yearly cost per GPU of the owned option of lab 15.3 divided by 8760 h.
* `fixtures/real_sandbox_sacct.txt` is a **real capture** from the Slurm 23.11 sandbox of the Slurm module (4 CPUs, no
  GPU: CPUs stand in for GPUs), taken by `verify-live.sh` on the date given in its first line.

```
gen_trace.py          synthetic trace generator (seeded)
starter/showback.py   nine functions to write (TRES parsing, hours, utilization, percentiles, idle allocation, cost report)
reference/showback.py reference solution and command-line report (read it after your own attempt)
tests/                19 tests; IMPL=starter|reference selects the code under test
verify.sh             offline: reference green, starter red, report on the synthetic trace
verify-live.sh        needs root and Slurm: runs jobs, exports sacct, checks our hours against Slurm's CPUTimeRAW
```

```bash
export PYTHON=/path/to/python                          # needs pytest only
IMPL=starter $PYTHON -m pytest -q tests                # your work: failures at the start
PYTHON=$PYTHON bash verify.sh                          # offline proof
sudo PYTHON=$PYTHON bash verify-live.sh                # live proof on a real Slurm (about 1 minute)
$PYTHON reference/showback.py fixtures/synthetic_sacct.txt --capacity 64 --rate 2.08
```

Limits, stated on purpose: "lost candidates" is an upper bound (a job with checkpoints loses only the work since the
last one); utilization measures allocation, not useful work (that needs GPU metrics, module 14); a job holding GPUs while
idle looks perfectly utilized here; no multi-cluster, no preemption accounting beyond the final state.
