# E1 — Evidence-Bearing Human Objective Integration

**Upstream:** E0 PR #762, issue #760. **External contract reference:** URA PR #756. This E1 branch builds on the E0 branch but **does not import, merge, edit, or admit** #756. Review as a stacked PR.

## Run (repository root)

```bash
python3 experiments/human_objective_e1.py --objective "Find training and certification resources useful for HumanAIOS"
python3 -m unittest discover -s tests -p test_human_objective_e1.py -v
```

## What the output actually means

- E1 interprets the objective by deterministic keywords and explicitly lists unknown constraints. It does **not** infer organizational competency gaps from an external graph.
- E1 accepts caller-supplied **synthetic** normalized URA-format records and screens for safe structural provenance and non-authorizing status. No live provider is queried.
- A SHA256 digest inside a supplied record is a *claim*, not independently attested evidence. It must **not** be represented as actual verification.
- E1 makes suggestions for *review*, not real qualification, eligibility, enrollment, or money movement.
- It does not call `hmbm_compat.project`, read or mutate HMBM custody, update DHP, release GEN-003, or confer prediction authority.

## Boundaries and review controls

- Provenance mismatch, absent digest, invalid URL, execution/authorization claims, and unsupported fixtures fail closed.
- E1 does not independently establish that a source hostname is in a trusted registered-provider allowlist; until adapter integration has its own admission, do not interpret these records as verified URA output.
- No inbound Gmail processor or outbound mailer is installed; first human reply was manually processed. Do not post personal email content to public issue.
- Historical eligibility remains solely the concern of separately verified HMBM evidence and trusted verifier; GEN-003 and existing canonical state unchanged.
- CI passing is technical evidence, not policy admission.

## Admission stages

1. Run E0 and E1 tests and inspect PR CI at exact head.
2. Review the independent #756 URA normalized contract for compatibility. Do not implicitly merge its branch.
3. Human tests explanation correctness and explicit abstention.
4. Later, with separate authorization: implement a real registered URA adapter consumer, independent verifier, privacy-scoped email intake, and a human review/send step.
