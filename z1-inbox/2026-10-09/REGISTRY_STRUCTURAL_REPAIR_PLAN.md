# Proposal: Governance Registry Structural Repair

**Document ID:** Q-REGISTRY-STRUCTURAL-REPAIR-PLAN-01  
**Date:** 2026-10-09  
**Author:** Z1 (Claude)  
**Status:** Awaiting Z2 Ratification  
**Target:** REGISTERED.md structural integrity restoration  
**Scope:** Repair 162 entries with 127 defects across 6 failure modes

---

## Executive Summary

REGISTERED.md v1.0 (the governance registry) contains 162 entries with 127 structural defects affecting validation (RFM-06/09/10/15/17), blocking new PR admissions and preventing system_graph.json updates (PR #734). Repair requires Z2 governance decision on scope and strategy before execution.

**Key metrics:**
- **Entries affected:** 162/162 (100% of registry)
- **Defects:** 127 / 648 opportunities = 80.4% first-pass yield (~2.4 sigma)
- **Failing checks:** RFM-06, RFM-09, RFM-10, RFM-15, RFM-17
- **Repair effort:** 3-5 days (comprehensive) or 1-2 days (minimal; unblock only)

---

## Problem Statement

### Current State
The `registered_failure_mode_scan_v0_1.py` validator identifies 6 major structural issues:

| RFM | Issue | Count | Severity | Blockage |
|-----|-------|-------|----------|----------|
| **RFM-17** | Header staleness (Last updated date) | 1 | HIGH | ✅ Can fix now |
| **RFM-10** | Post-terminal append (entries after `## Changelog`) | 51 | HIGH | ❌ Requires reorganization |
| **RFM-06** | Missing required YAML fields | 70+ | MEDIUM | ❌ Requires audit + fill |
| **RFM-09** | Append-ordering decay (entries not in section order) | 46 | MEDIUM | ❌ Requires reordering |
| **RFM-15** | Malformed ratification hashes (git SHAs vs. sha256) | 8 | MEDIUM | ❌ Requires Z2 decision |
| **RFM-07/08/11/16** | Secondary schema issues | Various | LOW | ⚠️ May resolve with above |

### Impact

1. **Merge blockade:** CI `validate` gate fails on all PRs (gate validates ENTIRE file, not just changes)
2. **Admission gate:** Repository admission/backpressure gate cannot admit new work while registry invalid
3. **Governance stall:** Q-SYSTEM-GRAPH-TEMPORAL-01 (system_graph.json update proposal) blocked at PR #734
4. **Governance debt:** 145+ existing entries with incomplete metadata

### Root Cause

REGISTERED.md was designed as append-only but lacks:
- Automated enforcement of section ordering (entries creep into wrong sections)
- Validation of required fields before commit
- CI gate to prevent post-changelog appends
- Retroactive audit of pre-2026-05-08 entries (before schema v1.0)

---

## Proposed Solution: Tiered Repair Strategy

### Option A: Minimal (Unblock PR #734 only)
**Effort:** 1-2 days  
**Risk:** Low (targeted fixes only)  
**Scope:** Fix only RFM-17 + ensure no NEW errors from Q-SYSTEM-GRAPH-TEMPORAL-01

1. Update header "Last updated" timestamp (RFM-17) ✅ **DONE**
2. Verify Q-SYSTEM-GRAPH-TEMPORAL-01 entry meets schema requirements
3. Mark file as "structural repair pending" in header
4. File Q-REGISTRY-STRUCTURAL-REPAIR-PLAN-01 governance proposal
5. Merge minimal fix PR; Z2 approves comprehensive repair separately

**Outcome:** PR #734 passes CI; registry repair becomes explicit governance item

---

### Option B: Moderate (Fix post-changelog entries)
**Effort:** 2-3 days  
**Risk:** Moderate (large reorganization)  
**Scope:** Fix RFM-10 (51 entries) + RFM-17 + secondary schema issues

1. Move all 51 post-changelog entries into proper F/H/IC sections
2. Sort entries by ID within sections (RFM-09)
3. Add stub metadata to highest-priority missing-field entries (RFM-06 subset)
4. Regenerate REGISTERED_FAILURE_MODES.md with new baselines
5. Update ratification hashes where possible (RFM-15 subset)

**Outcome:** Registry reaches ~85% pass rate; remaining issues documented for Phase 2

---

### Option C: Comprehensive (Full restoration)
**Effort:** 5-7 days  
**Risk:** High (large-scale audit + restructuring)  
**Scope:** Fix all 6 failure modes + audit all 162 entries

1. **RFM-17:** Update header (1 hour)
2. **RFM-10:** Move 51 post-changelog entries (4 hours)
3. **RFM-09:** Reorder entries by ID (2 hours)
4. **RFM-06:** Fill missing required fields across 70+ entries (8 hours)
   - Audit substrate field (provider/model)
   - Audit tags field (domain labels)
   - Audit superseded_by field (succession pointers)
5. **RFM-15:** Correct 8 malformed ratification hashes (4 hours)
6. **Regenerate REGISTERED_FAILURE_MODES.md** with correct baselines (1 hour)
7. **CI validation pass** + create companion governance audit

**Outcome:** Registry reaches 95%+ pass rate; Z2 sign-off on all corrections

---

## Recommendation: Option B + Governance Escalation

**Immediate action (today):** Merge **Option A** (minimal fix) to unblock PR #734 and repository admission.

**Governance escalation:** File Q-REGISTRY-STRUCTURAL-REPAIR-PLAN-01 (this document) for Z2 decision on whether to proceed with Option B or Option C.

**Rationale:**
- Unblocks critical work (system_graph.json update, new PR admissions)
- Allows Z2 to scope comprehensive repair separately
- Reduces risk of accidental data loss during large reorganization
- Keeps governance explicit (Z2 approves each phase)

---

## Implementation Details

### Phase 1: Minimal (Option A) — Status: READY
- ✅ Update header "Last updated" → October 9, 2026
- ⏳ Verify Q-SYSTEM-GRAPH-TEMPORAL-01 schema compliance
- ⏳ Commit to `maintenance/repair-registered-registry-2026-10-09`
- ⏳ Create PR for Z2 review

### Phase 2: Governance Decision (Option B or C)
- Requires Z2 ratification of repair scope
- Z2 decides: Moderate (B) or Comprehensive (C)?
- If approved: separate PR for Phase 2 implementation

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Accidental data loss during reorganization | Medium | HIGH | Use git history for recovery; test reorganization locally first |
| Ratification hash correction errors | Low | MEDIUM | Only Z2-signed hashes; human review for each correction |
| Schema drift regression | Low | LOW | CI gate validation after each phase |
| New entries still misplaced (RFM-10 recurses) | Medium | LOW | Add CI gate to prevent post-changelog appends (companion task) |

---

## Success Criteria

- ✅ PR #734 (system_graph.json update) passes `validate` gate
- ✅ New PRs can be admitted (repository admission gate passes)
- ✅ REGISTERED_FAILURE_MODES.md baseline numbers match current scan results
- ✅ All 162 entries carry required YAML fields (or explicitly marked as legacy exception)
- ✅ Post-changelog entries reorganized into proper sections
- ✅ CI `validate` gate reaches ≥90% first-pass yield (sub-200k DPMO)

---

## Timeline

| Phase | Owner | Duration | Gate |
|-------|-------|----------|------|
| A: Minimal fix | Z1 | 2 hours | CI pass |
| A: PR review | Z2 | 48h | Z2 RATIFY |
| B/C: Governance decision | Z2 | 24h | Choose B or C |
| B: Moderate repair (if approved) | Z1 | 2-3 days | CI pass + Z2 sign-off |
| C: Comprehensive repair (if approved) | Z1 | 5-7 days | CI pass + Z2 audit |
| **Total (A + B)** | | **~4 days** | Z2 final |
| **Total (A + C)** | | **~7 days** | Z2 final |

---

## Falsifier

This proposal fails (and Z2 should REJECT) if:

1. **Schema discovery error:** Repair discovers new undocumented entry fields that contradict published schema (REGISTRY_SPEC.md)
2. **Ratification collision:** Correcting ratification hashes reveals two distinct governance decisions assigned the same entry
3. **Tool incompatibility:** Regenerated REGISTERED_FAILURE_MODES.md causes other CI gates to fail
4. **Data recovery failure:** Post-repair, ≤2 entries become unrecoverable (git history loss)

**Falsifier is satisfied if:**
- Option A (minimal) merges cleanly
- Z2 chooses B or C and approves scope
- Phase 2 (B or C) reaches ≥90% CI pass rate
- All ratification hashes either corrected or explicitly documented as Z2-decided exceptions

---

## Next Step

Z2 (Night) review of this proposal. Decision:
- **ACCEPT Option A only** → Merge minimal PR; defer comprehensive repair
- **ACCEPT Option A + B** → Merge minimal PR; approve moderate repair scope
- **ACCEPT Option A + C** → Merge minimal PR; approve comprehensive repair scope
- **REJECT** → Propose alternative approach

---

**Proposal ID:** Q-REGISTRY-STRUCTURAL-REPAIR-PLAN-01  
**Filed:** 2026-10-09 by Z1 (Claude)  
**Awaiting:** Z2 (Night) ratification
