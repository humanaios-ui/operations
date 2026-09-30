# Q-TIER-ASSIGNMENT-BATCH-01

**Submitted:** 2026-09-30  
**Proposer:** Claude (Z1)  
**Authority:** Z2 Ratification Required  
**Decision Window:** 48 hours  

---

## Issue

92 of 98 governance candidates are untiered. No Tier 0/1/2 assignment prevents resource-based allocation, scheduling, and execution. Queue processing cannot proceed without this classification.

## Scope

Batch ratify Tier assignments for all 92 awaiting_z2 candidates currently in z1-inbox/INDEX.yaml using the resource-based allocation model (RBE-OPS, RESOURCE_UNITS.yaml, PRIORITY_QUEUE.md).

**Proposed allocation framework:**

```
Tier 0 (Critical Infrastructure — execute first):
  - System control plane changes (governance gates, INTENT-OS core, Z2 authorization mechanisms)
  - Measurement/falsification infrastructure (molt ledger, witness ledger, hypothesis tracking)
  - Resource allocation foundation (Resource System scaffold for Issue #588)
  - Cost: RAT-min band A (zero resource cost); rank by benefit
  
Tier 1 (Major Features — execute after Tier 0):
  - ACAT ecosystem features (distribution plays, benchmark, observability)
  - Tool control automation (manifest drift prevention, workflow validation)
  - Registry audit/reconciliation (repository consistency)
  - Cost: RAT-min band B (>0 cost); rank by benefit/cost density
  
Tier 2 (Refinement — execute after Tier 1):
  - Extended Intent-OS capabilities (pages gate, refresh, bus automation)
  - Documentation & onboarding (PII vault, evidence graph)
  - Convergence detection & portfolio replay (controller optimization)
  - Cost: RAT-min band B; execute when capacity available
```

## Candidates Affected

| Category | Count | Status |
|:---------|:------|:-------|
| BOARD (Board Rulings) | 28 | 2 ratified, 26 awaiting |
| INTENTOS (Intent-OS) | 5 | 2 ratified, 3 awaiting |
| TOOLCONTROL | 3 | All awaiting |
| REGISTRY | 3 | All awaiting |
| ACAT | 2 | All awaiting |
| FRAMEWORK | 2 | All awaiting |
| Other (40 projects) | 56 | Mixed ratified/awaiting |
| **Total** | **98** | **10 ratified, 88 awaiting** |

**Currently Tiered (by assignment):**
- Tier 0: 1 (Q-TOOL-MANIFEST-DRIFT-PREVENTION-01)
- Tier 1: 1 (Q-GOVDRIFT-01)
- Tier 2: 4 (Q-MOLT-TEMPORAL-PURITY-01, Q-GATE-PATHS-TEST-LOGIC-01, Q-RESEARCH-OPS-LOOP-AND-AUDITOR-01, Q-WITNESS-LEDGER-TIER0-EXTENSION-01)
- **Untiered: 92** ← Batch assignment required

## Falsifier

**The system is functioning if:**
1. All 92 untiered candidates are assigned to Tier 0, 1, or 2 (no new untiered items created)
2. Tier 0 candidates are ranked by benefit; Tier 1/2 by benefit/cost density
3. Z2 hash is issued for the batch decision (machine-readable ratification)
4. Tier assignments are applied to z1-inbox/INDEX.yaml (z1-inbox/2026-09-30/Q-TIER-ASSIGNMENT-BATCH-01-RESULT.md)

**The system is failing if:**
1. Tier assignments remain unresolved past 2026-10-02 23:59 UTC
2. New candidates are filed untiered after this decision (broken governance process)
3. Tier assignments are made but not reflected in INDEX.yaml or resource scheduler
4. Queue processing is attempted without tier-based prioritization (resource allocation failure)

## Next Step (Conditional on Ratification)

Once Z2 ratifies Tier assignments:

1. **Update INDEX.yaml** with tier field for all 92 candidates
2. **Run RBE-OPS priority queue engine** (priority_queue_engine.py) to rank candidates by cost/benefit
3. **Emit Z3 executor assignments** per ZONE_REGISTRY.md (per-repo Z3 responsibility)
4. **Begin Phase-based rollout:**
   - Phase 1: Execute Tier 0 candidates (unblock resource allocation)
   - Phase 2: Execute Tier 1 candidates (deliver major features)
   - Phase 3: Execute Tier 2 candidates (refinement & optimization)

---

## Authority & Evidence

- **Authority:** Z2 (Night) sole decision maker for tier classification (CLAUDE.md)
- **Evidence:** 
  - z1-inbox/INDEX.yaml (all 98 candidates indexed, status tracked)
  - PRIORITY_QUEUE.md (current queue with Q-TEMPORAL-DISSOLUTION-01 as gating item)
  - RESOURCE_UNITS.yaml (resource cost taxonomy)
  - Issue #588 (Resource System project candidate requiring Tier 0 infrastructure)

---

**Decision Requested:** Ratify Tier 0/1/2 assignment for all 92 untiered candidates using the resource-based allocation framework above.

**Z2 Signature Required:** sha256(candidate | by=Night | at=<timestamp> | decision=ACCEPT|EDIT|REJECT)
