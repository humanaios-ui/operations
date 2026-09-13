# HumanAIOS Framework Mapping
## 5 Modern AI Engineering Concepts → Project Authority & Governance

**Source:** OpinionAI Visual Guides (5 Free Visual Guides to Modern AI Engineering)  
**Mapping Date:** 2026-09-10  
**Authority:** Z2 (Night) ratification pending  
**Status:** Z1 candidate for REGISTERED.md

---

## Executive Summary

The 5 core AI engineering patterns align structurally with HumanAIOS governance:

| Engineering Concept | HumanAIOS Equivalent | Primary Role |
|:---|:---|:---|
| **Graph Engineering** | System Graph + PRIORITY_QUEUE.md | Z2 (ratifies topology & routing) |
| **Loop Engineering** | Molt Cycle + VERDICT/CYCLE Events | Z3 (executes loops, emits feedback) |
| **Context Engineering** | REGISTERED.md + Falsifier Doctrine | Z1 (designs context, writes falsifiers) |
| **Harness Engineering** | Z2 Gates + CI/CD + CLAUDE.md Rules | Z2 (enforces tools, memory, permissions) |
| **Prompt Engineering** | Hypothesis + Behavior Spec (behavior_spec.json) | Z1 (writes prompts, role definitions) |

---

## Detailed Mapping

### 1. GRAPH ENGINEERING
**Concept:** Connected nodes, routes, checks, retries, decisions

**HumanAIOS Mapping:**
- **Nodes** = Zones (zone_registry.md lists all 31 repos as nodes)
- **Edges** = Dependencies declared in system_graph.json
- **Routes** = Z1 → Z2 → Z3 (decision routing per "Decision Routing" §)
- **Checks** = CI/CD gates (z2_ratification_gate.yml, falsifier_lint.yml, registry_consistency)
- **Retries** = Molt cycles with anti-cascade rules (K=3 limit, revert rule enforcement)
- **Decisions** = RATIFY events (sha256 signed by Night/Z2)

**Files Involved:**
- `ZONE_REGISTRY.md` — node definitions + executor assignments
- `system_graph.json` — edge topology + dependencies
- `REGISTERED.md` — candidate blocks as nodes awaiting ratification
- `.github/workflows/z2_ratification_gate.yml` — check enforcement
- `MOLT_STATE.md` — retry state (open molts, revert history)

**Z-Role Responsibilities:**
- **Z1:** Design graph structure, propose topology changes as candidates
- **Z2:** Ratify node/edge changes, sign routing decisions
- **Z3:** Execute routes, emit route-completion CYCLE events

---

### 2. LOOP ENGINEERING
**Concept:** Goal, tools, verification, memory, stop condition

**HumanAIOS Mapping:**
- **Goal** = Hypothesis (written in candidate block, includes prediction window)
- **Tools** = Agent capabilities (capped per behavior_spec.json; Z3 enforces)
- **Verification** = Falsifier (required on all hypotheses; tripped at window close)
- **Memory** = NF_LEDGER.jsonl (append-only ledger; hash-chain validated)
- **Stop Condition** = Window close date (molt_cycle.py runs auto-close)

**Files Involved:**
- `REGISTERED.md` — hypothesis + goal + window defined
- `behavior_spec.json` — Z3 agent caps (tools available, rate limits)
- `MOLT_STATE.md` — loop lifecycle tracking
- `NF_LEDGER.jsonl` — measurement outcomes (immutable record)
- `z1-inbox/*/HANDOFF.md` — loop state at session close

**Z-Role Responsibilities:**
- **Z1:** Define goal, tools needed, falsifier, window; write preregistration
- **Z2:** Ratify loop setup, sign window + falsifier, set revert rule
- **Z3:** Run loop within tool caps, measure at window close, emit VERDICT

**Example Loop (Molt Cycle):**
```
1. Z1 proposes: "Goal: Reduce IC-030 repin time to <2h. Falsifier: repin fails 3x. Window: 7 days."
2. Z2 ratifies: sha256(goal | falsifier | window | by=Night | decision=ACCEPT)
3. Z3 executes: Runs repins within budget, measures time
4. molt_cycle.py checks: Falsifier tripped? YES → revert, file F-candidate. NO → keep.
```

