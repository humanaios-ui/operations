# IEW-001 — Independent Witness / Coordinator Boundary

**Status:** Z1 experimental control, not ratified. No automatic admission or merge authority.

## Inspected production contract

The default-branch `.github/workflows/repository-admission-gate.yml` uses `pull_request_target`, checks out the **trusted default branch**, obtains an exact coordinator state revision, checks `merge_authority: false`, verifies replay and calls `tools/repository_coordinator_v0_1.py --gate`. The coordinator's `_admission_evidence` accepts explicit PR admission in canonical state or closing links to admitted issue numbers; it does not accept arbitrary evidence receipts. Evaluation admission additionally requires an authorized human review tied to an issue in the prescribed state. Control-plane exemption is a distinct routing lane, not evidence-driven promotion.

## Threat cases

A: Read-only file open followed by fabricated stdout.

B: Self-consistent SHA-256 chain containing a hand-forged receipt.

C12: Import expected source then print invented stdout.

Each is injected as a candidate-supplied `witness_receipt` and must **not** change the actual coordinator lane or admission facts. These fixtures test non-promotion, not independent execution authenticity.

## Protected infrastructure / remaining prerequisites

The workflow in this PR is **not independently trusted until merged into an adequately protected base branch** and executed from that trusted branch. A draft PR can alter its own CI; its green CI is not an independent witness. Repository administrators must confirm GitHub rulesets/branch protection, required checks, CODEOWNERS review, permission separation, and inability of candidate authors to edit witness controls or bypass the branch rules. A separate trusted runner with pinned inputs, controlled signing key, external anchoring, and actual re-execution is still needed for independent experiment attestation. This patch does not silently modify `REPOSITORY_COORDINATOR_POLICY.json` or coordinator state.

## Acceptance

1. Confirm workflow runs from trusted main after review.
2. Confirm all five negative controls pass against the real coordinator.
3. Review protection rules and enforce required statuses; the workflow source alone cannot prove enforcement.
4. Add independent re-execution of pinned experimental commit in a later milestone, with exact versus tolerance-class comparisons and authenticated artifact provenance.

A Z1 positive result is *research evidence only*. Z2 authorization is separate.


## IEW-002 — explicit outcome-comparison boundary

`witness_gate.py` introduces a deliberately non-authorizing comparison contract. It requires externally captured source/input hashes, stdout digest and exit code; it rejects read-only-open / import-then-print false claims if the witness observation disagrees, treats a locally forged SHA-256 chain as inert in the absence of external observation, and ignores receipt-supplied `trusted_context` or `VERIFIED_EXECUTED` labels. Even `OUTCOME_MATCH` retains `admission_effect: NONE` and `independently_attested: false`.

**Security limitation:** In the tests, `observed` and `trusted_context` are controlled fixtures, not a trusted real GitHub runner. Therefore the tests establish fail-closed translation semantics, not independent execution or authenticated witness identity. `stdout` equality is exact; nondeterministic outcomes (e.g. TIMEOUT) need a separately specified comparator. No PR may call this contract an independent attestation until a protected workflow actually executes the pinned experiment and supplies observations outside candidate control.

## CI follow-up observed on PR #777 (head 51860c25)

Tool-manifest failed because `.z1-control/b4_fold_execute.py` exists but is absent from `tools-manifest.yaml`. Quality baseline failed because `tools/tests/test_outlier_public_adapter_v0_1.py` is missing from both the quality-baseline pytest enumeration and `tools/intent_os_test_harness_v1_0.py` baseline list. These failures are tracked as pre-existing cross-workstream integration issues; do not silently edit the protected tool manifest or unrelated test schedule within this research PR. Both require coordinated owner review.

## IEW-002 next acceptance requirements

- Pin experiment source/inputs to immutable git/object digests.
- Execute them on an independently administered runner with no candidate ability to edit witness control or signing materials.
- Capture program stdout/stderr/exit code at the runner boundary; never parse them from an author-written ledger.
- Sign or attest those captured observations with a verified run identity and anchor them externally.
- Validate branch protection/rulesets and required checks empirically.
- Run the same attack fixtures through the *original vulnerable checker* as demonstrations, then prove independent witness mismatch blocks promotion through a production gate.
- Preserve separate Z2 admission and merge authority; never treat an `OUTCOME_MATCH` as authorization.
