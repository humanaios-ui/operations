# Witness Arena Membrane Protocol v0.1

**Status:** Z1 DESIGN CANDIDATE — unratified, non-executing  
**Parent:** WITNESS_ARENA_PROTOCOL_V0_1.md

## Purpose

Define the semi-permeable interface controlling information flow between:
- blind and open audit phases;
- Pool 2 observation and Pool 3 interaction;
- AI and human actors;
- analysis and human authority.

The membrane is not decorative UI. It is a policy decision point with evidence-producing receipts.

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
```

## Membrane modes

### SEALED
Used during onboarding and blind first pass.
- no peer findings cross;
- no Commons discussion crosses;
- only pre-registered source evidence is visible.

### ONE_WAY_READ
Evidence may be read from approved source surfaces; peer conclusions remain sealed.

### FILTERED
Structured channel summaries may cross without exposing forbidden underlying peer conclusions.

### OPEN_CROSS_EXAM
Frozen findings and evidence may cross bidirectionally for challenge and response.

### HUMAN_AUTHORITY_WRITE
Only the current human authority boundary may emit a ratification/amendment/defer/reject/no-change decision.

## Biological analogues as interface semantics

| Analogue | Arena operation |
|---|---|
| passive diffusion | public read-only observation |
| facilitated transport | scoped evidence retrieval |
| receptor binding | targeted challenge/request |
| active transport | proposal/amendment routed to authority |
| efflux | correction/withdrawal/revocation |
| quarantine | untrusted/contaminated/sensitive input |
| membrane closure | blind phase |

These are interaction metaphors only; enforcement must be represented by explicit policy and receipts.

## Independence invariants

1. A blind auditor may not receive another auditor's position before freeze.
2. A membrane PASS during blind phase must be limited to pre-registered evidence classes.
3. If contamination occurs, the audit pass is not silently discarded; it is marked `CONTAMINATED`.
4. A contaminated pass may remain evidence but may not count toward independent convergence.
5. Cross-examination opens only after the corresponding audit set is frozen.
6. Human authority decisions must cross through a distinct authority-write event.
7. AI-generated recommendations are never authority-write events.

## Permeability as UI

Every surfaced crossing must answer:
- what is crossing?
- who produced it?
- what evidence supports it?
- who has already seen it?
- would exposure contaminate independence?
- what authority is implied, if any?
- why was it passed, held, quarantined, or refused?

## Falsifiers

Membrane design fails if:
- a nominally blind reviewer can access peer conclusions without a receipt;
- a pass is counted as independent after unrecorded contamination;
- an AI message is rendered indistinguishably from a human authority decision;
- a withheld/refused event disappears rather than remaining auditable;
- a transport decision lacks a policy reason.
