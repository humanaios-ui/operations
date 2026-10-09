# Q-SMAG-REEXAMINATION-01: Measurement Contract & Authority Model

**Status:** Z2 Ratification Required  
**Created:** 2026-09-23  
**Decision Window:** 48 hours (per CLAUDE.md)  
**Authority:** Z2 (carly.r.anderson@gmail.com)  
**Consolidated PRs:** #471, #474, #479  

---

## Executive Summary

SMAG calibration gate implementation requires architectural decisions before code can merge. PRs #471, #474, #479 contained valid technical fixes but implemented a design using **calendar-based rolling windows as merge authority**—explicitly rejected by Q-TEMPORAL-DISSOLUTION-01 policy.

This document establishes 6 architectural decisions required to unblock implementation.

---

## Decision 1: Measurement Contract

### Current (Rejected)
```python
gap_rate = failed_rows / total_rows (last 30 days)
if gap_rate > merge_pause_threshold:
    block_merge()
```

### Issues
- Calendar time (30 days) is not a valid internal merge authority predicate
- Q-TEMPORAL-DISSOLUTION-01 forbids elapsed-time-based control semantics
- Temporal dissolution gate scanner passes (no new keywords added) but **lexical pass ≠ architectural validity**
- Passing temporal scan only proves no prohibited token was added; does not establish rolling-window semantics are admissible

### Required Decision: Z2 Chooses One

**Option A: State/Evidence Predicate**  
Replace gap_rate with a state measurement (e.g., "ledger contains N recent passing audits" or "system has transitioned to safe state").  
*Advantage:* Timebound by evidence, not calendar  
*Risk:* May require new telemetry/ledger schema

**Option B: Artifact Count**  
Base merge authority on counts (e.g., "at least 10 ratified PRs in queue" or "evidence artifact count > K").  
*Advantage:* Observable, not time-dependent  
*Risk:* May be gamed by batch submission

**Option C: Audit Trail Replay**  
Use NF_LEDGER immutable audit trail; compute derived metric (confidence, safety score) from ledger events, not calendar window.  
*Advantage:* Cryptographically anchored  
*Risk:* Requires event semantics stable contract

**Option D: Defer to Molt Cycle**  
Move merge authority entirely to molt cycle; SMAG gate becomes observational only (no blocking).  
*Advantage:* Separates measurement from authority  
*Risk:* Requires molt infrastructure mature

---

## Decision 2: Z2 Ratification Validation

### Current (Insufficient)
```python
def is_profile_ratified(profile: dict) -> bool:
    ratified_by = profile.get("ratified_by_z2", "")
    if not ratified_by or ratified_by.startswith("TBD_"):
        return False
    return True
```

**Problem:** Accepts any non-TBD string; test uses `"sha256_hash_value"` as "signature"

### Issues
- No cryptographic validation of Z2 signature
- Changing fields in the profile can make unratified profile appear safe
- No anchor to authoritative Z2 record
- Blocks merge authority on an unchecked boolean

### Required Decision: Z2 Chooses Validation Method

**Option A: Hash Chain**  
Ratification fields contain HMAC or SHA256 hash; CI validates against Z2 ledger entry.  
*Advantage:* Tamper-evident  
*Risk:* Requires Z2 ledger infrastructure

**Option B: INTENT-OS Capability**  
Query INTENT-OS `/api/z2-authorized-machine-identities` or `/api/ratified-profiles/{id}` at runtime.  
*Advantage:* Live, always current  
*Risk:* CI depends on external service

**Option C: Git Signed Commit**  
Profile changes must be committed with Z2's git signature; CI verifies GPG signature.  
*Advantage:* Leverages existing git infrastructure  
*Risk:* Requires Z2 key management

**Option D: No Blocking Validation (Phase 1)**  
Profile-stored fields are advisory only; blocking authority requires separate Z2 approval mechanism (merge-gate CODEOWNERS).  
*Advantage:* Simplest; works for Phase 1  
*Risk:* Blocks are not self-documenting in profile

---

## Decision 3: Workflow Surface (Which File?)

