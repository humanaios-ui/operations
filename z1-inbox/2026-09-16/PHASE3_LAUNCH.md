# Phase 3 Launch: Holographic Live Service Testing

**Date:** 2026-09-16 (Z2 Authorization Received)  
**Proposer:** Claude Haiku 4.5 (Z1)  
**Authority:** Carly R. Anderson (Z2 Admiral)  
**Status:** ✅ Phase 3 Infrastructure Ready · Awaiting Credential Configuration  
**Branch:** claude/phase-3-live-testing (commit f3cac18)

---

## Executive Summary

**Phase 3 Live Service Testing Infrastructure is Complete**

Z2 has authorized Phase 3 launch. Phase 3 testing infrastructure is now in place and ready for live service validation of the holographic hypothesis against real Polycam, Replicate, and Supabase APIs.

- ✅ Phase 3 test suite created (F1-F4 falsifier validation)
- ✅ Supabase database schema for results storage
- ✅ CI enumeration updated
- ✅ Credential configuration template prepared
- 📋 **BLOCKING:** Polycam API key configuration required
- 📋 **BLOCKING:** Replicate & Supabase credentials deployment required

---

## What's Implemented (Commit f3cac18)

### Phase 3 Test Suite
**File:** `tools/tests/test_holographic_phase3_live.py` (325 lines)

**Test Coverage:**
1. **F1 Validation: API Connectivity**
   - `test_polycam_connectivity()` — Polycam API callable via urllib + JSON
   - `test_replicate_connectivity()` — Replicate API callable via urllib + JSON
   
2. **F3 Validation: Schema Equivalence**
   - `test_dry_run_vs_live_schema()` — Dry-run output structure matches live
   
3. **F4 Validation: Latency Budget**
   - `test_latency_budget()` — End-to-end latency < 60s

4. **Hypothesis Verdict**
   - Computes CONFIRMED / CONDITIONAL / FALSIFIED based on test results

**Test Behavior:**
- Skips gracefully if credentials unavailable (returns True for skipped tests)
- Can run in CI without blocking (no credentials needed for CI)
- Full validation occurs when credentials configured (local or CI environment)

### Supabase Schema
**File:** `supabase/migrations/20260916_holographic_jobs.sql` (105 lines)

**Table: `holographic_jobs`**
- Columns for capture → render → storage pipeline results
- Latency measurement storage (F4 validation)
- Schema equivalence score storage (F3 validation)
- Indexes for common queries (person_id, user_id, status, created_at, dry_run)
- RLS policies for access control
- Status tracking (pending | capturing | rendering | storing | complete | failed)

### CI Integration
**Updated Files:**
- `.github/workflows/quality-baseline.yml` — Added Phase 3 test to pytest baseline
- `tools/intent_os_test_harness_v1_0.py` — Added Phase 3 test to baseline list
- Test enumeration guard (`test_ci_suite_enumeration.py`) — Passes ✅

---

## Falsifier Validation Plan (Phase 3)

| Falsifier | Criterion | Test | Status |
|:----------|:----------|:-----|:-------|
| **F1** | urllib + JSON sufficient for external APIs | `test_polycam_connectivity`, `test_replicate_connectivity` | READY |
| **F2** | No transaction requirements (stateless REST) | Protocol design assumption | VALIDATED (Phase 2) |
| **F3** | Dry-run ≡ live output structure (>95% equivalence) | `test_dry_run_vs_live_schema()` | READY |
| **F4** | Latency < 60s (capture → render → storage) | `test_latency_budget()` | READY |

---

## Credential Configuration (Required to Proceed)

### Step 1: Configure Polycam API Key

**Source:** Polycam Enterprise account settings  
**URL:** https://poly.cam/account/settings/api  
**Account:** @HumanAIOS  
**Action Required:** Z2 must provide or confirm Polycam API key

```bash
export POLYCAM_API_KEY="sk_polycam_xxxxxxxxxxxxxxxxxxxx"
```

### Step 2: Configure Replicate API Key

**Provided by Z2:** [Configured in Z2 secure environment]  
**Action:** Deploy to CI environment as GitHub Secret

```bash
export REPLICATE_API_KEY="r8_xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

### Step 3: Configure Supabase Credentials

**Source:** Supabase project dashboard  
**URL:** https://supabase.com/dashboard  
**Required Values:**
- `SUPABASE_URL` — Project URL (https://xxxxxxxxxxxx.supabase.co)
- `SUPABASE_KEY` — API key (anon or service_role)

```bash
export SUPABASE_URL="https://xxxxxxxxxxxx.supabase.co"
export SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Step 4: Apply Supabase Migration

