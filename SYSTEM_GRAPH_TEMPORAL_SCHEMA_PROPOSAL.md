# Proposal: Temporal Sequencing for System Graph Schema

**Document ID:** Q-SYSTEM-GRAPH-TEMPORAL-01  
**Date:** 2026-10-08  
**Author:** Z1 (Claude)  
**Status:** Awaiting Z2 Ratification  
**Target:** system_graph.json v0.3  

---

## Problem Statement

**Current Issue:**
- system_graph.json v0.2 contains 16 detected cycles, rendering validation fails
- Cycles are **intentional by design** (molt feedback loops, resource constraints)
- Graph renderer assumes DAG (directed acyclic graph), which is incorrect for this system
- No way to distinguish between "unsafe cycles" and "designed feedback loops"

**Root Cause:**
Schema treats all edges as single-timeslice data dependencies. It doesn't represent:
- **Control flow** (work order scheduling)
- **Data flow** (information passing between processes)
- **Feedback loops** (time-sequenced iterative cycles)

**Impact:**
- `system_graph.rendered.md` validation fails (blocks regeneration)
- Graph analysis tools cannot reason about cycle safety
- Designers cannot distinguish intentional from accidental cycles

---

## Solution: Temporal Sequencing Model

Add explicit **generation/phase ordering** to break cycles while preserving design intent.

### Schema Changes

#### 1. **Add `generation` Field to Nodes**

```json
{
  "id": "MOLT",
  "name": "Molt Cycle",
  "type": "process",
  "status": "LAID",
  "zone": "code",
  "generation": [0, 1, 2],  // NEW: Can operate in generations 0-2
  "feedback_loop": true,     // NEW: Part of intentional cycle
  "generation_description": "Molts sequence through 3 generations (bounded by K=3 anti-cascade rule)"
}
```

**Generation Semantics:**
- `generation: [0]` — First-time computation (no prior state)
- `generation: [0, 1]` — Can iterate once (T₀ → T₁)
- `generation: [0, 1, 2]` — Can iterate twice (T₀ → T₁ → T₂)
- `generation: null` — Acyclic (always safe, same generation)

#### 2. **Extend Edge Definition**

```json
{
  "source": "FS",
  "target": "Z2",
  "edge_type": "control_flow",
  "label": "candidate block",
  "generation_rule": "same",     // NEW: FS gen N → Z2 gen N
  "feedback_loop": true,          // NEW: Part of molt cycle
  "cycle_id": "molt-ratification" // NEW: Links to the 5-node cycle
}
```

**Generation Rules:**
- `"same"` — source gen N → target gen N (no forward progress)
- `"forward"` — source gen N → target gen N+1 (advances generation)
- `"same_or_forward"` — either allowed (flexible timing)

#### 3. **Add Cycle Metadata**

```json
{
  "feedback_loops": [
    {
      "id": "molt-ratification",
      "name": "Molt Ratification Cycle",
      "nodes": ["MOLT", "FS", "Z2"],
      "description": "Molts generate findings; findings propose candidates; Z2 ratifies molts",
      "safety_mechanism": "anti-cascade-rules",
      "max_depth": 3,  // K=3 rule
      "is_intentional": true,
      "ratified_by": "Q-CLAUDE-MOLT-CYCLE-DESIGN-01"
    }
  ]
}
```

---

## Updated Validator Logic

### Old Logic (Fails on Cycles)
```python
def validate_graph(graph):
    if has_cycle(graph):
        return INVALID  # ❌ Current behavior
    return VALID
```

### New Logic (Respects Temporal Ordering)
```python
def validate_graph(graph):
    # Step 1: Identify feedback loops
    cycles = detect_cycles(graph)
    
    # Step 2: Check each cycle
    for cycle in cycles:
        cycle_meta = graph.feedback_loops.get(cycle.id)
        
        if not cycle_meta:
            return INVALID  # Unknown cycle
        
        if not cycle_meta.is_intentional:
            return INVALID  # Unintended cycle
        
        # Step 3: Verify generation constraints
        max_gen = 0
        for edge in cycle.edges:
            if edge.generation_rule == "forward":
                max_gen += 1
        
        if max_gen > cycle_meta.max_depth:
            return INVALID  # Exceeds depth limit
    
    # Step 4: Verify no cross-cycle contamination
    # (ensure cycles don't interact unsafely)
    
    return VALID if all_checks_pass else INVALID
```

---

## Schema Update: Detailed Examples

### Before (v0.2)

```json
{
  "version": "0.2",
  "nodes": {
    "MOLT": {
      "id": "MOLT",
      "name": "Molt Cycle",
      "type": "process",
      "status": "LAID"
    }
  },
  "edges": [
    {
      "source": "Z2",
      "target": "MOLT",
      "label": "RATIFY hash"
    },
    {
      "source": "MOLT",
      "target": "FS",
      "label": "REVERT → F/IC candidate"
    },
    {
      "source": "FS",
      "target": "Z2",
      "label": "candidate block"
    }
  ]
}
```

