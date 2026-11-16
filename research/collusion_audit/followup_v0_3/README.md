# V0.3 reviewer-directed follow-up — offline only

**Authority:** NONE. **Behavioral results:** NOT RUN. **Status:** additive workbench based on the public October review; not a retroactive October reanalysis and not a live-swarm experiment.

- `PROTOCOL_V0_3.md`: preregistration **candidate**, blind private assessment, real shared-error feasibility, quotas, two independent reviews and holdout policy.
- `SEMANTIC_MONITOR.md`: semantic prompt and strict input/output boundaries (no provider invoked).
- `harness.py`: stdlib-only schedule, harder inert numeric oracle, checks for label leakage and UNKNOWN, and retry-by-transport policy.
- `test_harness.py`: synthetic offline regressions. They do NOT measure detector performance.
- `REVIEW_RESPONSE.md`: concise October findings and the review changes.
- `freeze_receipt.json`: local file and schedule digests for verification; it does not authenticate an independent preregistration timestamp.

Run from this directory: `python3 -m unittest -v test_harness.py`. No dependencies or network access. Do not add an inference provider without a separately reviewed and approved execution scope.

Relation: Apart October project `talk-actions-and-planted-approval-pacts-an-exploratory-audit-d106`; existing HumanAIOS research PR #1010; Swarm Trusted Host PR #1153 is a separate, draft security workbench. No merge or real-model call is granted by this follow-up.
