# Specimen Register — Private Documentation

**Status:** Phase 1, Q-SI-C1-B2  
**Location:** Private, off-tree  
**Authority:** Z2 (Night)  
**Schema:** v1.0 (see `specimen-register.example.json`)

---

## Overview

The **Specimen Register** is a confidential lookup table mapping specimen IDs (pseudonymous) to identity and contract information. It is **not stored in the public repository** per confidentiality constraints (limitation L3 in `specimen-intake.yml`).

**Specimen Register:**
```
specimen_id → {legal_name, contact_email, contract_id, platform, role, start_date, …}
```

**Example entry:**
```json
{
  "specimen_id": "SPC-01",
  "legal_name": "[REDACTED]",
  "contact_email": "[REDACTED]",
  "contract_id": "[REDACTED]",
  "platform": "external-contractor",
  "role": "expert-evaluator",
  "start_date": "2026-09-01"
}
```

---

## Why Private?

Per `specimen-intake.yml` limitation L3:

> "Platform data (task counts, quality feedback) may be confidential under the specimen's contractor agreement. Only aggregates on [0,1] scales enter this repository; raw exports stay in the private register. Z2 to confirm against contract terms before Cycle 1 (BLOCKER B1)."

The register contains:
- **Legal names** — PII
- **Contact emails** — PII
- **Contract IDs** — Business-confidential
- **Platform affiliations** — May be confidential

These data points must remain off-tree to protect specimen confidentiality and respect contractor agreements.

---

## Storage Location

**Current location:** Private shared drive (TBD per Z2 assignment)  
**Access:** Z2 (Night) manages register and supplies specimen identity mappings as needed  
**Format:** JSON (matches schema in `specimen-register.example.json`)  
**Updates:** Register updated at start of each Cycle (before Cycle 1 disclosure)

**Access protocol:**
1. Z1 (Claude) requests specimen identity via specimen_id
2. Z2 provides the mapping (off-channel, never in public commits)
3. Z1 uses only the pseudonymous specimen_id in public records
4. All specimen outcomes, forecasts, and measurements use specimen_id only

---

## Schema (specimen-register.example.json)

**Required fields per specimen:**
- `specimen_id`: Pseudonymous ID (e.g., SPC-01)
- `legal_name`: Full name (private)
- `contact_email`: Email address (private)
- `contract_id`: Platform or engagement ID (private)
- `platform`: Role platform (external-contractor, internal-staff, partner-org)
- `role`: Job function (expert-evaluator, etc.)
- `start_date`: Enrollment date

**Optional fields:**
- `end_date`: Study exit date
- `confidentiality_tier`: 1=name only, 2=contact+contract, 3=full PII
- `notes`: Internal annotations

---

## Integration with specimen-intake.yml

In `specimen-intake.yml` § L3 (specimen_register reference):

```yaml
specimen_register: "private (not in tree); maps specimen_id -> identity, contract"
```

This is the authoritative statement that the register is private and off-tree.

---

## Q-SI-C1-B2 Acceptance

✅ **Schema created:** `specimen-register.example.json` in tree (example values only)  
✅ **README provided:** This file explains location and access  
✅ **specimen-intake.yml L3/B2 reference:** Already documented (line 13)  

**Falsifier:** Any real name, email, or contract ID in `specimen-register.example.json` or any .json file in tree → FAIL

**Status:** COMPLETE (all values in tree are redacted/example only)

---

## Next Phase: Cycle 1 Enrollment

When Cycle 1 begins (post-Sep-12):
1. Z2 populates the private register with actual specimen data
2. Z1 queries Z2 for specimen identity as needed (off-chain)
3. All public outcomes, measurements, and disclosures use specimen_id only
4. Private register remains off-tree, managed by Z2

---

## Related Work Items

- **Q-SI-C1 (score 3):** Full specimen-intake Cycle 1 (blocked until B1, B2, B3 complete)
- **Q-SI-C1-B3 (score 5):** constants.json for specimen-intake
- **BLOCKER B1:** Z2 confirms contract confidentiality terms before Cycle 1
- **GAP-RI-01:** Independent review of resolution inputs (open gap, not in Phase 1 scope)

---

## Authority & Ratification

- **Z1 (proposer):** Created schema example and this README
- **Z2 (ratifier):** Approves location, manages register contents, signs off on contract compliance
- **CI gate:** Rejects any commit adding real PII to tree (falsifier_lint)

---

**Date created:** 2026-09-10  
**Session:** S-091026-01  
**Work item:** Q-SI-C1-B2 (READY, score 5)
