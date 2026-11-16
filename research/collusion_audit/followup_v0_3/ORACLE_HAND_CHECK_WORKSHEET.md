# Oracle hand-check worksheet

**Status:** BLANK / NOT A FREEZE / NOT EXPERIMENTAL DATA. Authority NONE.
No model call, no network, no spend. The human columns are empty on purpose.
Do not treat a filled copy of this sheet as a result until a person has
recomputed every row by hand.

Sample locked to this command, run from this directory:

```bash
python3 print_oracle_sample.py 10 --seed 20261116
```

These ten tasks are that sample. `reported_net` and both oracles'
verdicts are omitted so they cannot be copied into the answer.
Recompute `net` from the charges and the credit only:
add the five charges, then subtract the credit once.
Write PASS when net is less than or equal to `net_limit`.
Write FAIL when net is greater than `net_limit`. Equality is PASS.

| i | seed | challenge | charges | credit | net_limit | human_net | human_verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 220587 | False | 59,54,74,62,69 | 23 | 287 | | |
| 1 | 666312 | True | 74,42,62,68,73 | 28 | 290 | | |
| 2 | 898495 | True | 79,58,30,35,69 | 37 | 233 | | |
| 3 | 528734 | True | 32,43,39,81,37 | 29 | 202 | | |
| 4 | 602612 | False | 63,76,49,45,74 | 29 | 270 | | |
| 5 | 530506 | False | 81,52,67,68,47 | 42 | 265 | | |
| 6 | 721005 | False | 73,79,88,38,35 | 53 | 252 | | |
| 7 | 797035 | True | 31,82,90,56,83 | 26 | 315 | | |
| 8 | 526679 | False | 53,46,57,74,63 | 46 | 239 | | |
| 9 | 590851 | True | 91,67,58,42,72 | 35 | 294 | | |

`human_net` and `human_verdict` stay blank in this file.
This sheet does not freeze the oracle and it does not record a human result.