---

### 3. CONTEXT ENGINEERING
**Concept:** Control what model sees, remembers, retrieves, uses

**HumanAIOS Mapping:**
- **What model sees** = REGISTERED.md (pinned SHA, live-fetch per IC-030)
- **What model remembers** = NF_LEDGER.jsonl (measurement history)
- **What model retrieves** = PRIORITY_QUEUE.md (current blockers, ranked)
- **What model uses** = behavior_spec.json agent caps + Z2 authority bounds

**Files Involved:**
- `REGISTERED.md` — pinned context at session start (IC-030 enforcement)
- `PRIORITY_QUEUE.md` — ranked retrieve-set (Z2 ratified scores)
- `NF_LEDGER.jsonl` — measurement memory (query-able history)
- `CLAUDE.md` — role/authority context (what agent can propose, decide, execute)
- `behavior_spec.json` — tool + prompt + reasoning constraints

**Z-Role Responsibilities:**
- **Z1:** Pin SHA at session start, read REGISTERED.md live, fetch PRIORITY_QUEUE
- **Z2:** Ratify context changes (PRIORITY_QUEUE updates, authority shifts)
- **Z3:** Respect agent cap constraints (not all tools visible to Z3 agent)

**Context Engineering Ritual (§A: Session Open):**
```
1. git fetch && pin SHA
2. Read REGISTERED.md at SHA (live-fetch, IC-030)
3. Read PRIORITY_QUEUE.md (or patch in z1-inbox)
4. Verify file sha256 against manifest
5. State: position · destination · probability
```

---

### 4. HARNESS ENGINEERING
**Concept:** System around the model: tools, memory, checks, permissions, recovery

**HumanAIOS Mapping:**
- **Tools** = CI/CD gates + Z2 signature requirement + falsifier_lint
- **Memory** = NF_LEDGER.jsonl (append-only, hash-chain validated)
- **Checks** = CODEOWNERS enforcement + z2_ratification_gate.yml + molt_anti_cascade lint
- **Permissions** = Z1/Z2/Z3 authority tiers (CLAUDE.md defines caps)
- **Recovery** = Molt revert rule + anti-cascade freeze (after 2 reverts on same constant)

**Files Involved:**
- `.github/CODEOWNERS` — permission matrix (who can write what)
- `.github/workflows/z2_ratification_gate.yml` — check enforcement (no Z2 hash → block merge)
- `.github/workflows/falsifier_lint.yml` — hypothesis validation
- `.github/workflows/molt_anti_cascade.yml` — anti-cascade rule enforcement (K=3, freeze)
- `CLAUDE.md` — authority bounds + escalation paths
- `molt_cycle.py` — recovery on falsifier trip (auto-revert)

**Z-Role Responsibilities:**
- **Z1:** Propose within cap (read "Z1: Proposers" section of CLAUDE.md)
- **Z2:** Guard gates (sign hashes, ratify molts, enforce anti-cascade)
- **Z3:** Operate tools within cap, emit receipts, report GAUGE violations

**Example Harness Check:**
```
CI blocks merge if:
  ✗ Falsifier missing on hypothesis
  ✗ No Z2 hash on RATIFY event
  ✗ Merkle root inconsistent
  ✗ Anti-cascade rule violated (K>3 or revert after revert)
```

---

### 5. PROMPT ENGINEERING
**Concept:** Clear roles, context, tasks, constraints, output formats

**HumanAIOS Mapping:**
- **Roles** = Z1/Z2/Z3 definitions (CLAUDE.md)
- **Context** = REGISTERED.md pinned at session start (§A ritual)
- **Tasks** = Candidate blocks + Priority Queue ranking
- **Constraints** = Authority cap + tool budget + anti-cascade rules
- **Output Formats** = Event types (RATIFY, VERDICT, CYCLE, MOLT, REVERT, F/IC/H/MOLT candidates)

