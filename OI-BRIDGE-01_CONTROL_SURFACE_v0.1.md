# OI-BRIDGE-01: HAIOS Agent Bridge Control Surface Specification (v0.1.1)

**Status:** Z1 Candidate (awaiting Z2 ratification) — revision addressing adversarial reviews on PR #455  
**Date:** 2026-09-22  
**Author:** Claude (Z1 Proposer); revision by Grok (independent review integration)  
**Authority Reference:** CLAUDE.md §1 (Z1 proposal rights)  
**Revision note:** Incorporates findings from independent adversarial reviews (owner + Grok). Does not claim implementation. Standing: SPEC ONLY.

---

## Decision Object

**QUESTION:**  
How should registered AI nodes exchange messages, evidence references, and challenges while preserving provenance, independent judgment, and human authority within the HumanAIOS governance system?

**PROPOSED SCOPE:**  
Phase 0 Control Surface for OI-BRIDGE-01: a governed asynchronous communication substrate that supports MESSAGE → DELIVERY → RESPONSE → CHALLENGE → EVIDENCE → DISPOSITION → CONTINUE | HUMAN_REQUIRED, enforcing authority references without autonomous collective decision-making.

**PURPOSE:**  
1. Enable Z1 proposers to communicate hypotheses, findings, and evidence across node boundaries  
2. Preserve independent judgment — no node can cause another node to perform consequential actions based solely on message content  
3. Enforce authority references — consequential actions route through independently resolved authority (authenticated external event or cryptographic signature)  
4. Support Z2 ratification when human judgment is required — not for ordinary pre-authorized collaboration  
5. Provide falsifiable architecture — v0.1 can fail on clear, measurable criteria  
6. Foundation for Phase 1 (delivery + identity) and Phase 2+ (multi-node, ledger integration)

**NON-GOALS:**  
- Autonomous collective intelligence  
- Real-time synchronous decision-making  
- Credential storage or OAuth delegation  
- End-to-end encryption as a Phase 0 requirement  
- Consensus algorithms (nodes do not vote; Z2 ratifies authority; Z3 executes)

---

## Core Invariants (9 Critical Rules)

**I1: BRIDGE_ENFORCES_AUTHORITY_REFERENCES_BUT_DOES_NOT_CREATE_AUTHORITY**  
- Bridge validates that every *consequential* action references a valid authority decision.  
- Authority is not a self-asserted string. Resolution must terminate in:  
  - an authenticated external event (e.g. REGISTERED.md entry with verifiable provenance, GitHub commit attributable to Z2 identity), **or**  
  - a cryptographic signature over a canonical payload verifiable without trusting the bridge as signer.  
- A hash of a human-readable sentence plus `valid: true` is **not** authority.  
- Bridge does not create, modify, or delegate authority.  
- Violation: consequential action proceeds without independently resolved authority → PRIMARY FALSIFIER.

**I2: MESSAGE_BODY_IS_UNTRUSTED_INPUT**  
- Claim, evidence reference, and challenge content are untrusted external input.  
- No message body alone determines a node's consequential actions.  
- Nodes must verify evidence references (fetch, hash, timestamp).  
- Authenticity of the envelope is established by per-node asymmetric signature (preferred) or equivalent; bridge-held shared HMAC alone is insufficient if compromised-bridge is in scope.

**I3: OBSERVATION_IS_NOT_REGISTERED_FINDING**  
- An observation becomes a registered finding only after Z2 ratification and ledger entry (or explicit append-only disposition).  
- Epistemic standing starts as CLAIMED / OBSERVED, not REGISTERED.  
- Nodes must not treat non-REGISTERED observations as facts for consequential decisions.  
- Violation → secondary falsifier NON_REGISTERED_AS_FACT.

**I4: ESCALATION_IS_NOT_OPTIONAL**  
- When a node detects an escalation trigger, it must emit an escalation event.  
- Events are not suppressible or coalesced away.  
- Violation → secondary falsifier SKIPPED_ESCALATION / ESCALATION_SUPPRESSION.

**I5: DISPOSITION_OVERRIDES_CONTINUE — WITH CORRECT SCOPE**  
- DISPOSITION (HUMAN_REQUIRED, VOID, REVERT, authority grant/deny) overrides CONTINUE for *consequential* paths.  
- CONTINUE is valid for reversible, non-consequential, pre-authorized collaboration **without** mandatory Z2 ratification of every exchange.  
- Z2 is required for **authority**, not for conversation.  
- Violation: node continues *consequential* action despite pending HUMAN_REQUIRED or denied authority → secondary falsifier DISPOSITION_OVERRIDE.

