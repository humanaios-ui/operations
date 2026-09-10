# Candidate Block: Q-NF-SCHEMA-01 — Unify NF_LEDGER Schema

**Z1 Proposer:** Claude (AI agent)  
**Date Submitted:** 2026-09-10  
**Phase:** 1 (Sep 16–27)  
**Priority Queue Score:** 8 (pending authoritative queue transition)  
**Status:** DRAFT — calibration_ref pending before Z2 ratification request

---

## Work Order

**Title:** Unify NF_LEDGER schema and resolve 4 format incompatibilities  
**Owner:** Z1 (design) + Z3 (implementation)  
**Due:** 2026-09-18 (research complete); 2026-09-23 (deployed to main)  
**Blocking:** Q-MOLT-04 and authoritative queue/routing transitions

---

## Problem Statement

Four incompatible calibration ledger formats exist across the codebase:

1. **nf_ledger_v0_1** (humanaios/REGISTERED.md) — Score-only format, no prediction tracking
2. **molt_cycle events** (conceptual in system_graph.json) — Separate schema for molt proposals/outcomes
3. **specimen_intake ledger** (empirica-foundation-evaluator) — Claim resolution tracking, N per predictor
4. **breadcrumbs** (audit trail in empirica repositories) — Decision provenance, not standardized

**Impact:** Molt Cycle cannot measure its own predictions (no unified place to record them). Brier scores per predictor cannot be aggregated. B.6 receipt reconciliation cannot walk claims back to outcomes.

---

## Proposed Solution

**NF_LEDGER.jsonl** — Single authoritative hash-chained calibration ledger.

**Location:** `ledgers/NF_LEDGER.jsonl`  
**Format:** JSONL (one record per line), hash-chained, append-only  
**Scope:** Every molt, specimen outcome, and calibration signal

**Key changes:**
- Molt events ARE NF_LEDGER entries (not separate file)
- Specimen outcomes feed Brier calculation in the same ledger
- Breadcrumbs embedded as optional fields (session_id, breadcrumb, z2_ratified_at)
- Hash chain prevents tampering; planned CI gate enforces append-only

**Schema:** See attached `NF_LEDGER_SCHEMA_v1.md`

---

## Four Format Resolutions

### 1. nf_ledger_v0_1 → v1.0 Unification

**Prior:** REGISTERED.md contained score records only
```
{confidence: 0.85, topic: "calibration", date: "2026-08-15"}
```

**New:** Full molt record with prediction, window, outcome, hash chain
```
{molt_id: "M-20260916-0001", constant: "...", prediction: {...}, 
 outcome: "KEEP", brier_actual: 0.14, prior_hash: "...", hash: "..."}
```

**Migration:** Backfill v0.1 as `record_type="HISTORICAL"` with preserved predictor identity and historical prediction object, then recompute hash chain after genesis.

### 2. molt_cycle events → Unified

**Prior:** molt_events.jsonl (conceptual) with separate MOLT/MEASURE/KEEP/REVERT events

**New:** Single NF_LEDGER entry lifecycle:
- APPLY phase: Write with outcome="MEASURING"
- MEASURE phase: Append chained resolution record with outcome="KEEP"|"REVERT", brier_actual
- KEEP/REVERT: Emit as events downstream, but source of truth is NF_LEDGER

**Result:** One authoritative record. Events are projections.

### 3. specimen_intake ledger → Unified

**Prior:** Separate specimen_intake_v0.2 JSON tracking claim → resolution → N_resolved

**New:** Specimen outcomes as NF_LEDGER entries with:
- `predictor_id` and `variable` preserved for aggregation identity
- `prediction_value`, `actual_value`, `scale_max`, `binary`, `confidence` preserved
- `prediction.probability` = predictor's assigned probability
- `brier_actual` = (`prediction_value` - normalized `actual_value`)²
- `outcome` (`KEEP`/`REVERT`) tracked as a separate falsifier result, not as `actual_value`

