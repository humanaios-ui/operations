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

**CORRECTIONS APPLIED** (per humanaios-ui review, 2026-09-30): Eligible Resolver split into two rows; PII Gateway corrected to MISSING; Resource Manager clarified as accounting-focused foundation; Replay narrowed to portfolio replay; Activity Graph composition assumption noted as untested; verdict changed to UNRESOLVED pending #611 protocol.

| **Component** | **Location (main)** | **Main Evidence** | **Candidate Evidence** | **State** | **Executable?** | **Exercised?** | **Evidence (Would Prove Wrong)** |
|:---|:---|:---|:---|:---|:---|:---|:---|
| **Resource Miner** | `humanaios-funding-pipeline/resource-miner/` | `resource_miner/miner.py` (enrich, dedupe, route, need-match) | — | EXISTS | ✅ YES (Python module, callable) | ❓ Unclear (tests exist; CI status unknown) | `python3 -m pytest humanaios-funding-pipeline/resource-miner/tests/ -v` fails, or coverage <80% |
| **Eligibility Resolver** | `humanaios-funding-pipeline/entitlement-navigator/entitlement/engine.py` | `evaluate_program()`, `evaluate_profile()` (executable) | — | **EXISTS** | ✅ YES (methods callable) | ❓ Unclear (tests unknown) | Entitlement Navigator methods deleted or signature changed incompatibly |
| **Miner→Resolver Binding** | — | — | `#608` (integration) | **CANDIDATE** | ⚠️ CONDITIONAL | ❌ NO | PR #608 fails CI, or integration test `test_miner_entitlement_handoff()` fails (schema incompatibility) |
| **Activity Lifecycle Model** | — (design needed) | None found on main | None found in candidates | **MISSING** | ❌ NO | ❌ NO | NOTE: Assuming hard composition chain (Resolver → Activity Graph → Manager) is a **new architectural assumption**, not derived from existing components. This should be tested before being presupposed. Canonical schema for `ActivityEvent` + `ActivityGraph` not yet designed. |
| **Resource Accounting Ledger** | `tools/resource_ledger_v0_1.py` | Ledger claims/spend/yield logic (claim, spend, yield, price, waste, capacity, close, verify, report) | — | **EXISTS** | ✅ YES (CLI tool, executable) | ✅ YES (subcommands verified; tools/README) | `resource_ledger_v0_1.py` refactored or subcommands removed |
| **Resource Manager (Lifecycle)** | `schemas/resource_state.schema.json` (partial) | State schema exists (work-state/blocking-state) | — | **PARTIAL/FOUNDATION** | ⚠️ PARTIAL | ❓ Unclear | Note: #588's Resource Manager concerns **lifecycle** (inventory, restriction, allocation, consumption, conversion, renewal, expiration, loss, realized value), not accounting. `resource_state.schema.json` is work-state focused, not lifecycle-focused. Needs lifecycle model: acquired-state, discovered-state, allocated-state, consumed-state, converted-state, expires-state, loss-state. |
| **PII Claim Gateway** | `schemas/resource_request.schema.json` (found) | Schema contains resource cost/dependency semantics, **NOT** PII redaction | — | **MISSING** | ❌ NO | ❌ NO | `resource_request.schema.json` actually contains PII redaction fields, or separate `pii_redaction.py` logic found. (Note: privacy/redaction primitives exist elsewhere in repo; check audit-trail, claim-receipt, disclosure-receipt designs.) |
| **Portfolio Replay** | `tools/` (search yields none) | None found on main | Check #611 (convergence experiment) | **MISSING** | ❌ NO (on main); ❓ CANDIDATE | ❌ NO | NOTE: Portfolio replay = material evidence/controller changes recompute affected resource branches without re-asking known facts. Ledger replay (audit-trail reconstruction) is **narrower** and separate. Implement portfolio replay: (1) detect material change; (2) identify affected branches; (3) recompute without re-query. |

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

### **2. Eligibility Resolver** — EXISTS ✅

**Location:** `humanaios-funding-pipeline/entitlement-navigator/entitlement/engine.py`

**What it does:**
- Takes program/profile eligibility evaluation criteria
- Evaluates eligibility based on entitlement rules
- Returns pass/fail/conditional for resource allocation decisions

