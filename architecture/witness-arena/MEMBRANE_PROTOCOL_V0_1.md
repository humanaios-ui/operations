# Witness Arena Membrane Protocol v0.1.1

**Status:** Z1 DESIGN CANDIDATE — unratified, non-executing  
**Parent:** WITNESS_ARENA_PROTOCOL_V0_1.md  
**Revision:** v0.1.1 — adversarial hardening (structural independence claim narrowed)

## Purpose

Define the semi-permeable interface controlling information flow between:
- blind and open audit phases;
- Pool 2 observation and Pool 3 interaction;
- AI and human actors;
- analysis and human authority.

The membrane is a **policy decision point with evidence-producing receipts**.  
It is **not**, in v0.1, a capability-isolated enforcement barrier.

## Standing (honest)

| Claim | v0.1 status |
|-------|-------------|
| Auditable transport decisions | **IN SCOPE** |
| Receipts for every crossing attempt | **IN SCOPE** |
| Structural prevention of peer-conclusion access | **OUT OF SCOPE** until cryptographic sealed auditor contexts exist |
| Independence under compromised membrane writer | **NOT GUARANTEED** without external append-only log |

Blind-pass independence in v0.1 relies on **policy + receipts + operator/integrity controls**.  
Calling that "structural enforcement" is a LANGUAGE_IS_NOT_IMPLEMENTATION error.

## Transport model

Every attempted crossing is an envelope:

```yaml
transport_id:
epoch_id:
from_actor:
to_actor_or_surface:
direction: AI_TO_AI | AI_TO_HUMAN | HUMAN_TO_AI | HUMAN_TO_HUMAN
payload_ref:
payload_hash_or_content_ref:
purpose:
scope:
consent_ref:
authority_class:
prior_findings_visible:
sensitivity:
requested_transport:
```

Decision:

```yaml
decision: PASS | HOLD | QUARANTINE | REFUSE
reason_code:
policy_ref:
decided_by:
decided_at_observation:
resulting_visibility:
receipt_ref:
prev_membrane_event_hash:   # hash chain; required for external auditability
signature_or_commit_ref:    # binds event to producer; prevents silent rewrite
```

**Immutability:** Membrane events are append-only. Overwrites or deletions are falsifiers.  
**Validation:** Events enter the Evidence Graph only after signature/hash-chain check by a party that is not solely the membrane writer.

## Membrane modes

### SEALED
Used during onboarding and blind first pass.
- no peer findings cross (policy);
- no Commons discussion crosses;
- only pre-registered source evidence is visible (policy).

### ONE_WAY_READ
Evidence may be read from approved source surfaces; peer conclusions remain sealed (policy).

### FILTERED
Structured channel summaries may cross without exposing forbidden underlying peer conclusions.

### OPEN_CROSS_EXAM
Frozen findings and evidence may cross bidirectionally for challenge and response.

### HUMAN_AUTHORITY_WRITE
Only the current human authority boundary may emit a ratification/amendment/defer/reject/no-change decision.  
AI actors never emit this mode.

## Membrane authority (not a new tier)

Membrane PASS/HOLD/QUARANTINE/REFUSE decisions are **auditable observation records**.  
They do **not**:
- grant Z2/Z3 authority;
- revoke prior Z2 decisions;
- create a fourth governance tier.

Humans may override any membrane decision. The override is itself a recorded authority event.

## Independence invariants

1. A blind auditor may not receive another auditor's position before freeze (**policy**).
2. A membrane PASS during blind phase must be limited to pre-registered evidence classes.
3. If contamination occurs, the audit pass is marked `CONTAMINATED` (not silently discarded).
4. A contaminated pass may remain evidence but may not count toward independent convergence.
5. Cross-examination opens only after the corresponding audit set is frozen.
6. Human authority decisions must cross through a distinct authority-write event.
7. AI-generated recommendations are never authority-write events.
8. Back-dated or rewritten membrane events without hash-chain break detection are falsifiers.

## Contamination detection (required before operational claim)

v0.1 does not yet specify a mechanical detector. Before any operational claim:

```yaml
contamination_detection:
  mechanism: TBD  # e.g. sealed context hashes, access logs, time-bound audit windows
  detection_window: TBD
  self_report_required: true
  failure_to_report_consequence: mark pass CONTAMINATED; exclude from convergence counts
```

Until mechanism is defined, independence claims remain **process-level**.

## Cross-domain divergence escalation

When AI and human domains remain in material conflict after bounded challenge:

1. Do **not** pool-vote or compute combined agreement ratios.
2. Escalate to `HUMAN_AUTHORITY_AGENDA` with both domain records intact.
3. Minority evidence with stronger direct refs is not suppressed by majority convergence.
4. Epoch may pause on protocol-validity conflicts (e.g. ZONE_SEMANTICS disagreement) until human disposition.

## Falsifiers

Membrane design fails if:
- a nominally blind reviewer can access peer conclusions without a receipt;
- a pass is counted as independent after unrecorded contamination;
- an AI message is rendered indistinguishably from a human authority decision;
- a withheld/refused event disappears rather than remaining auditable;
- a transport decision lacks a policy reason;
- membrane events are rewritten without detectable hash-chain break;
- the system claims structural independence while only providing receipts.
