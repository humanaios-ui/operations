# ZONE_REGISTRY.md — 31-Zone Ecosystem Map

**Purpose:** Authoritative registry of 31 HumanAIOS repositories (zones); executor assignments; resource caps  
**Authority:** Z2 ratifies zone list, executor assignments, and caps  
**Model:** Resource-based economy; each zone has resource budget (not time-based)  
**Updated:** 2026-09-14T00:00:00Z

---

## Active Zones (Full Proposal Cap)

| Zone ID | Repo Name | Purpose | Z3 Executor | Resource Cap | Status |
|:--------|:----------|:--------|:-----------|:-------------|:-------|
| Z-000 | operations | Governance coordination + REGISTERED.md | TBD | 80 units/cycle | ✅ ACTIVE |
| Z-001 | humanaios | Core platform | TBD | 100 units/cycle | ✅ ACTIVE |
| Z-002 | humanaios-internal | Internal tools | TBD | 80 units/cycle | ✅ ACTIVE |
| Z-003 | acat-inspect | Audit/inspection | TBD | 60 units/cycle | ✅ ACTIVE |
| Z-004 | acat-x | Extended auditing | TBD | 60 units/cycle | ✅ ACTIVE |
| Z-005 | acat-dashboard | Analytics dashboard | TBD | 50 units/cycle | ✅ ACTIVE |
| Z-006 | acat-observatory | System monitoring | TBD | 40 units/cycle | ✅ ACTIVE |
| Z-007 | empirica-practice-mesh | Empirica integration | TBD | 70 units/cycle | ✅ ACTIVE |

---

## Limited-Cap Zones (Scoped Proposals)

| Zone ID | Repo Name | Purpose | Proposal Cap | Z3 Executor | Resource Cap | Status |
|:--------|:----------|:--------|:-------------|:-----------|:-------------|:-------|
| Z-008 | lasting-light-ai | Research repo | RQ1/RQ2/RQ3 only | TBD | 30 units/cycle | ⚠️ LIMITED |
| Z-009 | docs | Documentation | Content only | TBD | 20 units/cycle | ⚠️ LIMITED |
| Z-010 | findlocaltattooartists | Service catalog | Content only | TBD | 25 units/cycle | ⚠️ LIMITED |

---

## Read-Only Zones (No Proposals)

| Zone ID | Repo Name | Purpose | Status |
|:--------|:----------|:--------|:-------|
| Z-011 | research | Frozen papers archive | 🔒 READ-ONLY |

---

## Planned Zones (Aspirational, 20 Repos TBD)

| Zone ID | Repo Name | Status | Roadmap Date | Notes |
|:--------|:----------|:--------|:-------------|:------|
| Z-012 | empirica-autonomy | PLANNED | TBD | Autonomy module |
| Z-013–Z-031 | (19 more repos) | PLANNED | See PLANNED_REPOS.md | TBD |

**Total active:** 12 zones (8 full-cap + 3 limited-cap + 1 read-only)  
**Total planned:** 20 zones  
**Total ecosystem:** 32 zones

---

## Resource Budget Model

Each zone has a **per-cycle resource budget** (measured in units, not time):

```
Example: Z-001 (humanaios) cap = 100 units/cycle

Each activity consumes units:
- Z1 proposal creation: 1-5 units (depends on complexity)
- Z2 ratification: 1-2 units (decision review)
- Z3 agent execution: 5-50 units (depends on agent cycles, tools used)

When 100 units consumed → zone halts work
No 48h deadline; no arbitrary window
Capacity refills on next cycle or when Z2 allocates
```

---

## Authority Matrix

| Action | Zone Type | Z1 | Z2 | Z3 | Authority |
|:-------|:----------|:----|:----|:----|:----------|
| Propose change | Active | ✅ | ✅ ratify | — | Z2 ratifies |
| Propose change | Limited | ✅ (scoped) | ✅ ratify | — | Z2 ratifies |
| Propose change | Read-only | ❌ | — | — | Frozen; no proposals |
| Execute change | Active | — | — | ✅ | Z2 assigns executor |
| Adjust cap | Any | ❌ | ✅ | — | Z2 only |
| Add zone | Any | — | ✅ | — | Z2 (updates registry) |

---

## Executor Assignments (TBD — Z2 Delegation)

Per CLAUDE.md §"Z3: Executors", Z2 (Night) delegates executor assignments per zone.  
Current status: **Pending Z2 decision** (see CLAUDE.md "many TBD pending Night's delegation").

Once assigned, each zone entry will include:
```yaml
z3_executor: "<GitHub username or team>"
escalation_contact: "<Email or Slack>"
handoff_schedule: "<When executor receives VERDICT/cycle results>"
```

---

## Next Steps (Z1 Research)

1. **Identify 20 planned repos** (Z-012–Z-031)
   - Search humanaios-ui GitHub org for all repos
   - Classify as: active, planned, archived, external
   
2. **Map executor names** (currently all TBD)
   - Verify Z2 (Night) delegation decisions
   - Document per zone
   
3. **Finalize resource caps**
   - Current caps are estimated; should be validated against historical spend
   - Adjust based on zone complexity

4. **Link to PLANNED_REPOS.md**
   - Aspirational repos tracked separately (roadmap)
   - Active repos stay in ZONE_REGISTRY.md

---

## Metadata

```yaml
metadata:
  total_active_zones: 12
  total_planned_zones: 20
  total_ecosystem: 32
  authority: "Z2 (Night)"
  model: "resource-based caps (not time-based deadlines)"
  format: "YAML table + registry"
  last_updated: "2026-09-14T00:00:00Z"
  executor_assignments: "PENDING Z2 DELEGATION"
```
