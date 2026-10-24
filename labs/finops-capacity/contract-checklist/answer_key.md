# Answer key — review of `fictional_contract.md` (FICTIONAL contract)

The four deal-breakers, in the order a training-fleet owner should read them.

| Clause | Finding | Why it bites a training fleet | What to ask | Possible concession |
|---|---|---|---|---|
| 3.2 | A node is "available" if its management interface answers | A node with a dead GPU or a degraded interconnect is up for the provider and useless for a gang-scheduled job. The SLA never triggers. | Availability defined by health checks on GPUs, interconnect and storage mount, in an annex. | Accept a 99.5% target if the definition is strict. |
| 1.2 | Take-or-pay on all 512 GPUs from day one | You pay for GPUs you cannot use (delivery in tranches, failed nodes, low demand). | Bill delivered and accepted capacity; 10% flex band; resale or reassignment. | A longer term for a lower unit price. |
| 2.2 | No remedy for late delivery, invoicing from the Start Date | The provider carries no schedule risk; you carry all of it. | Invoice accepted capacity only; credit per week of delay. | Accept "as available" tranches if invoicing follows acceptance. |
| 9.4 | Provider may terminate for convenience on 30 days notice without refund | A training programme cannot be rebuilt in 30 days; prepaid fees are lost. | Delete it, or 12 months notice with refund and transition help. | Reciprocal exit for the customer after month 12 against a fee. |

Other findings worth a sentence in a review meeting:

- 3.4/3.5: credits capped at 10% and the sole remedy. Even a month of poor service returns at most one tenth of the fee. Ask for higher tiers and keep termination for cause.
- 4.1/4.2: no replacement time and the right to substitute "similar" hardware. Ask for a number of hours and the same GPU model.
- 4.3: deemed acceptance on delivery. Ask for acceptance tests (burn-in, interconnect bandwidth, storage throughput) before invoicing starts.
- 5.1: no performance commitment. The measured acceptance values become a contractual floor.
- 9.2: force majeure covering component shortages and power. This removes the provider's core risk from the provider.
- 8.1: transfer out at standard rates including at exit. Ask for a waiver or a cap at exit.

Scores are a sorting aid, not a measurement: weights and thresholds in `rubric.yaml` are the course's choices.
