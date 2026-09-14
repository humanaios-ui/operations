# ZONE_REGISTRY.md — Canonical Z1/Z2/Z3 Authority Map

**Location:** `operations/ZONE_REGISTRY.md` (canonical source)  
**Updated:** 2026-09-14  
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

## Repository Zone Assignments (12 active repos)

### **Tier 1: Governance Hubs**

| Repo | Primary | Secondary | Z1 Proposer Cap | Z2 Ratifier | Z3 Executor | Escalation |
|:-----|:--------|:----------|:---|:---|:---|:---|
| **operations** | Z2 gateway | Z3 for own gates | N/A (ops-only) | Night | Night | Admiral (Night) |
| **humanaios** | Z3 integration hub | Z2 escalation point | Full | Night | Integration lead (TBD) | Night |
| **humanaios-internal** | Z3 empirica umbrella | — | Full | Night | Empirica PM (TBD) | Night |

### **Tier 2: ACAT & Verification**

| Repo | Primary | Secondary | Z1 Proposer Cap | Z2 Ratifier | Z3 Executor | Escalation |
|:-----|:--------|:----------|:---|:---|:---|:---|
| **acat-inspect** | Z1/Z3 independent replication | Z2 arbitration | ACAT designs, replication designs | Night | ACAT team (TBD) | Night |
| **acat-x** | Z1 proposal source | Z3 evaluation | ACAT designs | Night | ACAT team (TBD) | Night |
| **acat-dashboard** | Z3 dashboard | Z1 proposal | Dashboard features | Night | ACAT team (TBD) | Night |
| **acat-observatory** | Z3 observational data | Z1 analysis | Observatory schema | Night | ACAT team (TBD) | Night (private repo) |

### **Tier 3: Research & Analysis**

| Repo | Primary | Secondary | Z1 Proposer Cap | Z2 Ratifier | Z3 Executor | Escalation |
|:-----|:--------|:----------|:---|:---|:---|:---|
| **lasting-light-ai** | Z1 research proposal | — | RQ1/RQ2/RQ3 methodology | Night | None (research only) | Admiral |
| **research** | Z0 archive (frozen papers) | Z1 analysis | None (read-only papers) | Night | None (read-only) | Admiral |
| **empirica-practice-mesh** | Z2 coordination | Z1 proposal | Mesh queries, governance | Night | Empirica PM (TBD) | Night |

### **Tier 4: Public Channels & Documentation**

| Repo | Primary | Secondary | Z1 Proposer Cap | Z2 Ratifier | Z3 Executor | Escalation |
|:-----|:--------|:----------|:---|:---|:---|:---|
| **docs** | Z3 docs deployment | Z1 content | Documentation content | Night | Web team (TBD) | Night |
| **findlocaltattooartists** | Z3 portfolio | Z1 content | Portfolio content | Night | Web team (TBD) | Night |

---

## Authority Rules

### **Z1 Proposer Rights & Caps**

**Full cap** (can propose anything, needs Z2 hash):
- humanaios, humanaios-internal, acat-inspect, acat-x, empirica-practice-mesh

**Limited cap** (can propose only in scope):
- acat-dashboard: dashboard features only
- acat-observatory: observatory schema only
- lasting-light-ai: methodology/research designs only
- docs, findlocaltattooartists: content proposals only

**Read-only** (Z0, no proposals):
- research (frozen papers, archive)

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
- **acat-inspect**: ACAT team (TBD)
- **acat-x**: ACAT team (TBD)
- **acat-dashboard**: ACAT team (TBD)
- **acat-observatory**: ACAT team (TBD)
- **lasting-light-ai**: None (research only)
- **research**: None (read-only archive)
- **empirica-practice-mesh**: Empirica PM (TBD)
- **docs**: Web team (TBD)
- **findlocaltattooartists**: Web team (TBD)

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
# Example root CODEOWNERS excerpt only (non-active when `.github/CODEOWNERS` is present)
/document-registry.yaml                    @humanaios-ui/doc-control
/CONTROLLED_DOCUMENTS.md                    @humanaios-ui/doc-control
/.doc-control/                             @humanaios-ui/doc-control
/.github/workflows/document-control.yml    @humanaios-ui/doc-control
/GOVERNANCE.md                             @humanaios-ui/governance
/PRINCIPLES_SEED_V1_0.md                   @humanaios-ui/governance
/SEED.md                                   @humanaios-ui/governance
/REGISTERED.md                             @humanaios-ui/research
*.md                                       @humanaios-ui/doc-control
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
