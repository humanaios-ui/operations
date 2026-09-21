# Q-SMAG-CALIBRATION-SCHEMA-CONFORMANCE-01

**Proposal ID:** Q-SMAG-CALIBRATION-SCHEMA-CONFORMANCE-01  
**Date:** 2026-09-21  
**Authority:** Z1 (Claude) proposes; Z2 (Night) ratifies  
**Tier:** Tier 1 (schema/runtime contract)  
**Category:** Intent-OS Phase 1 integration blocker  
**Status:** Awaiting Z2 decision  
**Blocks:** Z3 s2 (Intent-OS binding), Z3 s3 (monthly automation wiring)

---

## Executive Summary

WITNESS_STATE_V0_1.schema.json declares `calibration_profile.substrates` with `additionalProperties: false`, but BASELINE_S092126.json contains nine additional fields per substrate (measured_gap_rate, measured_clean_rate, status, calibration_notes, acat_dimensions_stressed, failing_checks_observed, next_review_date, ratification_date, expires_at). This violates the schema contract and prevents Intent-OS Phase 1 runtime validation and capability binding.

**Z2 Decision Required:** Should we expand WITNESS_STATE to v0.2 (Option A) or create separate ProfileSchema.json (Option B)?

---

## Root Cause Analysis

The schema mismatch emerges from two independent design processes:

1. **WITNESS_STATE_V0_1 design (Phase 0):** Created to capture runtime state at merge gate, defined minimal calibration_profile fields.
2. **Calibration profile data (SMAG feedback):** Designed to capture auditable measurement, gap analysis, and per-substrate metadata for Z2 ratification.

**Schema declares:**
```json
"calibration_profile": {
  "type": "object",
  "properties": {
    "substrates": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "confidence_weight": {"type": "number"},
        "review_bar": {"type": "string"},
        "merge_pause_threshold": {"type": "number"},
        "calibration_floor": {"type": "integer"}
      }
    }
  }
}
```

**Profile data contains (actual BASELINE_S092126.json):**
```json
"human:humanaios-ui": {
  "confidence_weight": 1.0,
  "review_bar": "standard",
  "merge_pause_threshold": 0.25,
  "calibration_floor": 10,
  "ratification_date": "2026-09-21",
  "expires_at": "2026-12-20",
  "measured_clean_rate": 0.9,
  "measured_gap_rate": 0.1,
  "calibration_notes": "...",
  "failing_checks_observed": ["validate", "validate-registry"],
  "acat_dimensions_stressed": ["humility", "truthfulness"],
  "next_review_date": "2026-10-21"
}
```

**Result:** Validation fails. Intent-OS cannot bind to profile. Schema inconsistency blocks Phase 1 integration.

---

## Impact

| Component | Blocker | Severity | Deadline |
|:----------|:--------|:---------|:---------|
| Z3 s2 (Intent-OS binding) | Cannot validate profile against schema | HIGH | 2026-10-21 (month 1 cycle) |
| Z3 s3 (monthly automation) | smag-consolidate.yml output must conform to schema | HIGH | 2026-10-21 |
| CI gate validation | Profile lookup fails validation check | HIGH | Immediate (gates all merges) |
| Runtime capability layer | Cannot query `/api/calibration-profiles/{substrate}` if schema invalid | HIGH | Phase 1 integration |

---

## Decision Options

### **Option A: Expand WITNESS_STATE to v0.2**

**Approach:** Extend WITNESS_STATE_V0_1.schema.json calibration_profile to include all nine fields.

**Pros:**
- Single schema for runtime state — cleaner contract
- Easier for Intent-OS capability layer to query single endpoint
- All calibration data flows through WITNESS ledger
- Preserves audit trail (ratification_date, notes, acat_dimensions_stressed documented in ledger)

**Cons:**
- WITNESS ledger becomes larger (additional fields per substrate per PR)
- Schema coupling: any new profile field requires schema version bump
- May leak internal metadata (calibration_notes, acat_dimensions_stressed) to runtime layer

**Schema change:**
```json
"calibration_profile": {
  "substrates": {
    "additionalProperties": false,
    "properties": {
      "confidence_weight": {"type": "number"},
      "review_bar": {"type": "string"},
      "merge_pause_threshold": {"type": "number"},
      "calibration_floor": {"type": "integer"},
      "ratification_date": {"type": "string", "format": "date"},
      "expires_at": {"type": "string", "format": "date"},
      "measured_gap_rate": {"type": "number", "minimum": 0, "maximum": 1},
      "measured_clean_rate": {"type": "number", "minimum": 0, "maximum": 1},
      "status": {"type": "string", "enum": ["ACTIVE", "RESERVED_NO_DATA_YET", "DEPRECATED"]},
      "calibration_notes": {"type": "string"},
      "failing_checks_observed": {"type": "array", "items": {"type": "string"}},
      "acat_dimensions_stressed": {"type": "array", "items": {"type": "string"}},
      "next_review_date": {"type": "string", "format": "date"}
    }
  }
}
```