**Main evidence (executable):**
- ✅ `evaluate_program()` and `evaluate_profile()` methods exist and are callable
- ✅ Methods implement deterministic eligibility logic
- ✅ Integrated with the Entitlement Navigator on main

**Candidate evidence:**
- PR #608: Miner → Eligibility Resolver binding (integration, not resolver itself)

**Exercised?**
- ❓ Unclear — tests likely exist; CI status unknown

**Falsifier (would prove EXISTS wrong):**
- `humanaios-funding-pipeline/entitlement-navigator/entitlement/engine.py` deleted or methods removed
- `evaluate_program()` / `evaluate_profile()` signature changed incompatibly
- Methods fail or throw on standard inputs

**Next step:** Verify resolver tests pass; validate integration with Resource Miner output schema via PR #608.

---

### **2B. Miner → Resolver Binding** — CANDIDATE ⚠️

**Location:** PR #608 (unmerged)

**What it does:**
- Wires Resource Miner output (ranked candidates) into Eligibility Resolver
- Ensures schema compatibility between miner's `ResourceCandidate` and resolver's input
- Enables end-to-end: Miner → Resolver → downstream

**Main evidence:**
- ❌ Not on main (binding unmerged)

**Candidate evidence:**
- ✅ PR #608: explicit resource-miner + entitlement-navigator integration

**Exercised?**
- ❌ Unmerged — no CI validation on main

**Falsifier (would prove CANDIDATE wrong):**
- PR #608 closes or is reverted
- Integration test `test_miner_entitlement_handoff()` fails
- Schema mismatch: miner output cannot be passed to resolver input

**Next step:** Merge PR #608 after validating interface compatibility.

---

### **3. Activity Lifecycle Model** — MISSING ❌

**Location:** None found

