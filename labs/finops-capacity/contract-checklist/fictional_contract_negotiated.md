# GPU CAPACITY AGREEMENT, AFTER ONE ROUND OF NEGOTIATION — **FICTIONAL EXAMPLE, WRITTEN FOR A COURSE. NOT A REAL CONTRACT, NOT A REAL PROVIDER.**

Between "Fictional Compute Provider" (the "Provider") and "the Customer".
Every number below is invented to exercise a review grid. Clause headings are stable identifiers used by the lab.

## 1. Term and commitment
1.1 Minimum Term: 24 months from the Start Date.
1.2 Committed Capacity: 512 GPUs, billed on the capacity delivered and accepted. The Customer may reduce the billed capacity by up to 10% with 30 days notice.
1.3 Renewal: the agreement renews automatically for 12 months unless the Customer gives notice of non-renewal at least 30 days before the end of the term; the Provider reminds the Customer 90 days before.
1.4 The Customer may terminate for convenience after month 12 against a fee of 3 months of fees.

## 2. Delivery
2.1 The estimated delivery date of the Committed Capacity is 1 March. Delivery may be made in tranches; the first tranche is 25% of the Committed Capacity and the remainder is delivered as available.
2.2 Each week of delay of a tranche gives a credit of 2% of the monthly fee of that tranche. The Customer is invoiced only for accepted capacity.

## 3. Availability
3.1 Availability Target: 99.5% per calendar month, measured per cluster.
3.2 A node is available only if its GPUs, interconnect and storage mount pass the health checks of Annex B.
3.3 Scheduled maintenance of up to 24 hours per month, announced 48 hours in advance, is excluded. Emergency maintenance is excluded and needs no notice.
3.4 Service Credits: 5% of the monthly fee if availability is below 99.5% and at least 99.0%; 10% of the monthly fee if below 99.0%. The credit is capped at 30% of the monthly fee.
3.5 Service Credits are the Customer's sole and exclusive remedy for unavailability. The Customer must claim within 30 days of the end of the month.

## 4. Replacement
4.1 The Provider will replace a failed node within 48 hours. The node counts as unavailable until replaced.
4.2 A replacement has the same GPU model, memory and interconnect as the failed node.
4.3 Capacity is accepted after the acceptance tests of Annex A: burn-in, interconnect bandwidth and storage throughput.

## 5. Performance
5.1 The values measured at acceptance are a floor: a measured value below 90% of the acceptance value is Unavailability.

## 6. Support
6.1 Support is available on business days, 09:00 to 17:00 CET, by ticket. The target first response for a critical incident is 4 business hours.
6.2 A named technical contact and an escalation path are listed in Annex C.

## 7. Price
7.1 The unit price is fixed for the first 12 months. From the second year the Provider may increase prices once a year by up to 3%.
7.2 No surcharge applies outside the price formula of this clause.

## 8. Data and exit
8.1 Data transfer out of the Provider's network is waived for 180 days after termination.
8.2 Customer data is deleted within 30 days after termination and the Provider gives a deletion certificate.
8.3 The Provider may move the Committed Capacity to another data center only with the written consent of the Customer.

## 9. Liability and force majeure
9.1 The Provider's total liability is limited to the fees paid in the 12 months preceding the claim. The Provider is not liable for loss of data, profits, or training progress.
9.2 Force majeure excludes the Provider's supply chain and power supply.
9.3 The Provider may suspend service for non-payment after 15 days written notice.
9.4 The Provider may not terminate for convenience.