### Current Conflict
- **Implemented:** `.github/workflows/quality-baseline.yml` (PR #471, #474, #479)
- **Profile's Checklist:** `merge-gate.yml` (per BASELINE_S092126.json implementation_checklist)

### Issues
- Merge control ≠ quality checks; should not be in quality-baseline
- Profile's own spec lists merge-gate.yml as the target
- Merge-gate doesn't exist yet (Phase 1 infrastructure gap)

### Required Decision: Z2 Chooses Scope

**Option A: Move to merge-gate.yml (Future)**  
- Phase 1: Advisory in quality-baseline.yml only
- Phase 2: Move to merge-gate.yml once merge-gate infrastructure exists
- *Timeline:* Requires merge-gate.yml creation as separate Phase 2 work

**Option B: Quality-Baseline as Phase 1 (Temporary)**  
- Phase 1: Implement as non-blocking quality gate (advisory warnings only)
- Phase 2: Move blocking logic to merge-gate.yml
- *Risk:* Mixed purpose (quality + control); confusing to operators

**Option C: Create merge-gate.yml Now**  
- Create merge-gate.yml in Phase 1; wire SMAG gate there immediately
- *Advantage:* Aligns with profile spec from day 1
- *Risk:* New CI infrastructure; coordination with merge-gate owners needed

---

## Decision 4: Authority Model (Advisory vs. Blocking)

### Current State
- **Profile Status:** Unratified (ratified_by_z2 = "TBD_AWAITING_Z2_DECISION")
- **Workflow Behavior:** Blocks merges if gap_rate exceeds threshold
- **Conflict:** Blocking authority before Z2 ratification violates governance

### Issues
- Profile not ratified; blocking on unratified profile is premature
- review_bar marked advisory but workflow claims enforcement
- Phase 1 spec says "advisory"; Phase 2 says "blocking"

### Required Decision: Z2 Chooses Phasing

**Option A: Phase 1 = Advisory Only**
- Do not block merges; emit warnings and metrics only
- Unblock Phase 2 once profile is ratified and infrastructure mature
- *Advantage:* Safe; no accidental merge blocks during development
- *Risk:* Gate is inert; low signal on actual impact

**Option B: Phase 1 = Blocking with Escape Hatch**
- Block by default, but CI allows override with Z2 comment approval
- Profile remains unratified; blocking is "experimental"
- *Advantage:* Tests real impact; allows Z2 to intervene case-by-case
- *Risk:* Requires Z2 on-call for each override

**Option C: Phase 1 = Blocking (Ratified Profile Required)**
- Block only after profile is ratified and signed
- Delay Phase 1 implementation until ratification complete
- *Advantage:* Authority-sound from day 1
- *Risk:* Delays Phase 1 delivery

---

## Decision 5: Data Integrity Constraints

### Issues Identified

**Issue A: Malformed JSON Silently Ignored**
```python
try:
    row = json.loads(line)
except json.JSONDecodeError:
    continue  # ← Bad record disappears from denominator
```
Corrupt failing records can vanish; unverifiable ledger appears safe.

**Issue B: Missing `failing_checks` Field**
```python
failing_checks = row.get("failing_checks", [])  # ← Defaults to empty
if failing_checks and len(failing_checks) > 0:
    failed_rows += 1
```
Records without `failing_checks` counted as passing; dilutes measured failure rate.

**Issue C: Missing Ledger Returns 0.0**
```python
if not Path(ledger_path).exists():
    return 0.0  # ← Opens gate (fails open)
```
Configured measurement source absent → gate permits merges without evidence.

### Required Decision: Z2 Chooses Validation Strategy

**Option A: Fail-Closed on Invalid Content**
- Malformed JSON → exit 2 (block merge, error)
- Missing `failing_checks` → exclude row with justification or block
- Missing ledger → exit 2 (block merge)
- *Advantage:* No false negatives; errors surface immediately
- *Risk:* Ledger errors can cause unintended merge blocks

**Option B: Partial Evidence with Justification**
- Malformed JSON → skip with log message; tag measurement as "partial"
- Missing `failing_checks` → exclude row; report count of excluded rows
- Missing ledger → report "measurement unavailable" without blocking
- *Advantage:* Measurement continues despite errors; visibility of caveats
- *Risk:* Requires formal "partial evidence" state definition

**Option C: Strict Ledger Schema Enforcement**
- Define explicit ledger schema contract (JSON schema file)
- CI validates schema on merge (separate gate)
- Gate only accepts conformant records; malformed are schema violations (separate from SMAG)
- *Advantage:* Schema enforcement is orthogonal; SMAG assumes valid data
- *Risk:* Requires separate schema validation gate infrastructure

---

## Decision 6: review_bar Enforcement Gap

### Current
```python
def enforce_review_bar(substrate_profile: dict) -> bool:
    review_bar = substrate_profile.get("review_bar", "standard")
    print(f"📋 Review bar requirement: {review_bar}")
    print(f"   (Phase 1: advisory; full enforcement requires ACAT metadata)")
    return True  # ← Always returns True
```

**Workflow claim:** "review_bar enforced"  
**Reality:** Always passes; ACAT review metadata not in CI

### Issues
- Workflow claims enforcement; code does not enforce
- ACAT review metadata not available in Phase 1
- review_bar gate cannot be implemented without ACAT integration

### Required Decision: Z2 Chooses Deferral

**Option A: Remove Enforcement Claim**
- Delete `enforce_review_bar()` function
- Document in PR that review_bar enforcement deferred to Phase 2
- *Advantage:* Honest about what Phase 1 does
- *Risk:* Gap between claimed and actual enforcement

**Option B: Defer to Separate ACAT Gate**
- SMAG gate ignores review_bar in Phase 1
- Create separate ACAT review metadata gate (Phase 2)
- *Advantage:* Separates concerns; cleaner architecture
- *Risk:* Requires new gate infrastructure

**Option C: Phase 1 Stub (Warn on Mismatch)**
- Check if review_bar is "standard" (default); warn if changed
- Real enforcement deferred to Phase 2
- *Advantage:* Alerts if review_bar is misconfigured
- *Risk:* False sense of enforcement

---

## Preserved Technical Contributions

All from consolidated PRs #471, #474, #479. Ready to port once architecture decided:

### 1. Fail-Closed Ledger I/O (Security Fix)
```python
except IOError as e:
    print(f"❌ Error reading ledger: {e}")
    sys.exit(2)  # ← Fail-closed instead of return 0.0
```
**Impact:** Ledger read errors block merges instead of opening gate

### 2. Z2 Ratification Status Check (Governance)
```python
if not is_profile_ratified(profile):
    print(f"⚠️  Profile awaiting Z2 ratification (Phase 1: advisory)")
```
**Impact:** Visible warning when profile unratified; Phase 1 advisory, Phase 2 blocking

### 3. Parameter Naming (Temporal Policy Compliance)
Changed `--window-days` → `--lookback-periods` to avoid temporal-dissolution-gate patterns

### 4. Manifest Synchronization
- Regenerated TOOLS_MANIFEST.md from tools-manifest.yaml
- Assigned categories to 2 newly discovered scripts
- Resolved manifest sync issues

### 5. Test Coverage
- 15 regression tests for gap_rate computation, profile loading, ratification
- All passing locally

---

## Timeline & Next Steps

### Phase 1: Z2 Decision (Now)
1. Z2 reviews 6 architectural questions
2. Z2 chooses Option A/B/C/D for each decision
3. Z2 signs RATIFICATION event (per CLAUDE.md)
4. **Decision window:** 48 hours

### Phase 2: Implementation (After Ratification)
1. Create implementation PR with chosen architecture
2. Port preserved technical fixes from #471/#474/#479
3. Implement ratified measurement contract
4. Wire Z2 ratification validation (chosen method)
5. Create merge-gate.yml if Option A or C (Decision 3)
6. Implement data integrity constraints (chosen strategy)

### Phase 3: Review & Merge
1. Copilot review of implementation
2. Z2 final sign-off
3. CI gate pass
4. Merge to main

---

## Questions for Z2

Please respond with decisions for each question:

1. **Measurement Contract:** A / B / C / D (or custom proposal)?
2. **Z2 Ratification Validation:** A / B / C / D?
3. **Workflow Surface:** A / B / C?
4. **Authority Model:** A / B / C?
5. **Data Integrity:** A / B / C?
6. **review_bar Enforcement:** A / B / C?

Optionally: Any modifications to proposed options, or alternative approaches?

---

## Ratification Record

**Awaiting Z2 Signature**

Once Z2 decides, this section will be updated:
```
Ratified by: carly.r.anderson@gmail.com
Ratified at: <timestamp>
Decisions: <D1: A, D2: B, D3: C, D4: A, D5: B, D6: C>
Ratification Hash: sha256(decisions | by=Night | at=timestamp)
```

---

## References

- **CLAUDE.md:** Z2 authority, decision routing, governance model
- **Q-TEMPORAL-DISSOLUTION-01:** Policy forbidding calendar-based internal deadlines
- **Q-RECURSIVE-LEARNING-UPSTREAM-IMPACT-01:** Parent framework for SMAG work
- **Consolidated PRs:** #471, #474, #479 (evidence preserved for implementation)
- **Profile:** `calibration_profiles/BASELINE_S092126.json` (unratified; s1 blocked on Z2 sign-off)