**Problem:** Cycle detected: Z2 → MOLT → FS → Z2 ❌

### After (v0.3)

```json
{
  "version": "0.3",
  "schema_version": "temporal-1.0",
  "nodes": {
    "MOLT": {
      "id": "MOLT",
      "name": "Molt Cycle",
      "type": "process",
      "status": "LAID",
      "generation": [0, 1, 2],
      "feedback_loop": true,
      "generation_description": "Bounded to 3 generations per anti-cascade K=3 rule"
    },
    "Z2": {
      "id": "Z2",
      "name": "Z2 Ratification Gate",
      "type": "gate",
      "generation": [0, 1, 2],
      "feedback_loop": true
    },
    "FS": {
      "id": "FS",
      "name": "Findings Scan",
      "type": "process",
      "generation": [0, 1, 2],
      "feedback_loop": true
    }
  },
  "edges": [
    {
      "source": "Z2",
      "target": "MOLT",
      "label": "RATIFY hash",
      "edge_type": "control_flow",
      "generation_rule": "same",
      "feedback_loop": true,
      "cycle_id": "molt-ratification"
    },
    {
      "source": "MOLT",
      "target": "FS",
      "label": "REVERT → F/IC candidate",
      "edge_type": "data_flow",
      "generation_rule": "forward",
      "feedback_loop": true,
      "cycle_id": "molt-ratification"
    },
    {
      "source": "FS",
      "target": "Z2",
      "label": "candidate block",
      "edge_type": "control_flow",
      "generation_rule": "forward",
      "feedback_loop": true,
      "cycle_id": "molt-ratification"
    }
  ],
  "feedback_loops": [
    {
      "id": "molt-ratification",
      "name": "Molt Ratification Cycle",
      "nodes": ["Z2", "MOLT", "FS"],
      "edges": [
        {"source": "Z2", "target": "MOLT"},
        {"source": "MOLT", "target": "FS"},
        {"source": "FS", "target": "Z2"}
      ],
      "description": "Z2 ratifies molt → molt reverts → findings scanned → candidates to Z2",
      "safety_mechanism": "anti-cascade-rules",
      "anti_cascade_rules": [
        "One open molt per constant",
        "No candidate from own window (rule 2)",
        "K=3 max concurrent molts (rule 3)",
        "2-revert freeze (rule 4)",
        "Priority queue ranking (rule 5)"
      ],
      "max_depth": 3,
      "max_width": 1,
      "is_intentional": true,
      "design_rationale": "CLAUDE.md § Molt Decisions; enables recursive learning with safety bounds",
      "ratified_by": "Q-CLAUDE-GOVERNANCE-01",
      "validation": "PASS"
    }
  ]
}
```

**Result:** Cycle validated ✅ (intentional feedback loop with bounded depth)

---

## Temporal Execution Timeline

### Generation Model

```
Generation 0 (T₀):
  Z2 receives first MOLT candidate
    ↓
  Z2 RATIFY hash signed (generation_rule: same)
    ↓
  MOLT applies ratified change (generation_rule: same)

Generation 1 (T₁):
  MOLT window closes, falsifier tripped
    ↓
  MOLT → FS (REVERT → F/IC candidate) [generation_rule: forward]
    ↓
  FS emits new candidate (generation_rule: forward)
    ↓
  FS → Z2 [generation_rule: forward]
    ↓
  Z2 receives gen-1 candidate

Generation 2 (T₂):
  Z2 evaluates: is this a new molt or a re-score?
    ↓
  (K=3 rule: at most 2 more molts can start)
    ↓
  If approved: MOLT-B ratified (generation_rule: same)
    ↓
  MOLT-B applies [generation_rule: same]

Generation 3+ (blocked):
  Anti-cascade Rule 3: K=3 max concurrent
  → New molt candidates BLOCKED until one closes
```

**Why This Is Safe:**
- Max depth: 3 generations
- Max concurrent: 3 molts
- Each node knows which generation(s) it can operate in
- Edges enforce forward-only progress in feedback loops
- Validator confirms no edge violates generation constraints

---

## Migration Path

### Phase 1: Schema Update (Non-Breaking)
1. Add optional `generation`, `feedback_loop` fields to nodes (default: null/false)
2. Add optional `generation_rule`, `feedback_loop`, `cycle_id` fields to edges (default: null/false)
3. Add optional `feedback_loops` array to root (default: [])
4. Validator: WARN if cycles found but not marked (backward compatible)

### Phase 2: Annotation (Requires Z2 Ratification)
1. Z2 reviews and ratifies each feedback loop (ties to anti-cascade rules in CLAUDE.md)
2. Generate `feedback_loops` array with ratification hashes
3. Mark all nodes/edges in known cycles with generation info

