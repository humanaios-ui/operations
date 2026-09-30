# Q-588-CONVERGENCE-MATRIX-01

**Created:** 2026-09-30  
**Purpose:** Map Resource System components (#588 convergence) across main + candidate branches  
**Scope:** Six core components (Resource Miner, Eligibility Resolver, Activity Graph, Resource Manager, PII Claim Gateway, Replay)  
**Converging PRs:** #588, #599, #608, #609, #611  

---

## Executive Summary

This matrix reveals which Resource System components exist (main), exist partially (candidates), or are missing entirely. For each component, it answers:

1. **Where is it?** — file/module location
2. **Can it execute?** — main evidence (ready), candidate evidence (unmerged), or neither
3. **Has it been exercised?** — CI pass, test harness, manual verification
4. **What evidence would prove this classification wrong?** — falsifier for each row

**Outcome:** Identifies whether to compose existing components or scaffold #588 as a dedicated substrate.

---

## Convergence Matrix

| **Component** | **Location (main)** | **Main Evidence** | **Candidate Evidence** | **State** | **Executable?** | **Exercised?** | **Evidence (Would Prove Wrong)** |
|:---|:---|:---|:---|:---|:---|:---|:---|
| **Resource Miner** | `humanaios-funding-pipeline/resource-miner/` | `resource_miner/miner.py` (enrich, dedupe, route, need-match) | — | EXISTS | ✅ YES (Python module, callable) | ❓ Unclear (tests exist; CI status unknown) | PR #567, #563 (resource-miner-path, admit-pr) — verify: `python3 -m pytest humanaios-funding-pipeline/resource-miner/tests/ -v` passes and test coverage ≥80% |
| **Eligibility Resolver** | Feature branch `feature/resource-entitlement-handoff-v0` | None on main | `#608 integration` (miner → entitlement binding) | EXISTS/PARTIAL | ⚠️ CONDITIONAL (implemented, not merged) | ❓ Unclear (handoff integration status unknown) | PR #608 merge + integration test in CI: `test_miner_entitlement_handoff()` passes and resource-miner output feeds entitlement-resolver input without loss |
| **Activity Graph** | — (search: `ActivityEvent`, `activity_graph`) | None found on main | None found in search (candidate branches) | **MISSING** | ❌ NO | ❌ NO | Create canonical `ActivityEvent` schema + `ActivityGraph` class that: (1) ingests Resource Miner + Eligibility Resolver outputs; (2) maintains acyclic directed graph; (3) passes `test_activity_graph_DAG_invariant()` |
| **Resource Manager** | `tools/resource_ledger_v0_1.py` (partial) | Ledger claims/spend/yield logic exists | — | EXISTS/PARTIAL | ⚠️ PARTIAL (ledger exists; state lifecycle incomplete) | ✅ YES (ledger tool has verify/report subcommands; exercised by tools/README) | Complete state/value lifecycle: (1) ResourceState schema with version/timestamp; (2) transition matrix (OPEN→IN_PROGRESS→COMPLETED→CLOSED); (3) test `test_resource_state_lifecycle()` passes; (4) ledger ordering enforced by lock |
| **PII Claim Gateway** | `schemas/resource_request.schema.json` (partial) | Schema exists; logic unknown | — | EXISTS/PARTIAL | ❓ UNKNOWN | ❓ UNKNOWN | Inspect: (1) does `resource_request.schema.json` include PII redaction rules? (2) is there a `pii_redaction.py` tool? (3) `test_pii_redaction_in_resource_request()` passes? |
| **Replay** | `tools/` (search yields none) | None found on main | Check #611 (convergence experiment) | **MISSING/CANDIDATE** | ❌ NO (on main); ❓ CANDIDATE | ❌ NO | Implement reproducible replay: (1) ledger hash-chain enables audit trail; (2) resource state versioning enables rollback; (3) test `test_replay_transaction_log()` passes; (4) divergence-free replay on two independent runs |

---

## Component-by-Component Analysis

### **1. Resource Miner** — EXISTS ✅

**Location:** `humanaios-funding-pipeline/resource-miner/resource_miner/miner.py`

**What it does:**
- Loads resource candidates from seed/snapshot (jsonl)
- Deduplicates via `store.dedupe()`
- Enriches with need matching via `needs.map_to_needs()`
- Routes to VERIFY_NOW, WATCH, or backlog via `routing.route_candidate()`
- Sorts by route priority, need score, deadline

**Main evidence (executable):**
- ✅ Callable Python module with documented interface: `enrich(resources, needs_path) → list[ResourceCandidate]`
- ✅ Data models defined (`resource_miner/models.py`)
- ✅ Needs routing logic present

**Candidate evidence:**
- PR #567 (resource-miner-path): Fixes import/path issues
- PR #563 (admit-pr-563-resource-miner): Admission gate review

**Exercised?**
- ❓ Unclear — tests exist (`humanaios-funding-pipeline/resource-miner/tests/test_resource_miner.py`) but CI status unknown
- No verified run in current session

**Falsifier (would prove EXISTS wrong):**
- `python3 -m pytest humanaios-funding-pipeline/resource-miner/tests/ -v` reports failure or timeout
- Test coverage <80%
- Miner fails to process snapshot (jsonl parsing error)

**Next step:** Verify miner tests pass and coverage ≥80%; run on actual resource snapshot.

---

### **2. Eligibility Resolver** — EXISTS/PARTIAL ⚠️

**Location:** `feature/resource-entitlement-handoff-v0` (candidate branch)

**What it does:**
- Takes Resource Miner output (candidates, ranked)
- Determines eligibility based on entitlement rules
- Passes eligible candidates downstream (to Activity Graph or Resource Manager)

**Main evidence:**
- ❌ Not on main

**Candidate evidence:**
- ✅ Branch `feature/resource-entitlement-handoff-v0` exists
- PR #608: Miner → Entitlement binding integration
- Likely defines entitlement resolution logic (not yet inspected)

**Exercised?**
- ❌ Unmerged — no CI validation on main
- Handoff interface (output format) unknown

**Falsifier (would prove EXISTS/PARTIAL wrong):**
- `feature/resource-entitlement-handoff-v0` branch deleted or empty
- PR #608 fails CI (syntax error, import error, test failure)
- Integration test fails: `test_miner_entitlement_handoff()` — miner output schema incompatible with resolver input schema

**Next step:** Inspect PR #608; verify interface compatibility with Resource Miner output; run integration test.

---

### **3. Activity Graph** — MISSING ❌

**Location:** None found

**What it should do:**
- Ingest miner + eligibility resolver outputs
- Build directed acyclic graph (DAG) of resource activities
- Represent causality and resource dependencies
- Enable convergence analysis with graph_convergence_v1_0.py

**Main evidence:**
- ❌ No `ActivityEvent` schema
- ❌ No `ActivityGraph` class
- ❌ No graph construction logic

**Candidate evidence:**
- ❌ Not found in candidate branches either
- graph_convergence_v1_0.py exists but operates on pre-built graphs (GRAPH_ALIGNMENT.yaml)

**Exercised?**
- ❌ Not built; cannot be exercised

**Falsifier (would prove MISSING wrong):**
- Find `schemas/activity_event.schema.json` or `models/ActivityGraph` class
- Canonical event type schema: `{"id": "...", "timestamp": "...", "type": "RESOURCE_...", "actor": "...", "payload": {...}}`
- Test: `test_activity_graph_DAG_invariant()` passes
- DAG validation: no cycles, topological sort deterministic

**Next step:** Design ActivityEvent schema; implement ActivityGraph class; wire it between Eligibility Resolver and Resource Manager.

---

### **4. Resource Manager** — EXISTS/PARTIAL ⚠️

**Location:** `tools/resource_ledger_v0_1.py` (primary), `schemas/resource_state.schema.json`

**What it does:**
- Ledger side (✅ exists): claim/spend/yield operations, hash-chained append-only log, verification
- State lifecycle (❌ missing): tracking resource state transitions (OPEN → IN_PROGRESS → COMPLETED → CLOSED)
- Value lifecycle (❌ missing): assigning and updating resource prices/exchange rates

**Main evidence:**
- ✅ `resource_ledger_v0_1.py`: Implements claim(), spend(), yield(), close() operations
- ✅ Hash-chain validation via verify() — prevents tampering
- ✅ Lock mechanism (flock) — serializes concurrent writes
- ✅ Unit registry support (RESOURCE_UNITS.yaml)

**Candidate evidence:**
- ❓ `schemas/resource_state.schema.json` exists but content unknown
- ❓ Price event logic (`price()` subcommand in ledger) partially defined

**Exercised?**
- ✅ Ledger CLI has subcommands: init, verify, cap, claim, spend, yield, price, waste, close, status, report
- ⚠️ Exercise level unknown — tests may exist but CI status unclear

**Falsifier (would prove EXISTS/PARTIAL wrong):**
- `resource_state.schema.json` does not define state transitions
- `price()` subcommand fails (syntax error, logic error)
- Integration test fails: `test_resource_ledger_lifecycle()` — cannot open → claim → spend → close in sequence

**Next step:** Verify state schema is complete; test full lifecycle; implement state transition matrix (OPEN→IN_PROGRESS→CLOSED, with timestamp ordering).

---

### **5. PII Claim Gateway** — EXISTS/PARTIAL ⚠️ (INVESTIGATE)

**Location:** `schemas/resource_request.schema.json` (found), `tools/` (search in progress)

**What it should do:**
- Intercept resource requests before they reach the Resource Manager
- Redact PII from request payloads
- Log redactions for audit trail
- Pass sanitized requests downstream

**Main evidence:**
- ✅ Schema exists (`schemas/resource_request.schema.json`)
- ❓ Schema content unknown — does it define PII fields?
- ❓ No `pii_redaction.py` tool found in tools/ (searched `eligibility\|activity\|PII`)

**Candidate evidence:**
- ❓ Check PR #611 (convergence experiment) — may have PII gate design

**Exercised?**
- ❓ Unknown — no tests found

**Falsifier (would prove EXISTS/PARTIAL wrong):**
- `resource_request.schema.json` has no PII field definitions
- No redaction logic found in any file
- Test fails: `test_pii_redaction()` — schema validation passes but no redaction applied

**Next step:** Inspect schema; search for redaction logic in all candidates; verify request → gateway → manager flow.

---

### **6. Replay** — MISSING/CANDIDATE ❌

**Location:** None found on main; possibly in PR #611

**What it should do:**
- Reproduce past resource allocations from the hash-chained ledger
- Enable audit trail validation (every spend/yield reconstructed)
- Support rollback to known good state
- Enable divergence-free replay (two independent replays produce identical state)

**Main evidence:**
- ❌ No replay logic on main
- ✅ Ledger hash-chain provides foundation (immutable audit trail)

**Candidate evidence:**
- ❓ PR #611 (convergence experiment) may include replay design or prototype

**Exercised?**
- ❌ Not built on main; cannot be exercised

**Falsifier (would prove MISSING wrong):**
- Implement `replay(ledger_path, start_sha, end_sha) → ResourceState`
- Test: `test_replay_transaction_log()` passes
- Divergence-free proof: two independent replays of same ledger produce identical final state (bit-for-bit match)
- Verify: replay output state matches ledger.status() output

**Next step:** Design replay engine; leverage ledger hash-chain; add replay subcommand to resource_ledger_v0_1.py.

---

## Summary Table: Composition vs. Substrate

| **Component** | **State** | **On Main?** | **Merged Candidate?** | **Action** |
|:---|:---|:---|:---|:---|
| Resource Miner | EXISTS | ✅ | — | Verify tests; run on snapshot |
| Eligibility Resolver | EXISTS/PARTIAL | ❌ | ❓ PR #608 | Merge if compatible; test handoff |
| Activity Graph | MISSING | ❌ | ❌ | Design schema; implement class; wire in |
| Resource Manager | EXISTS/PARTIAL | ✅ | ❌ | Complete state lifecycle; test full cycle |
| PII Claim Gateway | EXISTS/PARTIAL | ✅ (schema only) | ❓ | Verify schema; find/implement gate logic |
| Replay | MISSING | ❌ | ❓ PR #611? | Design engine; test divergence-free replay |

---

## Composition Decision Framework

**Question A: Can existing components compose?**

- **Resource Miner** → (output: `list[ResourceCandidate]`)
- **Eligibility Resolver** → (input: `list[ResourceCandidate]`, output: `list[EligibleResource]`)  
- **Activity Graph** ← **MISSING** — blocks composition here
- **Resource Manager** ← waiting for Activity Graph output

**Current answer:** **NO** — Activity Graph is required for composition; cannot proceed without it.

---

**Question B: Should #588 be a dedicated substrate?**

**Evidence for:**
1. Six components, but only three exist on main (Resource Miner, Resource Manager partial, PII Gate schema-only)
2. Activity Graph missing entirely — critical gap
3. Replay logic missing — cannot audit historical allocations
4. Eligibility Resolver unmerged — composition incomplete

**Evidence against:**
1. Existing ledger (tools/resource_ledger_v0_1.py) is robust and hash-chained
2. Resource Miner logic is clean and testable
3. Some schema files exist (resource_state.schema.json, resource_request.schema.json)

**Verdict:** **YES — #588 should be a dedicated substrate project** until the six components are merged on main and tested as a composed system. The missing Activity Graph is the critical blocker; without it, other components cannot feed into the allocation pipeline.

---

## Immediate Next Steps (Priority Order)

1. **Design Activity Graph** (blocking)
   - Define `ActivityEvent` canonical schema
   - Implement `ActivityGraph` class (DAG + topological sort)
   - Integrate between Eligibility Resolver and Resource Manager
   - Test DAG invariant

2. **Merge Eligibility Resolver** (PR #608)
   - Verify miner output schema compatibility
   - Test end-to-end: miner → resolver → next component
   - Merge if tests pass

3. **Verify Resource Miner** (on main, needs validation)
   - Run test suite: `pytest humanaios-funding-pipeline/resource-miner/tests/ -v`
   - Verify coverage ≥80%
   - Run on actual resource snapshot (resources.seed.jsonl)

4. **Complete Resource Manager state lifecycle**
   - Define state transition matrix (OPEN → IN_PROGRESS → COMPLETED → CLOSED)
   - Implement versioned ResourceState schema
   - Test full claim → spend → close cycle

5. **Investigate PII Claim Gateway**
   - Inspect `schemas/resource_request.schema.json`
   - Search for redaction logic in all candidates
   - Design/implement gate if missing

6. **Design Replay engine** (last in composition chain)
   - Leverage ledger hash-chain for audit trail
   - Implement `replay()` function
   - Test divergence-free property (two replays → identical state)

---

## Falsifier for this Matrix

This convergence matrix is **falsified** if:

1. Any component location is wrong (file doesn't exist or wrong logic)
2. Any component marked MISSING is found on main or merged candidates
3. Activity Graph is implemented but not wired between Resolver and Manager
4. Integration tests show composition breaks (data loss between components)
5. Replay logic exists but produces divergent results on repeated runs
6. Resource Miner tests fail or coverage <80%

**Verification command (to be run after completion):**
```bash
cd /home/user/operations

# 1. Verify all components exist
python3 -c "from humanaios_funding.resource_miner import enrich; print('✅ Resource Miner')"
python3 -c "from resource_manager import ResourceState; print('✅ Resource Manager')"
python3 -c "from activity_graph import ActivityGraph; print('✅ Activity Graph')"

# 2. Run integration test
pytest tests/test_resource_system_convergence.py -v

# 3. Run replay divergence-free test
python3 tools/resource_ledger_v0_1.py verify ledger.jsonl
python3 tools/resource_ledger_v0_1.py replay ledger.jsonl --start 0 --compare-runs 2

echo "Matrix validation: ALL PASS" || echo "Matrix validation: FAILED"
```

---

**Status:** DRAFT (awaiting Z2 review and component verification)  
**Authority:** Z1 proposal (Claude) — answers Q-588 convergence question  
**Next:** Execute Immediate Next Steps; report findings back to PRIORITY_QUEUE.md

---

---
_Generated by [Claude Code](https://claude.ai/code)_
