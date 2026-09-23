# Z2 Ratification: SMAG Calibration & Sequencing Blockers

**Date:** 2026-09-21  
**Ratifier:** Night (Z2 Serial Gate)  
**Authority:** Z2 ratifies both IC candidates for Z3 executor pathway sequencing toward 2026-10-21 first monthly calibration cycle

---

## Decision 1: Q-SMAG-CALIBRATION-SCHEMA-CONFORMANCE-01

**Candidate:** Q-SMAG-CALIBRATION-SCHEMA-CONFORMANCE-01  
**Decision:** **ACCEPT** → Proceed with **Option A** (expand WITNESS_STATE to v0.2)

### Rationale
- Single schema simplifies Intent-OS capability binding (one endpoint vs. two)
- Audit trail preservation (all metadata in WITNESS ledger)
- Phase 1 readiness for cleaner API: `GET /api/calibration-profiles/{substrate}`
- 7 new fields to schema definition is manageable

### Implementation Directive (Z1 + Z3 s2/s3 owners)
1. Z1 updates `WITNESS_STATE_V0_1.schema.json` → v0.2 with 7 additional fields:
   - measured_gap_rate, measured_clean_rate, status, calibration_notes
   - failing_checks_observed, acat_dimensions_stressed, next_review_date

2. Z3 s2 owner registers BASELINE_S092126.json via Intent-OS capability manifest  
   - Profile queryable at `/api/calibration-profiles/{substrate}` endpoint  
   - Machine identity `noreply@anthropic.com` authorized via INTENT-OS capability  
   - Profile expires_at enforced (reverts to defaults post-expiry)

3. Z3 s3 owner updates smag-consolidate.yml profile generator  
   - Output conforms to WITNESS_STATE v0.2 schema  
   - CI validation gates profile schema conformance  

---

## Decision 2: Q-SMAG-Z3-TASK-SEQUENCING-01

**Candidate:** Q-SMAG-Z3-TASK-SEQUENCING-01  
**Decision:** **ACCEPT** → Proceed with proposed **Phase 1 → Phase 2 sequencing**

### Confirmed Task Order & Critical Finding
- **s1 (CI gate wire-up):** INDEPENDENT of schema choice — starts immediately after Z2 ratification
- **s2 (Intent-OS binding) & s3 (Monthly automation):** Run parallel, AFTER schema decision ratified

### Critical Dependency Clarification
s1 requires only the 4 core runtime fields already in WITNESS_STATE_V0_1:
- confidence_weight, review_bar, merge_pause_threshold, calibration_floor

Schema expansion (Option A) does NOT block s1 implementation. s1 begins now; s2/s3 begin after schema fields are confirmed.

### Implementation Directive

**Phase 1: s1 Execution (immediately, 2026-09-21–2026-09-25)**
- Z3 s1 owner assigned: TBD (CI/CD specialist)
- Task: Add profile lookup to `.github/workflows/quality-baseline.yml` (or new merge-gate.yml)
- Acceptance criteria:
  - Gate queries BASELINE_S092126.json from HEAD
  - Extracts review_bar + merge_pause_threshold for human:humanaios-ui
  - Enforces review_bar before merge approval
  - Computes gap_rate from NF_LEDGER.jsonl (30-day rolling window: failed_checks / total_checks)
  - Auto-pauses merges if gap_rate > merge_pause_threshold
- Deliverable: PR with quality-baseline.yml changes + test results (3 test PRs)
- Go/No-Go Gate: 2026-09-25 (Gap rate computation verified; CI passes)

**Phase 2: s2/s3 Parallel (2026-09-25–2026-10-20, after s1 Go gate)**
- Z3 s2 owner assigned: TBD (Intent-OS integration specialist)
- Z3 s3 owner assigned: TBD (or Z1 builds generator; Z3 runs automation)
- s2 task: Register BASELINE_S092126.json in Intent-OS manifest
  - Endpoint queryable at `/api/calibration-profiles/{substrate}`
  - Capability signature validation for `noreply@anthropic.com`
  - Schema validation confirms v0.2 conformance
  - Deliverable: PR with Intent-OS manifest + test results
  - Go/No-Go Gate: 2026-09-28 (Endpoint responds with valid profile; CI schema validation passes)

- s3 task: Wire monthly automation to `.github/workflows/smag-consolidate.yml`
  - Change schedule from weekly Monday → monthly on 21st (cron: `0 0 21 * *`)
  - First trigger: 2026-10-21 00:00 UTC
  - Workflow calls tools/calibration_profile_generator.py (builds new profile if gap_rate changed)
  - Generator opens PR to REGISTERED.md with Z2-ratification-signature requirement (only if profile changed)
  - Deliverable: PR with smag-consolidate.yml + generator.py + test results
  - Go/No-Go Gate: 2026-09-28 (Profile generation succeeds; PR opener test passes; CI schema validation passes)

**Phase 3: Integration & First Monthly Cycle (2026-10-21)**
- All three PRs (s1, s2, s3) merged to main by 2026-10-20
- smag-consolidate.yml fires at 2026-10-21 00:00 UTC
- Gap analysis runs on 30-day window (2026-09-21 → 2026-10-21)
- Profile generator produces updated profile (or confirms renewal)
- Z2 ratifies updated profile
- Z3 s1 gate enforces updated profile in merge gate
- Z3 s2 Intent-OS binding queries updated profile
- Monthly cycle repeats: 2026-11-21, 2026-12-21, ...

### Z3 Executor Assignment Required
Per ZONE_REGISTRY.md, Z2 must assign:
- **s1 owner** (CI/CD specialist): Can start immediately
- **s2 owner** (Intent-OS integration specialist): Starts after schema decision
- **s3 automation owner** (Python + workflow): Starts after schema decision

---

## Falsifiers

Both IC candidates remain under falsifier discipline:

**Q-SMAG-CALIBRATION-SCHEMA-CONFORMANCE-01:**
- Falsifier 1: Profile validation fails when loaded by smag-consolidate.yml
- Falsifier 2: Intent-OS endpoint returns invalid response (schema mismatch)
- Falsifier 3: WITNESS v0.2 schema rejected by runtime layer (Option A)

**Q-SMAG-Z3-TASK-SEQUENCING-01:**
- Falsifier 1: Any s1/s2/s3 task incomplete or blocked at 2026-10-20 23:59 UTC
- Falsifier 2: smag-consolidate.yml fails to run on 2026-10-21
- Falsifier 3: Generated profile fails schema validation in CI
- Falsifier 4: Intent-OS endpoint unavailable at 2026-10-21

---

## Z2 Hash

This ratification is recorded here pending signature by Z2 (Night) with format:
```
sha256(Z2_RATIFY_SMAG_BLOCKERS.md | by=Night | at=2026-09-21T17:03:00Z | candidates=[Q-SMAG-CALIBRATION-SCHEMA-CONFORMANCE-01, Q-SMAG-Z3-TASK-SEQUENCING-01] | decisions=[Option A, sequencing confirmed])
```

---

**Next:** Z3 executors assigned and begin Phase 1 (s1 implementation). Z1 prepares schema files for v0.2 update.

_Recorded by Z1 (Claude) on 2026-09-21 at 17:03 UTC_  
_Ratification by Z2 (Night) pending signature_