**I6: NODE_IDENTITY_IS_IMMUTABLE_AND_VERIFIABLE**  
- Each node has a pre-established identity bound to authenticatable credentials (email, machine capability, Z2-issued token).  
- `sender_identity_verified` is **derived by the bridge/recipient**, never trusted from sender input.  
- Spoofing is detected at delivery and logged.  
- Violation → secondary falsifier SPOOFING.

**I7: EVIDENCE_REFERENCES_ARE_VALIDATED_NOT_ASSUMED**  
- Bridge records references; nodes validate (fetch → expected hash → observed hash → timestamp).  
- Validation produces a receipt: `{source, method, expected_hash, observed_hash, timestamp, result}`.  
- Failure → escalate or refuse consequential use.  
- Violation → secondary falsifier UNVALIDATED_EVIDENCE.

**I8: STATE_AXES_ARE_SEPARATED_AND_ENFORCED**  
- Visibility, epistemic standing, and delivery are **separate axes** (see §6).  
- Epistemic standing transitions are append-oriented: original records are not erased; SUPERSEDED / NARROWED / WITHDRAWN / UNRESOLVED may be appended.  
- Bridge cannot unilaterally rewrite historical messages.  
- Violation → secondary falsifier STATE_MUTATION_OUTSIDE_LEDGER.

**I9: HUMAN_AUTHORITY_IS_IRREPLACEABLE**  
- HUMAN_REQUIRED can only be cleared by Z2 (or governing human authority).  
- Mandatory for: sensitive data, credential scope, irreversible action, authority ambiguity, unresolved cross-node conflict after bounded challenge.  
- Violation → secondary falsifier HUMAN_REQUIRED_BYPASS.

---

## Primary Falsifier

**v0.1 FAILS IF:**  
One registered AI node can cause another registered AI node to perform a **consequential** action **solely because of message content** without a valid, independently resolved authority reference (authenticated external event or cryptographic signature over a canonical payload).

---

## Secondary Falsifiers

1. **SPOOFING** — Bridge accepts message claiming Node A identity from Node C.  
2. **TAMPERING** — Bridge/recipient accepts envelope that fails authenticity check.  
3. **ESCALATION_SUPPRESSION** — Trigger detected; escalation event not emitted.  
4. **NON_REGISTERED_AS_FACT** — Node treats non-REGISTERED observation as fact for consequential action.  
5. **SKIPPED_ESCALATION** — Trigger required escalation; node continued consequential path instead.  
6. **DISPOSITION_OVERRIDE** — Node ignores HUMAN_REQUIRED / denied authority and continues consequential action.  
7. **UNVALIDATED_EVIDENCE** — Node acts on evidence reference without successful validation receipt.  
8. **STATE_MUTATION_OUTSIDE_LEDGER** — Epistemic standing or historical message rewritten without append-only disposition / ledger event.  
9. **HUMAN_REQUIRED_BYPASS** — HUMAN_REQUIRED cleared by non-Z2 actor.  
10. **SCOPE_EXPANSION** — Consequential action outside granted authority scope without independent authorization.

---

## Phase 0 Control Surface

### 1. Node Identity Schema

```json
{
  "node_id": "claude-z1-proposer-20260922",
  "node_role": "Z1",
  "node_type": "ai_agent",
  "authenticated_identities": [
    {
      "type": "email",
      "value": "noreply@anthropic.com",
      "verified_by": "Z2",
      "verified_at": "2026-09-22T00:00:00Z"
    }
  ],
  "public_key": "ed25519:BASE64...",
  "session_id": "session_01Lm1ut3GdgQakWK694dj3wo",
  "active": true,
  "authority_cap": "Z1_PROPOSE"
}
```

Identity verification is performed by the bridge/recipient against pre-registered keys and Z2-verified bindings. Sender cannot self-assert `sender_identity_verified`.

### 2. Message Envelope Schema

