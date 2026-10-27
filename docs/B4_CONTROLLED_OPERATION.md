# B4 content migration — controlled-operation contract

Session graph: operations#759. Operation: `B4_CONTENT_MIGRATION`.

B4 is a **scoped copy operation**, not a general executor, a coordinator state mutation, an admission grant, or merge authorization.

1. Issue #759 must be admitted by the existing coordinator replayed state projection.
2. Migration plan must identify exactly one seat, a SHA-256 digest, source and target commit pins, and a unique operation ID.
3. Approval must be a GitHub API-observed issue comment by an authorized actor, with the **exact JSON object** described below as its whole body.
4. The validator rejects missing or stale state, absent/ambiguous approvals, mismatched commits, expired approval, and replayed operation IDs.
5. CI checks the validator's negative cases. **This branch does not install a privileged production execution workflow.** A production workflow must independently fetch the trusted default-branch implementation, verify branch/state SHA, authenticate GitHub API data, and bind a durable atomic consumed-ID ledger before invoking the migration helper.
6. JSON evidence objects are integration inputs; independently verify their provenance before use. `source=github_api` alone is **not authentication**.

Approval comment format:
```json
{
  "schema": "humanaios.b4-admission.v1",
  "decision": "APPROVE",
  "operation": "B4_CONTENT_MIGRATION",
  "issue": 759,
  "seat": "seat-001",
  "plan_sha256": "<64 lowercase hex>",
  "source_commit": "<40 lowercase hex>",
  "target_commit": "<40 lowercase hex>",
  "operation_id": "B4-unique-identifier",
  "expires_at": "2026-10-10T00:00:00Z"
}
```

### Limits
A user saying "admission approved" authorizes work to proceed but does not itself prove a replayed coordinator state transition. No B4 content movement is performed by this PR. A trusted production collector and replay-safe durable ledger are still required before actual execution can be enabled.
