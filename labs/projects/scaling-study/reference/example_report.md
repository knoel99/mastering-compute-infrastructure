<!-- Exemple produit par la solution de référence dans le bac à sable (VM 4 vCPU, torch 2.14.1 CPU, gloo, 3 répétitions par point). À comparer APRÈS votre propre étude : vos chiffres seront différents. -->
# Scaling study report

Machine: 4 logical CPUs, torch 2.14.1+cpu, backend gloo.
Model: MLP, 1051137 parameters, gradient message 4204548 bytes.
Design: 3 runs per point, 30 measured steps after 5 warm-up steps.

## Alpha-beta fit

alpha = 300.2 us, B = 1.049 GB/s

Ring model: `T(n) = 2(p-1) alpha + 2(p-1)/p * n/B`.

## Results

| mode | p | step (s) | IQR (s) | speedup | efficiency | Karp-Flatt | comm share | predicted (s) | model error | utilisation |
|---|---|---|---|---|---|---|---|---|---|---|
| strong | 1 | 0.0177 | 0.0007 | 1.00 | 1.00 | - | 0.00 | 0.0176 | 0.00 | - |
| strong | 2 | 0.0198 | 0.0018 | 0.90 | 0.45 | 1.234 | 0.48 | 0.0140 | 0.29 | - |
| strong | 4 | 0.0263 | 0.0029 | 0.67 | 0.17 | 1.650 | 0.69 | 0.0131 | 0.50 | - |
| weak | 1 | 0.0075 | 0.0006 | - | 1.00 | - | 0.00 | 0.0075 | 0.00 | - |
| weak | 2 | 0.0172 | 0.0008 | - | 0.43 | - | 0.55 | 0.0121 | 0.30 | - |
| weak | 4 | 0.0289 | 0.0016 | - | 0.26 | - | 0.71 | 0.0153 | 0.47 | - |

## Communication breakdown

| mode | p | pack (s) | wait (s) | all-reduce (s) | ring model (s) | all-reduce / model |
|---|---|---|---|---|---|---|
| strong | 2 | 0.0028 | 0.0021 | 0.0044 | 0.0046 | 0.96 |
| strong | 4 | 0.0046 | 0.0074 | 0.0114 | 0.0078 | 1.46 |

The extra barrier of `--decompose` perturbs the step time: use these runs to explain, not to report speedups.

## Definitions

- speedup `S = t1 / tp` (strong scaling), efficiency `E = t1 / (p tp)` (strong) or `t1 / tp` (weak).
- Karp-Flatt `e = (1/S - 1/p) / (1 - 1/p)`: if e grows with p, the loss is not a fixed serial part.
- utilisation (MFU of this study) = `6 * params * batch_per_rank / compute_time / peak`; `peak` must be measured (GEMM micro-benchmark), here: not provided, column left empty.

## Threats to validity

- The "processes" share the same 4 logical CPUs and communicate over the loopback interface:
  the measured all-reduce is a property of this machine, not of a GPU cluster.
- Few repetitions: the interquartile range is the spread of the per-run medians, with 3 runs per point.
- The communication time includes the wait for the slowest rank (load imbalance and scheduler noise).
- Warm-up steps are discarded; caches and CPU frequency are not controlled.
- The model is fitted on one message-size sweep and validated on the same machine, not on another.