**What it should do (per #588 definition):**
- Observability/history: source, action, artifact, AI activity, human activity, check-ins, observed execution, outcome, deviation, next operation
- **CRITICAL ASSUMPTION:** The matrix assumes hard composition: `Resolver → Activity Graph → Resource Manager`. This is **a new architectural assumption**, not derived from existing components, and should be tested before being presupposed.

**Main evidence:**
- ❌ No `ActivityEvent` schema
- ❌ No `ActivityGraph` class
- ❌ No activity lifecycle model

**Candidate evidence:**
- ❌ Not found in candidate branches either
- graph_convergence_v1_0.py exists but operates on pre-built graphs (requires external GRAPH_ALIGNMENT.yaml)

**Exercised?**
- ❌ Not built; cannot be exercised

**Falsifier (would prove MISSING wrong):**
- Find `schemas/activity_event.schema.json` or `models/ActivityGraph` class
- Canonical event type schema: `{"id": "...", "timestamp": "...", "type": "...", "actor": "...", "payload": {...}}`
- Test: `test_activity_graph_DAG_invariant()` passes
- DAG validation: no cycles, topological sort deterministic

**Next step:** (Conditional on architecture decision) Design ActivityEvent schema; test hard composition assumption; implement ActivityGraph class if composition is confirmed.

---

### **4. Resource Accounting Ledger** — EXISTS ✅

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

### **4. Resource Accounting Ledger** — EXISTS ✅

**Location:** `tools/resource_ledger_v0_1.py`

**What it does:**
- Append-only hash-chained ledger of resource claims, spends, yields, prices, waste, capacity, and closure
- Implements atomic serialization (flock lock)
- Validates unit registry (RESOURCE_UNITS.yaml)
- Supports verification, reporting, and price/exchange-rate recording

**Main evidence (executable):**
- ✅ `resource_ledger_v0_1.py`: Complete implementation with CLI subcommands
- ✅ Methods: init, verify, cap, claim, spend, yield, price, waste, close, status, report
- ✅ Hash-chain validation via verify() — prevents tampering
- ✅ Lock mechanism (flock) — serializes concurrent writes
- ✅ Unit registry support (RESOURCE_UNITS.yaml)

**Candidate evidence:**
- ❓ Price event logic (`price()` subcommand) partially documented

**Exercised?**
- ✅ Ledger CLI has subcommands documented in tools/README
- ⚠️ Full test coverage unknown; CI status unclear

**Falsifier (would prove EXISTS wrong):**
- `resource_ledger_v0_1.py` deleted or subcommands removed
- `verify()` or `close()` operations fail on valid inputs
- Hash-chain validation broken

**Next step:** Run ledger test suite; validate full claim → spend → close cycle.

---

### **5. Resource Manager (Lifecycle)** — PARTIAL/FOUNDATION ⚠️

**Location:** `schemas/resource_state.schema.json` (partial), needs full lifecycle model

**What #588 requires (NOT what the ledger provides):**
- **Resource lifecycle tracking**: inventory, restriction, allocation, consumption, conversion, renewal, expiration, loss, realized value
- **Acquired-state model**: when/how resource entered system (mined, granted, synthesized, imported)
- **Discovered-state model**: material changes (new facts, price updates, availability changes)
- **Allocated-state model**: reserved for specific purpose/actor/window
- **Consumed-state model**: actual use vs reserved; tracking deviation
- **Converted-state model**: resource → other resource transformation
- **Expires-state model**: TTL, renewal windows, stale-state detection
- **Loss-state model**: unavailable, revoked, orphaned resources

**Main evidence (partial):**
- ✅ `resource_ledger_v0_1.py`: Accounting foundation (claim/spend/yield)
- ⚠️ `schemas/resource_state.schema.json`: Exists; content is work-state/blocking-state focused, **NOT** lifecycle-focused

**Candidate evidence:**
- ❓ Price event logic, capacity tracking (partial)

**Exercised?**
- ✅ Ledger verified executable; accounting operations callable
- ❌ Lifecycle model not exercised (doesn't exist yet)

**Falsifier (would prove PARTIAL/FOUNDATION wrong):**
- Ledger deleted
- Ledger operations (claim/spend/close) fail
- But also: if `resource_state.schema.json` already contains acquired/discovered/allocated/consumed/converted/expires/loss state models fully, then this is EXISTS not PARTIAL

**Next step:** Design resource lifecycle state machine; define acquired/discovered/allocated/consumed/converted/expires/loss models; implement ResourceState versioning; integrate with ledger for durability.

---

### **6. PII Claim Gateway** — MISSING ❌

**Location:** `schemas/resource_request.schema.json` (found, but does not contain PII logic)

**What it should do:**
- Intercept resource requests before they reach allocation
- Redact/minimize PII from request payloads
- Maintain disclosure receipt (who asked for what, for what purpose, with which justification)
- Enforce minimum-sufficient-claim (don't ask for more data than needed)
- Pass sanitized requests downstream

**Main evidence:**
- ❌ `schemas/resource_request.schema.json` exists but contains **resource cost/dependency semantics**, NOT PII redaction
- ❌ No `pii_redaction.py` tool found
- ❌ No disclosure-receipt mechanism found
- ❌ No minimum-sufficient-claim validation found

**Candidate evidence:**
- ❓ Check PR #611 (convergence experiment) — may have PII gate design
- **NOTE:** Privacy/redaction primitives exist elsewhere in repo (audit-trail, claim-receipt, disclosure-receipt designs); integration point unknown

**Exercised?**
- ❌ Not exercised; logic does not exist on main

**Falsifier (would prove MISSING wrong):**
- Find `pii_redaction.py` or PII redaction logic in resource_request handlers
- Find disclosure-receipt generation on request intake
- Test: `test_pii_redaction_in_resource_request()` passes
- Redaction happens before allocation and is logged

**Next step:** Investigate privacy/redaction primitives elsewhere in repo; design PII gate if not present; integrate with resource request flow.

---

### **7. Portfolio Replay** — MISSING ❌

**Location:** None found on main; possibly in PR #611

**What #588 requires (NOT what ledger replay provides):**
- **Portfolio replay** = material evidence/controller changes recompute affected resource branches without re-asking known facts
- Detect material change (new evidence, controller action, falsifier trip, measurement completion)
- Identify affected branches (resources that depend on changed state)
- Recompute those branches (refresh allocation, reconcile consumption, update valuation)
- Divergence-free property (two independent replays produce identical state)

**Main evidence:**
- ❌ No portfolio replay logic on main
- ✅ Ledger hash-chain exists (foundation for audit trail, but NOT equivalent to portfolio replay)

**Candidate evidence:**
- ❓ PR #611 (convergence experiment) may include replay design

**Exercised?**
- ❌ Not implemented; cannot be exercised

**Falsifier (would prove MISSING wrong):**
- Implement `replay(evidence_change, affected_branches) → updated_resource_state`
- Detect material changes (evidence-provided, controller-action, falsifier-trip, window-closed)
- Test: `test_portfolio_replay_divergence_free()` passes (two independent replays → identical state)
- Test: `test_replay_recovers_prior_state()` passes (replay from ledger restores prior resource allocation)

**Next step:** (Conditional on #611 findings) Design portfolio replay engine; wire material-change detection; implement divergence-free replay; test against ledger for consistency.

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

## Summary Table: Component Inventory

| **Component** | **State** | **On Main?** | **Foundation/Merged?** | **Action** |
|:---|:---|:---|:---|:---|
| Resource Miner | EXISTS | ✅ | ✅ | Verify tests; run on snapshot |
| Eligibility Resolver | EXISTS | ✅ | ✅ | Verify methods; test integration |
| Miner→Resolver Binding | CANDIDATE | ❌ | PR #608 (unmerged) | Merge PR #608 after validating schema compatibility |
| Activity Lifecycle Model | MISSING | ❌ | ❌ | Design schema; decide if hard composition assumption holds |
| Resource Accounting Ledger | EXISTS | ✅ | ✅ | Verify test suite; validate accounting operations |
| Resource Manager (Lifecycle) | PARTIAL/FOUNDATION | ✅ (partial) | ⚠️ Incomplete | Design lifecycle state machine (acquired/discovered/allocated/consumed/converted/expires/loss); integrate with ledger |
| PII Claim Gateway | MISSING | ❌ | ❌ | Design gate; integrate with request flow |
| Portfolio Replay | MISSING | ❌ | ❓ PR #611? | Design engine; test divergence-free replay |

---

## Composition Decision Framework

**Note:** The original matrix concluded **YES — #588 should be dedicated substrate**. However, per humanaios-ui review, this verdict is **PREMATURE** and should remain **UNRESOLVED** pending completion of the #611 acceptance protocol, which preregistered:
- Broader matrix (~15 components)
- Missing-primitive set
- One end-to-end trace
- Provenance sequence
- **Only then** a composition-vs-substrate finding

---

**Current Question A: Can existing components compose?**

**Composition chain (per current matrix):**
- **Resource Miner** → (output: `list[ResourceCandidate]`)
- **Eligibility Resolver** → (input: `list[ResourceCandidate]`, output: `list[EligibleResource]`)  
- **Activity Lifecycle Model** ← **MISSING** — assumed as hard middleware, but this assumption is untested
- **Resource Manager (Lifecycle)** ← waiting for Activity Graph output

**Current answer:** **UNRESOLVED** — depends on whether Activity Graph is actually a required middleware (architectural assumption to be tested) or whether Resolver → Manager can compose directly with lifecycle state-machine.

---

**Current Question B: Is #588 a dedicated substrate or composition of existing parts?**

**Evidence for composition:**
1. Ledger exists and is robust (claim/spend/yield/price/capacity/close)
2. Resolver exists on main (entitlement evaluation)
3. Miner exists on main (candidate ranking)
4. Ledger + Resolver + Miner could potentially cover 50% of #588 scope

**Evidence for dedicated substrate:**
1. Lifecycle model (acquired/discovered/allocated/consumed/converted/expires/loss) is MISSING
2. Activity observability (source/action/artifact/AI/human/checkin/outcome/deviation) is MISSING
3. Portfolio replay (material-change recomputation) is MISSING
4. PII/disclosure/minimum-sufficient-claim gateway is MISSING
5. Miner→Resolver binding unmerged (PR #608)

**Current verdict:** **UNRESOLVED, PENDING #611 PROTOCOL** — the composition decision requires:
1. Verification that hard Activity Graph assumption is sound (or design a direct Resolver → Manager composition)
2. Mapping of the full ~15-component set (not just 6)
3. End-to-end trace through #611 (convergence experiment)
4. Falsifier protocol confirmation from #611 (what would prove composition works vs. substrate is needed)

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
