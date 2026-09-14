# GOVERNANCE_FILES.md — Authoritative Registry

**Purpose:** Single source of truth for all governance files, their structure, authority, and location.  
**Updated:** 2026-09-14  
**Authority:** Z2 (Night) — ratifies file definitions, structure changes, ownership  
**Model:** Resource-based (no arbitrary time deadlines; resource_cost & capacity-driven)

---

## File Registry

### Core Governance (Z2 Writes)

| File | Purpose | Format | Authority | R/W | Status |
|:-----|:--------|:-------|:----------|:----|:-------|
| **REGISTERED.md** | Candidate proposal log; all Z1 proposals awaiting/approved Z2 ratification | YAML array | Z2 sole write (sha256 hash required) | Z1 read, Z2 write | 🔴 MISSING |
| **CLAUDE.md** | Authority map; Z-roles, escalation paths, decision routing | Markdown + YAML frontmatter | Z2 ratifies changes | Z1 read, Z2 write | ✅ EXISTS |
| **PRIORITY_QUEUE.md** | Ranked blockers/findings; sorted by resource_impact (not deadline) | YAML array | Z2 ratifies scores | Z1 read, Z2 ratify | 🔴 MISSING |
| **ZONE_REGISTRY.md** | Active repos (31 zones), executor assignments, repo caps | YAML | Z2 ratifies changes | Z1 read, Z2 write | 🔴 MISSING |
| **MOLT_STATE.md** | Molt lifecycle state machine; open/closed molts, revert history | YAML state chart + ledger | Z2 ratifies transitions | Z1 read, Z2 write | ✅ EXISTS |
| **FRAMEWORK_MAPPING.md** | Maps 5 AI concepts → Z-roles, governance files, CI/CD gates | Markdown | Z2 ratification pending | Z1 read | ✅ EXISTS |

### Reference Docs (Z1 Reads; Z2 Ratifies Structure)

| File | Purpose | Format | Authority | R/W | Status |
|:-----|:--------|:-------|:----------|:----|:-------|
| **BOOT_PROCESS_MAP.md** | Maps session rituals (§A open, §B close) to resource states; halt conditions | Markdown stages + flowchart | Z2 ratifies design | Z1 read, Z2 write | 🔴 MISSING |
| **PLANNED_REPOS.md** | Roadmap (aspirational repos); resource budget per planned zone | YAML | Z2 ratifies roadmap | Z1 read, Z2 write | 🔴 MISSING |
| **GOVERNANCE_FILES.md** | This file; registry of all governance files | YAML table | Z2 ratifies definitions | Z1 read, Z2 write | 🟡 NEW |
| **CANDIDATE_BLOCK_TEMPLATE.md** | Template for Z1 proposals; falsifier, resource_cost, impact | Markdown + YAML example | Z2 ratifies template | Z1 read | 🟡 NEW |

### System State (Code Writes; Z1/Z2 Read)

| File | Purpose | Format | Authority | R/W | Status |
|:-----|:--------|:-------|:----------|:----|:-------|
| **NF_LEDGER.jsonl** | Append-only measurement ledger; every VERDICT/CYCLE/MEASURE event (hash-chained) | JSONL | Code append | Code write, All read | 🔴 MISSING |
| **system_graph.json** | Dependency topology; zones as nodes, inter-repo edges | JSON graph | Z2 (via blueprint) | Code write, All read | 🔴 MISSING |
| **MOLT_STATE.jsonl** | Molt measurement outcomes; one line per completed molt | JSONL | Code append | Code write, All read | 🔴 MISSING |
| **behavior_spec.json** | Z3 agent capability caps; tool limits, rate budgets, resource allocations | JSON | Z2 ratifies | Z1 read, Z2 write | 🔴 MISSING |

### Proposal Staging (Z1 Drafts; Z2 Ratifies)

| File | Purpose | Format | Authority | R/W | Status |
|:-----|:--------|:-------|:----------|:----|:-------|
| **z1-inbox/<date>/\*.md** | Candidate block drafts before REGISTERED.md submission | Markdown | Z1 author | Z1 write, Z2 read | 🟡 STRUCTURED |
| **z1-inbox/<date>/HANDOFF.md** | Session close summary; SHA pinned, findings, receipt walk-back, next blockers | Markdown | Z1 author | Z1 write, Z2 read | 🟡 STRUCTURED |

---

## File Dependencies & Boot Order

**§A (Session Open) — Read in this order:**

1. **CLAUDE.md** (first; establishes authority context)
2. **ZONE_REGISTRY.md** (verify repo is active; confirms caps)
3. **REGISTERED.md** (live-fetch at pinned SHA; proposals awaiting ratification)
4. **PRIORITY_QUEUE.md** (ranked by resource_impact; current work)
5. **MOLT_STATE.md** (open molts; state transitions)
6. **BOOT_PROCESS_MAP.md** (reference; session ritual mapping)

**§B (Session Close) — Write/Emit in this order:**

1. Walk claim vs. **NF_LEDGER.jsonl** (receipt reconciliation; B.6)
2. Emit receipt (claim → ledger entry)
3. Harvest F/IC/H candidates → **z1-inbox/<date>/HANDOFF.md**
4. Z2 ratifies findings (signs handoff, moves candidates to PRIORITY_QUEUE.md)

---

## Authorization Model (Resource-Based)

All Z2 writes require:
1. **SHA-256 hash** (falsifier_lint gate; candidate includes falsifier before submission)
2. **Resource cost estimate** (REGISTERED.md entry includes resource_cost field)
3. **Impact prediction** (PRIORITY_QUEUE.md entry scored by resource_impact, not deadline)
4. **Falsifier truth table** (required on hypotheses; tested at measurement time, not at arbitrary deadline)

**No time-based gates.** Only resource-capacity and regulatory compliance.

---

## Status Symbols

- ✅ EXISTS — file found; structure known
- 🔴 MISSING — referenced in CLAUDE.md or spec; not yet created
- 🟡 NEW — being created in this session
- 🟡 STRUCTURED — exists in z1-inbox/ but not centralized

---

## Next Steps

1. Create **REGISTERED.md** (YAML; candidates with resource_cost)
2. Create **PRIORITY_QUEUE.md** (YAML; ranked by resource_impact)
3. Create **ZONE_REGISTRY.md** (YAML; 31 repos, caps, executors)
4. Create **BOOT_PROCESS_MAP.md** (session rituals → resource states)
5. Create **PLANNED_REPOS.md** (roadmap; resource budgets)
6. Create **behavior_spec.json** (Z3 caps; resource allocations)
7. Create **NF_LEDGER.jsonl** (measurement log; hash-chain template)
8. Create **system_graph.json** (31 zones as nodes; dependencies as edges)

All resource-based; no deadlines except regulatory.