### Phase 3: Validation Enforcement
1. Switch validator to NEW logic (cycles must be explicitly marked)
2. Block unmarked cycles (CI gate)
3. Update system_graph_render_v1_0.py to skip cycle warnings for validated loops

---

## All 16 Cycles: Classification

| # | Cycle | Type | Safety Rule | Status |
|:--|:------|:-----|:------------|:-------|
| 1 | CIG→REG→PRS→EV→FS→Z2→CIG | Validation | Hash-chain | ⚠️ Review |
| 2 | Z2→MOLT→Z2 | Direct molt | Anti-cascade-3 | ✅ Intentional |
| 3 | EV→FS→Z2→MOLT→CONST→TC→EV | Feedback | Anti-cascade-1,3 | ✅ Intentional |
| 4 | PRS→EV→FS→Z2→MOLT→CONST→TC→Q→PRS | Execution | Anti-cascade-3,5 | ✅ Intentional |
| 5 | EV→FS→Z2→MOLT→CONST→TC→Q→AG→EV | Execution | Anti-cascade-3,5 | ✅ Intentional |
| 6 | Q→OM→NF→Q | Scoring | Anti-cascade-5 | ✅ Intentional |
| 7 | MOLT→CONST→TC→Q→OM→NF→MOLT | Feedback | Anti-cascade-1,3 | ✅ Intentional |
| 8 | Z2→MOLT→CONST→TC→Q→OM→Z2 | Ratification | Anti-cascade-3 | ✅ Intentional |
| 9 | EV→FS→Z2→MOLT→CONST→TC→Q→ADV→EV | Testing | Anti-cascade-3 | ✅ Intentional |
| 10 | MOLT→CONST→TC→Q→MOLT | Direct | Anti-cascade-1,3 | ✅ Intentional |
| 11 | Q→RL→Q | Resource | Anti-cascade-5 | ✅ Intentional |
| 12 | MOLT→CONST→TC→Q→RL→MOLT | Resource | Anti-cascade-3 | ✅ Intentional |
| 13 | PRS→EV→FS→Z2→MOLT→CONST→PRS | Measurement | Anti-cascade-2 | ✅ Intentional |
| 14 | EV→FS→Z2→MOLT→ML→EV | Ledger | Anti-cascade-1 | ✅ Intentional |
| 15 | FS→Z2→MOLT→FS | Direct | Anti-cascade-1,2 | ✅ Intentional |
| 16 | CIG→REG→MK→CIG | Validation | Merkle-chain | ⚠️ Review |

**Legend:**
- ✅ **Intentional** — Designed feedback loop, covered by anti-cascade rules
- ⚠️ **Review** — Validation/merkle cycles; need separate safety analysis

---

## Affected Files

| File | Change | Scope |
|:-----|:--------|:-------|
| `system_graph.json` | Schema v0.2 → v0.3; add generation/feedback_loop fields; list all 16 cycles | Major |
| `tools/system_graph_render_v1_0.py` | Update validator to handle temporal rules | Major |
| `tools/system_graph_generator.py` | Add generation assignment logic; validate against anti-cascade rules | Major |
| `CLAUDE.md` | Document feedback loops under "Molt Decisions" § | Minor |
| `.github/workflows/z2_ratification_gate.yml` | Update to validate against feedback_loops manifest | Minor |

---

## Validation Checklist (for Z2)

- [ ] **Design Alignment:** Do the 16 feedback loops correctly map to the anti-cascade rules in CLAUDE.md?
- [ ] **Safety Bounds:** Is K=3 the correct max-depth for all cycles? (Verify against molt_cycle.py)
- [ ] **Cross-Cycle Risk:** Can any two feedback loops interact unsafely?
- [ ] **Temporal Ordering:** Does the generation model match the actual molt measurement window W?
- [ ] **CI Impact:** Will updated validator catch regressions if someone adds an unmarked cycle?

---

## Success Criteria

✅ `system_graph.rendered.md` regenerates without "Cycle detected" error  
✅ All 16 cycles explicitly marked with anti-cascade rule justification  
✅ Validator correctly rejects new unmarked cycles while accepting known ones  
✅ Generation constraints enforceable by CI/CD gates  
✅ Documentation updated to explain temporal model to new readers  

---

## Timeline

| Phase | Owner | Duration | Gate |
|:------|:------|:---------|:-----|
| Proposal review | Z2 | 48h | Z2 RATIFY |
| Schema implementation | Z1 | 3 days | CI pass |
| Feedback loop annotation | Z1 | 2 days | Anti-cascade validation |
| Validator update | Z1 | 3 days | system_graph lint |
| Rendered.md regeneration | Automation | 1h | CI pass |
| **Total** | | **~10 days** | Z2 signed |

---

**Next Step:** Awaiting Z2 (Night) ratification via REGISTERED.md entry.
