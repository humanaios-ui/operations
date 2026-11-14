# Cycle-003 Project Output and Merge Gate

**Status: EXPERIMENT IN PROGRESS — DO NOT MERGE**

PR #597 is the evidence-bearing project container for HMBM-CYCLE-003. The branch remains unmerged while the cycle is active. Merge is a ratification event after the experiment, not an experimental operation.

## Freeze boundary

The experiment MUST NOT be changed merely to improve observed performance. The frozen HMBM universe, cohorts, operator ontology, cost model, schedules, model/rubric, H0 window, prediction rules, and omission audit remain unchanged.

DHP may record what happens to the experiment; it may not rewrite what the experiment was.

If an operational defect requires intervention during the cycle, preserve:
- pre-correction state;
- failure record;
- authority for intervention;
- exact correction;
- affected epochs/artifacts;
- post-correction verification;
- residual unknowns.

Corrections are evidence. They are not retroactive edits.

## Evidence accumulation

The PR may accumulate immutable or append-only experimental evidence:
- DHP transition receipts;
- candidate manifests and hashes;
- persistence/read-back receipts;
- communication receipts;
- acceptance receipts;
- omission audits;
- failure and exception records;
- checkpoint metrics;
- correction records;
- final Cycle-003 audit and project report.

An ACCEPTED receipt remains distinct from Git merge. Canonical HMBM state advances only through the experiment's Witness authority. Git merge advances repository canonical knowledge only after the project gate below is satisfied.

## Merge gate

PR #597 MUST remain unmerged unless all conditions are evidenced:

- [ ] `H24_COMPLETE`
- [ ] `FINAL_AUDIT_COMPLETE`
- [ ] `NO_UNRESOLVED_CANONICAL_GAPS`
- [ ] `DHP_EVIDENCE_CHAIN_VERIFIED`
- [ ] `FAILURES_AND_CORRECTIONS_ACCOUNTED`
- [ ] `FINAL_PROJECT_REPORT_COMMITTED`
- [ ] `HUMAN_REVIEW_COMPLETE`

If any gate is false or unknown, disposition is **HOLD / DO NOT MERGE**.

After the cycle, human review may result in MERGE, REVISE, or REJECT. Merge means the repository accepts the tested implementation and its attached evidence as project output; it does not erase failures or imply that every experimental hypothesis succeeded.

PAPER ONLY / NO REAL CAPITAL.
