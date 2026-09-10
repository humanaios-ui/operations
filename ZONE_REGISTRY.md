# ZONE_REGISTRY.md — Canonical Z1/Z2/Z3 Authority Map

**Location:** `operations/ZONE_REGISTRY.md` (canonical source)  
**Updated:** 2026-09-09  
**Authority:** Z2 (Night) — ratifies zone assignments and escalation paths  
**Enforcement:** CI gate validates every PR against this registry. Zone misalignment = merge block.

---

## Zone Model

| Zone | Role | Function | Authority | Output |
|:-----|:-----|:---------|:----------|:-------|
| **Z1** | Proposer | Read, analyze, propose changes. No direct execution. | Z1 team lead + Claude | Candidate blocks → REGISTERED.md (awaiting Z2 hash) |
| **Z2** | Ratifier | Accept/edit/reject proposals. SHA256 sign each decision. Enforce anti-cascade rules. | Night (Carly R. Anderson) — Admiral seat | RATIFY events, ratification hashes, constants versioned with molt_id |
| **Z3** | Executor | Land ratified changes to code, run experiments, emit VERDICT events. | Per-repo assignment (see table) | VERDICT events, Brier scores, receipts for B.6 reconciliation |

---

## Repository Zone Assignments (31 repos)

### **Tier 1: Governance Hubs**

| Repo | Primary | Secondary | Z1 Proposer Cap | Z2 Ratifier | Z3 Executor | Escalation |
|:-----|:--------|:----------|:---|:---|:---|:---|
| **operations** | Z2 gateway | Z3 for own gates | N/A (ops-only) | Night | Night | Admiral (Night) |
| **humanaios** | Z3 integration hub | Z2 escalation point | Full | Night | Integration lead (TBD) | Night |
| **humanaios-internal** | Z3 empirica umbrella | — | Full | Night | Empirica PM (TBD) | Night |

### **Tier 2: Practice Hubs**

| Repo | Primary | Secondary | Z1 Proposer Cap | Z2 Ratifier | Z3 Executor | Escalation |
|:-----|:--------|:----------|:---|:---|:---|:---|
| **empirica-autonomy** | Z1/Z2 builder + ratification | — | Agent configs, gate changes | Night | Engineering lead (TBD) | Night (gate), Admiral (constants) |
| **empirica-foundation-evaluator** | Z3 assessment seat | — | Rubric proposals only | Night | Admiral or delegated (TBD) | Admiral |
| **empirica-mesh-support** | Z2 coordination | Z1 proposal source | Mesh queries | Night | Integration (TBD) | Night |
| **empirica-outreach** | Z2 community governance | Z1 resource/content | Content proposals | Night | Community lead (TBD) | Night |
| **empirica-resource-miner** | Z0/Z1 discovery | — | Resource proposals (read-only extraction) | Night | None (read-only) | Night |
| **flta-app-empirica** | Z3 experiment runner | Z1 proposal source | Experiment params | Night | FLTA team (TBD) | Night |

### **Tier 3: Independent Verification**

| Repo | Primary | Secondary | Z1 Proposer Cap | Z2 Ratifier | Z3 Executor | Escalation |
|:-----|:--------|:----------|:---|:---|:---|:---|
| **acat-inspect** | Z1/Z3 independent replication | Z2 arbitration | ACAT designs, replication designs | Night | ACAT team (TBD) | Night |
| **lasting-light-ai** | Z1 research proposal | — | RQ1/RQ2/RQ3 methodology | Night | None (research only) | Admiral |

### **Tier 4: Public Channels & Experiments**

| Repo | Primary | Secondary | Z1 Proposer Cap | Z2 Ratifier | Z3 Executor | Escalation |
|:-----|:--------|:----------|:---|:---|:---|:---|
| **website** | Z1/Z3 public comms + deployment | — | Content (Z1), deployment (Z3) | Night | Web team (TBD) | Night |
| **grok-crossref** | Z1 research | — | Crossref API integration designs | Night | None (research only) | Admiral |
| **collaborator-ops** | Z3 collaboration platform | — | Ops & tooling | Night | Collaborator team (TBD) | Night |
| **local-machine-optimizer** | Z1 optimization research | — | Optimization strategies | Night | None (research only) | Admiral |
| **opportunity-aggregator** | Z3 data pipeline | Z1 proposal source | Feature proposals | Night | Data team (TBD) | Night |

### **Tier 5: Archive & Exploratory**

| Repo | Primary | Secondary | Z1 Proposer Cap | Z2 Ratifier | Z3 Executor | Escalation |
|:-----|:--------|:----------|:---|:---|:---|:---|
| **empirica-autonomy-archive** | Z0 archive | — | None (read-only) | Night | None | N/A |
| **empirica-opportunity-aggregator.archive** | Z0 archive | — | None (read-only) | Night | None | N/A |
| [Other archived repos] | Z0 | — | None (read-only) | Night | None | N/A |

---

## Authority Rules

