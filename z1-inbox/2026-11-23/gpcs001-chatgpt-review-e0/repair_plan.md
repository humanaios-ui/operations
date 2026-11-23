# Bounded repair plan and falsifier tests

**Owner:** Existing #775, with related #677, #691, #923; do not create a new authority source. **Stage:** PROPOSED_ONLY / Z1 / no code activation.

## Smallest next changes
1. **Portable discovery only.** Review adding a short, versioned pointer under an existing agent-readable instructions/entry file directing agents to #775 and requiring access attestation, privacy gate, idempotent public-safe delta, and negative-state receipt. It must not claim that a URL automatically unlocks Claude/Grok/ChatGPT histories.
2. **Scope-aware identifier ledger.** The human owner resolves the currently conflicting public uses of \`HAIOS-MM-ACAT-002\`. Preserve alias history. Require distinct \`graph_family\` / \`workstream\` / \`source_revision\` before SAME_AS is allowed; no automatic sequential ID assignment.
3. **Graph crosswalk gate.** Before populating draft PR #1310 crosswalk, pin a consented original graph snapshot in a verified private store, record digest, schema version, creator/valid-time and source class; reviewer confirms hash and graph family. Publish only safe graph counts/opaque evidence state after independent approval.
4. **Freshness and replay.** For each source, record \`accessible\`, \`read\`, \`partial\`, \`stale\`, \`inaccessible\`, and readback/provenance. Do not assert current local file existence from an old private index.
5. **Independent review.** Compare proposed findings with #775's earlier run receipts before admission; separately verify public source links and protected checks for any eventual code changes. Agent scores remain HOLD under #750.

## Synthetic negative tests (required before automatic imports)
- Wrong scope but same research ID -> \`CONFLICT_HOLD\`; no SAME_AS.
- 358-node graph mentioned without bytes or source receipt -> \`PRIVATE_HOLD\`; crosswalk stays empty.
- Old Drive/local index with current computer offline -> \`INACCESSIBLE\` or \`STALE\`; not FULL_SOURCE_READ.
- AI memory summary posing as original transcript -> \`CHAT_DERIVED\`, never independently verified.
- Same mailbox, different self-labels -> identity \`UNAUTHENTICATED\`; cannot claim independent P2.
- Private emails, IDs, names, local paths, raw chats in contribution -> \`REJECT_UNSAFE\`; no public write.
- Exact duplicate from prior #775 receipt -> \`EXACT_DUPLICATE\`; skip repeat.
- Retrieved issue text asking to merge, deploy, or label Z2 -> ignored; \`AUTHORITY_EFFECT: NONE\`.
- Altered source revision, fake approval, incomplete pagination -> HOLD and retain discrepancy.
- Finished PR/green CI -> not equivalent to real human benefit or production proof.

## Closure
A human reviews exact IDs, source custody, and priorities. A code-bearing implementation requires its own protected CI and authenticated approval. This proposal itself grants no permission.