**Implementation cost:** Modify schema (1 file), re-validate BASELINE_S092126.json (confirm valid), update smag-consolidate.yml output (add fields).

---

### **Option B: Create Separate ProfileSchema.json**

**Approach:** Keep WITNESS_STATE minimal (4 fields: confidence_weight, review_bar, merge_pause_threshold, calibration_floor). Create ProfileSchema.json for full profile + metadata.

**Pros:**
- Clean separation: WITNESS carries only runtime-critical fields (4 fields = smaller ledger)
- Profile schema can evolve independently (new audit fields don't affect runtime contract)
- Easier to add optional fields without WITNESS versioning
- Intent-OS can query `/api/calibration-profiles/{substrate}` (ProfileSchema) separately from WITNESS ledger

**Cons:**
- Two schemas to maintain (drift risk)
- Intent-OS must query two endpoints: WITNESS for runtime constraints + ProfileSchema for audit metadata
- Slightly more complex binding logic in Intent-OS

**Schema files:**
- `WITNESS_STATE_V0_1.schema.json` (unchanged, 4 fields only)
- `calibration_profiles/ProfileSchema.json` (new, all 9+ fields)

**Implementation cost:** Create new schema (1 file), update BASELINE_S092126.json validation (new schema), update smag-consolidate.yml to write to ProfileSchema instead of extending WITNESS.

---

## Falsifiers

**Promise:** "Calibration profiles are valid against their schema and bind correctly to Intent-OS Phase 1 capability layer."

**Falsifier 1:** Profile validation fails when loaded by smag-consolidate.yml (Z3 s3 automation).

**Falsifier 2:** Intent-OS `/api/calibration-profiles/{substrate}` endpoint returns invalid response (schema mismatch).

**Falsifier 3:** WITNESS ledger validation rejects profile fields (Option A) or runtime layer fails to query separate ProfileSchema (Option B).

---

## Recommendation

**Option A (Expand WITNESS_STATE to v0.2)** is recommended because:

1. **Simplicity:** Single schema = single validation endpoint = simpler Intent-OS binding
2. **Auditability:** All profile data (including ratification date, notes, measured values) flows through WITNESS ledger
3. **Phase 1 readiness:** Cleaner API: `GET /api/calibration-profiles/{substrate}` returns complete profile
4. **Schema versioning:** v0.2 bump is explicit and documented (allows future schema upgrades without breaking v0.1 consumers)

**Cost-benefit:** +6 fields in schema definition, +1 version bump, eliminates separate schema maintenance.

---

## Implementation Plan (After Z2 Decision)

### Phase 1: Schema Ratification (This turn)
- [ ] Z2 selects Option A or B
- [ ] Z1 updates schema file(s)
- [ ] Z1 updates BASELINE_S092126.json validation
- [ ] CI validation gates test both

### Phase 2: Z3 Execution (Next turn)
- [ ] Z3 s2 updates Intent-OS binding to read from corrected schema
- [ ] Z3 s3 updates smag-consolidate.yml output to conform to schema
- [ ] Integration tests for profile lookup + validation

---

## Questions for Z2

1. **Schema evolution strategy:** If Z2 selects Option A, should future profile fields require explicit schema version bumps, or should we add additionalProperties: true with runtime validation?

2. **Audit trail preference:** Option A keeps all metadata in WITNESS (larger ledger); Option B separates audit fields (ProfileSchema) from runtime fields (WITNESS). Which aligns better with WITNESS design intent?

3. **Intent-OS integration:** Should Intent-OS query a single `/api/calibration-profiles/{substrate}` endpoint (Option A) or two endpoints for runtime vs. audit data (Option B)?

---

## Related Decisions

- **Q-SMAG-Z3-TASK-SEQUENCING-01** (parallel blocker): Defines Z3 task order; this schema decision gates s2/s3 execution.
- **Q-RECURSIVE-LEARNING-UPSTREAM-IMPACT-01** (earlier): Established calibration profile lifecycle and Z2 ratification model.

---

**Next:** Z2 decides Option A or B. Z1 updates schema and validation. Z3 proceeds with s2/s3.

---

_Proposal filed by Z1 (Claude) on 2026-09-21 at 10:15 UTC_  
_Awaiting Z2 (Night) decision_