### **Z1 Proposer Rights & Caps**

**Full cap** (can propose anything, needs Z2 hash):
- empirica-autonomy, humanaios, humanaios-internal, empirica-foundation-evaluator, empirica-mesh-support, empirica-outreach, acat-inspect

**Limited cap** (can propose only in scope):
- empirica-resource-miner: resource proposals only (read-only extraction)
- empirica-foundation-evaluator: rubric proposals only
- website: content proposals only
- lasting-light-ai, grok-crossref, local-machine-optimizer: methodology/research designs only
- opportunity-aggregator, flta-app-empirica: feature/parameter proposals only

**Read-only** (Z0, no proposals):
- Archive repos

### **Z2 Ratifier (Night) — Serial Gate**

**Process:**
1. Read Z1 candidate block (CI checks falsifier presence)
2. Accept, edit, or reject within 48h
3. Sign: `sha256(candidate | by=Night | at=timestamp | decision=ACCEPT|EDIT|REJECT)`
4. Emit RATIFY event → trigger CI gate → merge (if all proofs pass)

**Escalation:**
- IC beyond 48h → Admiral decision (Admiral = Night, may delegate)
- Tier 2 molt (node/edge change) → requires registry entry + ADV run before KEEP
- Disputed decision → request Z2 re-read + re-sign

### **Z3 Executor — Per-Repo**

**Assignments (TBD = awaiting Night's delegation):**
- **operations**: Night (Z2 self-executes governance)
- **humanaios**: Integration lead (TBD)
- **humanaios-internal**: Empirica PM (TBD)
- **empirica-autonomy**: Engineering lead (TBD)
- **empirica-foundation-evaluator**: Admiral or delegated (TBD)
- **empirica-mesh-support**: Integration (TBD)
- **empirica-outreach**: Community lead (TBD)
- **acat-inspect**: ACAT team (TBD)
- **website**: Web team (TBD)
- **flta-app-empirica**: FLTA team (TBD)
- **opportunity-aggregator**: Data team (TBD)
- **collaborator-ops**: Collaborator team (TBD)

**Execution workflow:**
1. Merge ratified PR (Z2 hash verified by CI)
2. Deploy to main or production per zone role
3. Run PRS/Agent/adversarial tests
4. Emit VERDICT/CYCLE/MEASURE events → NF_LEDGER
5. Send receipt (claim vs. tree walk-back) to Night for B.6 reconciliation

---

## Escalation Paths

**Standard escalation:** Z1 → Z2 (Night) → Admiral (Night) if 48h passes

**Time-sensitive decisions (< 24h needed):**
- Emergency security patches: Z2 may skip 48h window, document in RATIFY event
- Gate consistency failures: Z2 may revert to last known-good state, file IC-CAND

**Disputed decisions:**
- Z1 contests Z2 rejection → request re-read + documentation
- Z3 discovers Z2 assumption violated → emit GAUGE + request re-evaluation
- Both result in new candidate block; original rejection stands until re-signed

---

## Zone Transitioning Rules

**From Z1 to Z2:**
- Requires Z2 hash and IC-030 REGISTERED.md pin

**From Z2 to Z3:**
- Requires RATIFY event + CI gate pass (falsifier_lint, registry_consistency, molt_anti_cascade)

**From Z3 back to Z1 (on VERDICT failure):**
- VERDICT event → Findings Scan → F/IC candidate → Z2 decision

**Operator changes:**
- Reassignment of Z2 or Z3 requires Z2 ratification + ops-team announcement
- Night remains Z2 until explicitly reassigned by Admiral (self, or delegated)

---

## CI/CD Gate Integration

**CODEOWNERS rules:**

```yaml
# Global governance-adjacent changes
/REGISTERED.md operations-team
/PRIORITY_QUEUE.md operations-team
/ZONE_REGISTRY.md operations-team
/CLAUDE.md operations-team
/MOLT_STATE.md operations-team
/NF_LEDGER.jsonl operations-team
/system_graph.* operations-team

# Per-repo zone-specific
/src/** @zone-executor
/docs/GOVERNANCE.md @z2-ratifier
```

**Lint gates:**

| Gate | Check | Block? | Repair |
|:-----|:------|:-------|:--------|
| falsifier_lint | No H without falsifier | YES | Add falsifier_lint.py check to repo |
| z2_hash_verify | RATIFY hash present | YES | Z2 must re-sign |
| registry_consistency | Zone assignment matches ZONE_REGISTRY.md | YES | Sync zone in repo CLAUDE.md |
| molt_anti_cascade | Anti-cascade rules 1–5 enforced | YES | Emit IC-CAND if violated |

---

## Appended Events

```
2026-09-09 18:49 CST — Z2 (Night) ratified ORGANIZATION_BLUEPRINT_v1.md | ZONE_REGISTRY.md ratified | Phase 0 READY
2026-09-09 — Z1 created ZONE_REGISTRY.md from blueprint Q-Z-ASSIGNMENT-03 spec
```