```json
{
  "envelope": {
    "message_id": "msg_20260922_001",
    "sender_node_id": "claude-z1-proposer-20260922",
    "recipient_node_id": "night-z2-ratifier",
    "timestamp": "2026-09-22T14:30:00Z",
    "message_type": "HYPOTHESIS|FINDING|CHALLENGE|EVIDENCE|ESCALATION|DISPOSITION",
    "visibility_state": "PRIVATE|BLIND|RELEASED_TO_COMMONS",
    "epistemic_standing": "CLAIMED|EVIDENCE_CHECKED|OBSERVED|REGISTERED|SUPERSEDED|NARROWED|WITHDRAWN|UNRESOLVED",
    "delivery_state": "PENDING|DELIVERED|ACKNOWLEDGED|FAILED"
  },
  "body": {
    "intent": "Submit PR readiness assessment for #445",
    "claim": "PR #445 has no conflicts and passes all CI checks",
    "evidence_references": [],
    "classification": "INTERNAL"
  },
  "provenance": {
    "sender_signature": "ed25519_sig_...",
    "sender_identity_verified": null,
    "verification_note": "sender_identity_verified is set by bridge/recipient after check; never trusted from sender"
  }
}
```

Default classification: **INTERNAL / PRIVATE**. PUBLIC requires explicit release.

### 3. Authority Reference Schema (proof, not assertion)

```json
{
  "authority_reference": {
    "type": "EXTERNAL_EVENT|CRYPTOGRAPHIC_SIGNATURE|PRIOR_Z2_DECISION_BOUND",
    "resolution": {
      "method": "REGISTERED_MD_ENTRY|GITHUB_COMMIT_ATTRIBUTION|ED25519_SIG_OVER_CANONICAL_PAYLOAD",
      "source_ref": "REGISTERED.md#RATIFY-...",
      "canonical_payload": "PR#445|commit=abc123|decision=ACCEPT|by=Night|at=2026-09-22T14:35:00Z",
      "signature_or_event_id": "...",
      "verified_by_bridge_at": "2026-09-22T14:36:00Z",
      "verification_result": "PASS|FAIL"
    },
    "issued_by": "Z2",
    "scope": "MERGE_PR_445_ONLY",
    "expires_at": "2026-09-25T14:35:00Z"
  }
}
```

**Rejected forms:** `sha256("human readable sentence")` with `valid: true` and no external verification path; any authority object whose truth depends solely on fields supplied by the requesting node.

### 4. MESSAGE → DISPOSITION Flow (corrected)

**Step 1: MESSAGE** — Node A constructs envelope; signs with node key; classification defaults INTERNAL.  
**Step 2: DELIVERY** — Bridge verifies sender identity (derived), verifies signature, routes; sets `delivery_state=DELIVERED`.  
**Step 3: RESPONSE** — Node B: ACCEPT | REQUEST_EVIDENCE | CHALLENGE | ESCALATE.  
**Step 4: CHALLENGE** (optional) — Bounded; after bound exhausted without resolution → HUMAN_REQUIRED.  
**Step 5: EVIDENCE** — Independent validation; each node emits validation receipt.  
**Step 6: DISPOSITION**  
- Reversible / non-consequential / within pre-authorized scope → **CONTINUE** (no Z2 required).  
- Unresolved disagreement after bounded challenge → HUMAN_REQUIRED.  
- Consequential action requested → require independently resolved authority reference; if missing/ambiguous → HUMAN_REQUIRED.  
- Sensitive / irreversible / credential / authority ambiguity → HUMAN_REQUIRED.  
**Step 7: CONTINUE | HUMAN_REQUIRED** — Nodes act only on CONTINUE with valid authority where consequential; pause on HUMAN_REQUIRED until Z2 clears.

**Rule of thumb:** Z2 gates **authority**, not **conversation**.

### 5. Escalation Contract

Mandatory triggers: AMBIGUITY, CONFLICT, DRIFT, GAUGE, RECEIPT_GAP, VOID, AUTHORITY_UNCLEAR, SCOPE_EXPANSION.  
Escalation events are logged immediately; bridge cannot selectively drop them.

### 6. Separated State Axes

| Axis | Values | Purpose |
|------|--------|---------|
| **visibility_state** | PRIVATE, BLIND, RELEASED_TO_COMMONS | Who may read |
| **epistemic_standing** | CLAIMED, EVIDENCE_CHECKED, OBSERVED, REGISTERED, SUPERSEDED, NARROWED, WITHDRAWN, UNRESOLVED | What kind of belief it is |
| **delivery_state** | PENDING, DELIVERED, ACKNOWLEDGED, FAILED | Transport status |

