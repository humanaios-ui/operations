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
