# Q-SMAG-RATIFICATION-01: Z2 Architectural Decisions

**Status:** AWAITING_Z2_SIGNATURE  
**Created:** 2026-09-24  
**Authority:** Z2 (carly.r.anderson@gmail.com / Night)  
**Decision Window:** 48 hours (per CLAUDE.md §A)  
**Reference Document:** SMAG_REEXAMINATION.md (merged to main, commit db61a1f3)

---

## Ratification Context

SMAG_REEXAMINATION.md consolidated architectural issues from PRs #471, #474, #479 and framed 6 decisions for Z2 authority. This document records Z2's choices and cryptographic signature authorizing Phase 2 implementation.

---

## Z2 Decisions (PENDING)

### Decision 1: Measurement Contract

**Question:** How should SMAG gate compute merge authority predicate?

**Z2 Choice:** _____ (A/B/C/D or custom proposal)

**Rationale:** (Optional Z2 explanation)

---

### Decision 2: Z2 Ratification Validation

**Question:** How should system cryptographically validate Z2 signature on profiles?

**Z2 Choice:** _____ (A/B/C/D or custom proposal)

**Rationale:** (Optional Z2 explanation)

---

### Decision 3: Workflow Surface

**Question:** Which CI workflow file should implement SMAG gate?

**Z2 Choice:** _____ (A/B/C or custom proposal)

**Rationale:** (Optional Z2 explanation)

---

### Decision 4: Authority Model

**Question:** Should Phase 1 SMAG gate be advisory or blocking?

**Z2 Choice:** _____ (A/B/C or custom proposal)

**Rationale:** (Optional Z2 explanation)

---

### Decision 5: Data Integrity Constraints

**Question:** How should gate handle malformed/missing ledger data?

**Z2 Choice:** _____ (A/B/C or custom proposal)

**Rationale:** (Optional Z2 explanation)

---

### Decision 6: review_bar Enforcement

**Question:** How should review_bar requirement be enforced in Phase 1?

**Z2 Choice:** _____ (A/B/C or custom proposal)

**Rationale:** (Optional Z2 explanation)

---

## Ratification Signature (PENDING)

Once decisions are finalized, Z2 signs:

```
RATIFIED_BY: carly.r.anderson@gmail.com
RATIFIED_AT: <ISO8601 timestamp>
DECISIONS: D1: <choice>, D2: <choice>, D3: <choice>, D4: <choice>, D5: <choice>, D6: <choice>
SIGNATURE: sha256(<exact candidate bytes before this signature block> | by=Night | at=<timestamp> | decision=ACCEPT)
```

---

## Phase 2 Handoff

Upon Z2 signature, this document authorizes Phase 2 implementation to:
1. Port all preserved technical fixes from #471/#474/#479
2. Implement chosen measurement contract (D1)
3. Implement chosen ratification validation (D2)
4. Place gate in chosen workflow surface (D3)
5. Enforce chosen authority model (D4)
6. Handle data integrity per chosen strategy (D5)
7. Implement review_bar enforcement per choice (D6)

All Phase 2 PRs reference this document: "Implements per Q-SMAG-RATIFICATION-01 Z2 decisions."

---

## References

- **SMAG_REEXAMINATION.md:** Architecture decision framework (6 questions, options A/B/C/D per decision)
- **CLAUDE.md:** Z2 ratification authority, 48-hour decision window, RATIFY event format
- **Consolidated PRs:** #471, #474, #479 (preserved in SMAG_REEXAMINATION.md)