**Example:**
```json
{molt_id: "M-20260917-S001", constant: "specimen:claim-RQ1-042",
 predictor_id: "specimen-evaluator", variable: "claim-RQ1-042",
 prediction: {metric: "claim_resolution", probability: 0.73},
 prediction_value: 0.73, actual_value: 1.0, scale_max: 1.0, binary: true, confidence: 0.73,
 outcome: "KEEP", brier_actual: 0.073}
```

**Integration:** Specimen calibration automatically aggregated into per-predictor Brier via NF_LEDGER.

### 4. breadcrumbs → Unified

**Prior:** Audit logs scattered in empirica repos, no standard format

**New:** Optional fields in every NF_LEDGER entry:
- `breadcrumb`: Human name (e.g., "Q-MOLT-04 window close")
- `session_id`: Session that created molt
- `z2_ratified_at`: Explicit timestamp

**Result:** Complete decision → measurement audit trail in one record. B.6 receipt reconciliation can walk entry.session_id back to transcript.

---

## Technical Deliverables

**Q-NF-SCHEMA-01 completion requires:**

1. **NF_LEDGER_SCHEMA_v1.md** (15 KB, delivered)
   - Field definitions, format rules, hash chain spec
   - Brier Skill Score calculation
   - Molt Cycle integration pseudocode
   - Genesis record seeding

2. **CI gate enhancement** (planned `z2_ratification_gate.yml`)
   - Validate NF_LEDGER hash chain on every merge
   - Enforce append-only (no deletions, no reordering)
   - Reject if anti-cascade rules violated (K=3, revert freeze)

3. **molt_cycle.py skeleton** (Phase 1, before Q-MOLT-04)
   - Read NF_LEDGER, extract last record, verify hash
   - Aggregate Brier per predictor
   - Check anti-cascade freeze rules

4. **Genesis record** (0-line)
   - Initialize ledgers/NF_LEDGER.jsonl with system:initialized entry
   - Commit to main at Phase 1 launch (Sep 16)

---

## Falsifier

**Claim:** NF_LEDGER schema unifies all four incompatible formats and enables Molt Cycle measurement.

**This claim is FALSE if:**
- Molt predictions cannot be recorded in NF_LEDGER in a way that Molt Cycle can read at window close, OR
- Specimen calibration cannot be aggregated into per-predictor Brier from NF_LEDGER entries, OR
- The hash chain cannot prevent reordering/deletion (CI gate fails to catch tampering in 2+ tested scenarios), OR
- Anti-cascade enforcement cannot freeze a constant after 2 consecutive reverts

**Test method (Phase 1):**
- Create 3 test molts with known predictions
- Measure outcomes at window close
- Verify Brier calculated per falsifier
- Attempt hash-chain tampering; verify CI gate rejects
- Create scenario triggering 2 reverts; verify constant frozen

**Success criterion:** All 4 tests pass by 2026-09-23 (Phase 1 close).

---

## Unblock Path for Q-MOLT-04

Q-MOLT-04 (Molt Cycle) is blocked on this schema because it needs:
- Known record format to read NF_LEDGER
- Hash-chain validation routine
- Brier calculation implementation
- Anti-cascade rule checks

Once this schema is ratified, calibration_ref is attached, and queue blockers are formally cleared, Q-MOLT-04 can proceed with implementation confidence that the storage format won't change mid-sprint.

---

## Z2 Review Checklist

- [ ] Falsifier is testable and unambiguous
- [ ] Four incompatibilities actually resolved (review each mapping above)
- [ ] Hash chain prevents tampering (review CI gate spec in schema)
- [ ] Brier calculation is mathematically sound (review formula)
- [ ] Schema extends without breaking existing records (review migration path)
- [ ] Molt Cycle integration is viable (review pseudocode in schema)

---

## Summary

This candidate unifies HumanAIOS's scattered calibration tracking into a single authoritative, tamper-evident ledger. It resolves 4 format incompatibilities and enables the Molt Cycle (Phase 1's core learning function) to measure its own predictions.

**Ratification requested after calibration_ref attachment.** Upon Z2 signature and queue status transition, Z1 deploys genesis record to main.
