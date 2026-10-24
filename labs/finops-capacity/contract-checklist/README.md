# Lab 15.4 — Reading a capacity contract (module 15, `finops-capacity`)

A review grid applied by a script to a **FICTIONAL** GPU capacity contract (`fictional_contract.md`: invented provider,
invented numbers, planted problems) and to its version after one negotiation round (`fictional_contract_negotiated.md`).
Nothing here is a real contract or legal advice. The structure of the clauses (availability measured by minutes, credits as
a percentage of the monthly fee, sole remedy, claim deadlines) mirrors what public cloud SLAs do; for a real one, read the
provider's own page the day you decide (the module page quotes the AWS EC2 and Google Compute Engine SLAs with their dates).

```
fictional_contract.md              26 numbered clauses, 4 deal-breakers planted
fictional_contract_negotiated.md   the same after one round: a plausible partial outcome
rubric.yaml                        24 graded items: regex, thresholds, weight, deal-breaker flag, "ask"
review.py                          deterministic scorer; exit status 1 if a deal-breaker is red
sla.py                             availability per node-hour, credit tiers, value of lost training time
expected.json, answer_key.md       the answer key (statuses; commented table of the deal-breakers)
tests/                             12 tests
verify.sh                          pytest, then the two reviews with the expected exit statuses
```

```bash
export PYTHON=/path/to/python           # needs pytest and pyyaml
PYTHON=$PYTHON bash verify.sh           # prints "contract score 7/100 ..." then "contract score 88/100 ..."
$PYTHON review.py fictional_contract.md rubric.yaml
```

Exercise: before opening `answer_key.md`, read the contract and write your own list of the five clauses you would
refuse to sign; then compare with the script, and change a threshold in `rubric.yaml` to see which findings move.
The score is a sorting aid, not a measurement: weights and thresholds are the course's choices.

Limit, stated on purpose: flag items turn red when the faulty wording is *present* and stay green when it is absent, so a
contract that is silent on a subject can look green. On a real contract, replace the regular expressions by a manual,
clause-by-clause survey (the grid itself, its weights and its "ask" column stay useful).