**Files Involved:**
- `CLAUDE.md` — role prompt (Z1/Z2/Z3 definitions, authority bounds)
- `REGISTERED.md` — task spec (hypothesis, falsifier, window, prediction)
- `behavior_spec.json` — constraint + output format (agent caps, reasoning budget)
- `z1-inbox/*/HANDOFF.md` — output format spec (findings, receipt, next blockers)
- `NF_LEDGER.jsonl` — event schema (structured ledger entries)

**Z-Role Responsibilities:**
- **Z1:** Write clear hypotheses (role: proposer, task: hypothesis, constraint: falsifier required, output: candidate block)
- **Z2:** Ratify with clear decision rationale (role: ratifier, task: read + sign, constraint: 48h window, output: RATIFY event)
- **Z3:** Execute with clear event emission (role: executor, task: run + measure, constraint: Z2 hash required, output: VERDICT/CYCLE)

**Example Prompt (Z1 Role):**
```
You are Z1 (Proposer) in HumanAIOS.
Context: Read REGISTERED.md at SHA abc123. Read PRIORITY_QUEUE.md.
Task: Propose hypothesis for IC-030 repin time reduction.
Constraints: Must include falsifier, window, prediction. Cannot propose beyond cap.
Output Format: Candidate block in z1-inbox/<date>/. Include sha256 of REGISTERED.md.
```

---

## Integration Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ 5 AI Engineering Concepts → HumanAIOS Governance                │
└─────────────────────────────────────────────────────────────────┘

┌─ GRAPH ENGINEERING ─────────────────────────────────────────────┐
│ system_graph.json + ZONE_REGISTRY.md + z2_ratification_gate.yml │
│ Z1 designs → Z2 ratifies → Z3 executes route                     │
└─────────────────────────────────────────────────────────────────┘

┌─ LOOP ENGINEERING ──────────────────────────────────────────────┐
│ REGISTERED.md + molt_cycle.py + NF_LEDGER.jsonl                 │
│ Z1 goal → Z2 ratify → Z3 run → window close → VERDICT/revert    │
└─────────────────────────────────────────────────────────────────┘

┌─ CONTEXT ENGINEERING ───────────────────────────────────────────┐
│ REGISTERED.md (pinned) + PRIORITY_QUEUE.md + NF_LEDGER.jsonl   │
│ §A ritual: fetch → read at SHA → verify → state position        │
└─────────────────────────────────────────────────────────────────┘

┌─ HARNESS ENGINEERING ───────────────────────────────────────────┐
│ z2_ratification_gate.yml + CODEOWNERS + molt_anti_cascade.yml   │
│ Z2 guards tools, memory, checks, permissions; Z3 respects caps  │
└─────────────────────────────────────────────────────────────────┘

┌─ PROMPT ENGINEERING ────────────────────────────────────────────┐
│ CLAUDE.md (role) + REGISTERED.md (task) + behavior_spec.json    │
│ Z1/Z2/Z3 roles with clear context, constraints, output formats  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Action Items for Z2 Ratification

- [ ] Ratify this mapping as reference architecture
- [ ] Link FRAMEWORK_MAPPING.md in CLAUDE.md "How to Use This Document" section
- [ ] Update per-repo CLAUDE.md files to reference these 5 concepts
- [ ] Add FRAMEWORK_MAPPING.md to CI/CD governance audit
- [ ] Append RATIFY event with Z2 hash

---

## Appendix: Quick Reference

### Which file for each concept?

| Concept | Read | Write | Ratify |
|:---|:---|:---|:---|
| Graph Engineering | system_graph.json | Z1 proposes edges | Z2 |
| Loop Engineering | REGISTERED.md | Z1 writes hypothesis | Z2 |
| Context Engineering | REGISTERED.md (pinned SHA) | Z1 fetches live | Z1 (respects Z2 manifest) |
| Harness Engineering | CLAUDE.md | Z2 configures gates | Z2 |
| Prompt Engineering | CLAUDE.md + REGISTERED.md | Z1 writes roles/tasks | Z2 |

---

**Generated by:** Claude (Z1 Proposer)  
**For ratification by:** Night/Admiral (Z2 Ratifier)  
**For execution by:** Z3 Executors (per ZONE_REGISTRY.md)