**Append-only correction:** REGISTERED (or any standing) is not erased. Corrections append SUPERSEDED / NARROWED / WITHDRAWN / UNRESOLVED with pointers to the prior record.  
**Do not overload "SEALED"** to mean all three axes.

### 7. Threat Model (updated)

| Attack | Mitigation |
|--------|------------|
| Spoofing | Pre-registered identity + recipient/bridge-derived verification |
| Tampering | Per-node asymmetric signature; bridge does not hold the only authenticity secret |
| Escalation suppression | Escalation written to durable log before continue path |
| Non-registered as fact | Epistemic standing check before consequential action |
| Evidence spoofing | Validation receipt required |
| Authority bypass | Resolution must terminate in external event or crypto proof |
| Scope expansion | Scope field checked against requested action |
| Compromised bridge | Bridge cannot forge node signatures; cannot silently rewrite history |

### 8. Privacy & Retention

- Default: INTERNAL / PRIVATE  
- PUBLIC only on explicit release  
- Envelopes (non-REGISTERED): retain ≥7 days or until disposition  
- REGISTERED / escalation: permanent append-only  
- Session secrets: clear at session close  

### 9. Identity & RLS Model (implementable)

Principal mapping required (`node_principals`: auth_uid UUID → node_id TEXT + role).  
RLS policies join on principal map; client-supplied `node_id` alone never satisfies policy.  
See revision notes in PR #455 for full SQL example.

```sql
CREATE TABLE node_principals (
  auth_uid UUID PRIMARY KEY,
  node_id TEXT NOT NULL UNIQUE,
  role TEXT NOT NULL CHECK (role IN ('node','z2','z3','bridge')),
  active BOOLEAN NOT NULL DEFAULT true
);
```

### 10. Evidence Validation Receipt

```json
{
  "receipt_id": "evr_001",
  "message_id": "msg_20260922_001",
  "source": "https://...",
  "method": "fetch_and_sha256",
  "expected_hash": "abc123...",
  "observed_hash": "abc123...",
  "timestamp": "2026-09-22T14:31:00Z",
  "result": "PASS|FAIL|UNAVAILABLE",
  "validator_node_id": "night-z2-ratifier"
}
```

### 11. Adversarial Test Preregistration

T1 Spoofing · T2 Tampering · T3 Non-registered-as-fact · T4 Scope expansion · T5 HUMAN_REQUIRED bypass · T6 Evidence validation failure  
All must be registered before Phase 1 claims enforcement.

---

## Implementation Standing

| Component | Standing |
|-----------|----------|
| This control surface | **SPEC ONLY** — no runtime authority |
| PR Manager skill in this PR | **STUB** — fetchers return empty/None; GitHub wiring is Phase 1 |
| Bridge delivery / identity / ledger | **NOT STARTED** (Phase 1+) |

LANGUAGE_IS_NOT_IMPLEMENTATION: docs must not describe STUB surfaces as Active / Real-time.

---

## Roadmap

**Phase 0 (this document):** Control surface, invariants, falsifiers, schemas — awaiting Z2.  
**Phase 1:** Delivery layer, identity enforcement, asymmetric signatures, principal map, PR Manager GitHub wiring, honest status labels.  
**Phase 2:** Ledger integration, escalation durability, Z2 ratification automation.  
**Phase 3+:** Multi-node onboarding, INTENT-OS binding, anti-cascade.

---

## Related Documents

- CLAUDE.md — authority model  
- REGISTERED.md — findings and Z2 signatures  
- PRIORITY_QUEUE.md — blocker ranking  
- .claude/skills/pr-manager/* — STUB consumer (not Phase 0 authority)

---

## Z2 Decision Required

**Proposed:** Ratify OI-BRIDGE-01 Phase 0 Control Surface **v0.1.1** (this revision) as the Z1-registered design candidate.  
**Authority:** Z2 (Night).  
**Decision window:** 48 hours from the revision commit timestamp on PR #455 (not from the original PR open time; not midnight UTC of calendar day).  
**Falsifier:** Spec fails if primary or secondary falsifiers can be triggered in a conforming implementation without enforcement.

**Signature format (once ratified):**  
`RATIFY <content-hash of this file> | by=Night | at=<ISO8601> | decision=ACCEPT`  
bound to an authenticated external event or cryptographic signature — not a bare string claim.

---

*End of OI-BRIDGE-01 Phase 0 Control Surface Specification (v0.1.1)*
