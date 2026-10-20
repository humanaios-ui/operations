# PIER-001 · adversarial review and admission hold

**Review type:** Internal adversarial code review, not independent witness.
**State:** Z1 candidate, not production, not admitted; no new runtime interface.
**Scope:** `run.py`, synthetic fixture, scoring, tests and aggregate JSON output.

## Observed issues and changes

| ID | Original weakness | Impact | Candidate mitigation | Test |
| --- | --- | --- | --- | --- |
| R1 | Attacker view included `SYN-00`, while the hidden label is selected by `index % 3`. | Role could be reconstructed with no messages by a code-aware attacker. | Strip correlation ID before attacker call; attach it in trusted harness after claims return. | `test_no_case_id_leak_even_at_stage_zero` |
| R2 | One relevant citation made other irrelevant source IDs appear supported. | Citation laundering; aggregate support overstates evidence quality. | Require **each** cited message to support the stated value. | `test_mixed_valid_and_invalid_evidence_is_unsupported` |
| R3 | Fixture generator and attacker share hard-coded clues. | No generalization or independent blinding. | Keep labeled **synthetic instrument smoke**; disallow promotion to real-world inference conclusions. | `test_report_declares_no_blind_holdout` |
| R4 | Zero network/model calls were emitted as counters without network observation. | Receipt could be mistaken for independently audited calls. | Rename to `declared_calls`; document that it is static metadata. | `test_all_stages_observed_and_gates_pass` |

## Replication

```sh
python3 -m unittest discover -s tests -p 'test_pier_001.py' -v
python3 experiments/pier_001/run.py
```

Expected: 14 tests pass; `smoke_gates_pass: true`; fixture SHA256
`f03359f9d2c084f2665f1ddbd65ceba851860287714e0aa65c637c45e773976d`.
Correct role counts by stages (0, 1, 3, 6): (0, 0, 20, 30).

## Unresolved independent gates

- [ ] Independent reviewer reproduces test results against the exact PR head.
- [ ] Protected CI and CodeRabbit findings reviewed and resolved.
- [ ] Confirm no unregistered tool or policy/gate changes are required.
- [ ] Separate preregistration + approved privacy threat model before any model calls.
- [ ] Separate explicit authorization, consent, retention/deletion and recourse design before any human-sourced data.

**No authority effect.** Test success cannot merge, deploy, grant permissions, publish personal profiles, or approve the next phase. This candidate is designed solely for review.