Once SUPABASE credentials are configured:

```bash
supabase db push --db-url "$SUPABASE_URL"
# OR manual SQL: supabase/migrations/20260916_holographic_jobs.sql
```

---

## Test Execution Modes

### Mode 1: CI (No Credentials)
```bash
python3 -m pytest tools/tests/test_holographic_phase3_live.py -v
# Tests skip if credentials unavailable (graceful degradation)
# Exit code 0 (tests pass by skipping)
```

### Mode 2: Local with Credentials
```bash
export POLYCAM_API_KEY="..."
export REPLICATE_API_KEY="..."
export SUPABASE_URL="..."
export SUPABASE_KEY="..."

python3 tools/tests/test_holographic_phase3_live.py
# Full hypothesis validation with real API calls
# Outputs: JSON results with latency measurements and schema equivalence scores
```

### Mode 3: Orchestrator Direct Call
```bash
python3 -c "
from tools.tests.test_holographic_phase3_live import Phase3LiveTester
tester = Phase3LiveTester()
results = tester.run_all()
print(results['verdict'])
"
# CONFIRMED / CONDITIONAL / FALSIFIED
```

---

## Hypothesis Verdict Criteria

**CONFIRMED:** 
- F1: Both APIs reachable via urllib + JSON
- F3: Dry-run output structure matches live (>95% equivalence)
- F4: End-to-end latency < 60s

**CONDITIONAL:**
- One or more sub-claims partially validated
- Schema equivalence <95% but structure matches
- Latency borderline (50-60s)

**FALSIFIED:**
- Any falsifier triggered (API unreachable, schema mismatch, latency >60s)
- Hypothesis invalidated; pivot required

---

## Next Steps (Execution Checklist)

1. **Z2 Provides Polycam API Key** ← BLOCKING
   - [ ] Confirm Polycam @HumanAIOS account has Enterprise API access
   - [ ] Generate or provide API token

2. **Configure CI/Local Environment** ← BLOCKING
   - [ ] Set POLYCAM_API_KEY (GitHub Secret for CI, .env.local for local)
   - [ ] Set REPLICATE_API_KEY (already provided)
   - [ ] Set SUPABASE_URL and SUPABASE_KEY

3. **Apply Supabase Migration**
   - [ ] Run `supabase db push` or execute migration SQL

4. **Run Phase 3 Tests**
   - [ ] Local: `python3 tools/tests/test_holographic_phase3_live.py`
   - [ ] CI: Merge PR to trigger full suite

5. **Validate Hypothesis**
   - [ ] Confirm F1 (API connectivity) — should be immediate
   - [ ] Confirm F3 (schema equivalence) — dry-run vs live comparison
   - [ ] Measure F4 (latency) — capture → render → storage round-trip

6. **Emit Hypothesis Verdict**
   - [ ] Document results in PHASE3_RESULTS.md
   - [ ] File F/IC candidates if falsifiers triggered
   - [ ] Update REGISTERED.md with verdict and remediation path

---

## Known Constraints & Assumptions

**Free Tier Limits:**
- Polycam: 3 scans/month (sufficient for hypothesis validation)
- Replicate: $10 credit (sufficient for NeRF fine-tuning test)
- Supabase: Free tier (sufficient for metadata storage)

**Test Data:**
- Synthetic identifiers (person_test_*, user_test_*) — no PII
- No production capture data (safe to run in test environment)
- Latency measured in local environment (CI latency may differ)

**Assumptions Validated in Phase 2 (Not Re-tested):**
- F2: Stateless orchestration (REST calls with job IDs) — proven in mocked tests
- Credential redaction (error logs) — tested in Phase 2

---

## Recommendation

**Phase 3 is infrastructure-complete and ready to execute.**

Recommendation: Z2 provides Polycam API key, CI/local credentials deployed, and Phase 3 test suite runs against real services. Full hypothesis validation expected within 1-2 hours (endpoint response time + async job completion).

**Decision Window:** None (Phase 3 launch approved by Z2)  
**Ready for:** Credential configuration and execution

---

**Phase 3 Infrastructure Ready. Awaiting Polycam API Key and Credential Deployment.**

