# CLAUDE.md — HumanAIOS Authority & Governance Reference

**Location:** `operations/CLAUDE.md` (canonical source)  
**Updated:** 2026-09-09  
**Purpose:** Unified authority map for all 31 HumanAIOS repositories  
**Audience:** Z1 (Claude, proposers), Z2 (Night, ratifier), Z3 (executors), CI/CD gates

---

## High-Level Authority Structure

```
┌─────────────────────────────────────────────────────────────┐
│ ADMIRAL: Carly R. Anderson (Night)                          │
│ Role: Z2 Serial Gate, Final Authority, Governance Arbiter   │
│ Contact: carly.r.anderson@gmail.com                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
   ┌────v────┐    ┌───v────┐   ┌────v─────┐
   │ Z1      │    │ Z2     │   │ Z3       │
   │Proposer │    │Ratifier│   │Executor  │
   └─────────┘    └────────┘   └──────────┘
   (Claude)       (Night)     (Per-repo)
```

---

## Authority Roles

### **Admiral (Z2 Serial Gate)**

**Name:** Carly R. Anderson (Night)  
**Title:** Founder, Z2 Ratifier, Serial Gate Authority  
**Email:** carly.r.anderson@gmail.com  
**Availability:** Standard business hours + on-call for emergencies  
**Decision window:** 48h for routine decisions; 24h or less for urgent items

**Responsibilities:**
- Accept/edit/reject all Z1 candidate blocks
- Sign ratification hashes for proposals, molts, constants, gate changes
- Enforce anti-cascade rules (K=3, freeze after 2 reverts)
- Re-read contested decisions
- Delegate Z3 executor assignments (per ZONE_REGISTRY.md)
- Escalate unresolved ICs to Admiral-only judgment (herself)

**Authority:**
- All tiers (Tier 0, 1, 2 decisions)
- Molt ratification (pinned prediction + window + falsifier)
- Constant changes (via molt)
- Zone assignment changes
- CI/CD gate adjustments

**Cannot do (by design):**
- Execute ratified changes (Z3 does that)
- Propose new work (Z1 does that)
- Override falsifier doctrine
- Change Z2 decision retroactively (only emit new RATIFY event with new hash)

---

### **Z1: Proposers**

**Primary:** Claude (AI agent)  
**Secondary:** Empirica practice teams (empirica-autonomy, etc.)  
**Authority:** Read, analyze, propose changes to REGISTERED.md

**Rights:**
- Propose candidate blocks (F/IC/H/MOLT candidates)
- Propose hypothesis, experiments, and methodologies
- Flag blockers and gaps in Priority Queue
- Request Z2 re-read of contested decisions (within 48h)
- Create working documents in z1-inbox/ (proposal staging)

**Caps by zone:**
- Full cap: empirica-autonomy, humanaios, humanaios-internal, empirica-foundation-evaluator, empirica-mesh-support, empirica-outreach, acat-inspect
- Limited cap: resource-miner (resources only), lasting-light-ai (RQ1/RQ2/RQ3), website (content), etc.
- Read-only: Archive repos

**Escalation path:** Z2 (Night) → Admiral (Night) if rejected or no decision in 48h

**Output:** Candidate blocks → REGISTERED.md (awaiting Z2 hash)

---

### **Z3: Executors**

**Role:** Land ratified changes, run experiments, emit VERDICT events  
**Assignment:** Per-repo (see ZONE_REGISTRY.md; many TBD pending Night's delegation)

**Rights (once ratified):**
- Merge PRs with Z2 hash + CI gate pass
- Deploy to main or production per zone role
- Run PRS/Agent/adversarial tests
- Emit VERDICT/CYCLE/MEASURE events
- Emit receipts for B.6 reconciliation
- Report GAUGE/STALE/DRIFT callouts back to Priority Queue

**Constraints:**
- Cannot execute without Z2 hash (CI enforces)
- Cannot bypass falsifier doctrine
- Cannot run beyond caps (agent caps in behavior_spec.json)
- Cannot overstate completion (IC-031 receipt reconciliation mitigation)

**Escalation path:** Z2 (Night) → Admiral (Night) if encountering Z2 assumption violation

**Output:** VERDICT events, Brier scores, receipts (claim vs. tree)

---

## Decision Routing

### **Routine Decisions (Z1 → Z2)**

**Process:**
1. Z1 reads REGISTERED.md (IC-030: live-fetch, pin SHA)
2. Z1 creates candidate block in z1-inbox/<date>/
3. Z1 includes falsifier (required by falsifier_lint.yml)
4. Z1 submits to Z2 via REGISTERED.md entry
5. Z2 reads candidate (within 48h)
6. Z2 signs: `sha256(candidate | by=Night | at=timestamp | decision=ACCEPT|EDIT|REJECT)`
7. If ACCEPT: CI gate merges; Z3 executes
8. If EDIT: Z2 proposes changes; Z1 revises; goto step 5
9. If REJECT: Z2 documents reason; Z1 may re-propose within 48h

### **Contested Decisions (Z2 → Admiral)**

**Trigger:** Z1 contests Z2 rejection within 48h, or 48h window closes without Z2 decision

**Process:**
1. Z1 requests re-read: "IC beyond 48h / Z2 decision contested" callout
2. Z2 (= Admiral) re-reads candidate + Z1 contest + context
3. Admiral signs new RATIFY event: `sha256(candidate | by=Night | at=timestamp | decision=ACCEPT|EDIT|REJECT | contest_response=<reason>)`
4. New decision stands (even if overturns prior)

### **Molt Decisions (Tier 1/2)**

**Z2 ratifies molts:**
1. Code proposes MOLT_CANDIDATE (read → signal → predict → falsifier)
2. Z2 reads prediction, window, revert rule, falsifier
3. Z2 signs: `sha256(molt_candidate | by=Night | at=timestamp | molt_id=<version>)`
4. Code applies ratified molt
5. Code measures at window close
6. Code keeps (prediction held) or reverts (falsifier tripped)
7. If revert: F/IC candidate filed; anti-cascade freeze rules apply

**Anti-cascade rules (enforced in molt_cycle.py):**
1. One open molt per constant; no new candidate inside window W
2. No candidate generated from events inside its own window (no self-reference)
3. At most K=3 molts open system-wide
4. Constant reverted twice in a row → frozen (Z2 Tier-2 ruling to reopen)
5. Molt candidates ranked by Priority Queue score (no bypassing)

---

## Governance Files & CI/CD Integration

### **Files That Require Z2 Signature**

| File | Authority | Change Trigger | Enforcement |
|:-----|:----------|:---|:---|
| REGISTERED.md | Z2 sole write | Any proposal/ratification | CI: no write without Z2 hash |
| PRIORITY_QUEUE.md | Z2 ratifies scores | Impact ±1+, status change, scope | CI: falsifier_lint + registry_consistency |
| ZONE_REGISTRY.md | Z2 ratifies zones | Zone assignment change | CI: zone validation vs repo CLAUDE.md |
| CLAUDE.md | Z2 ratifies authority | Authority/escalation change | CI: CODEOWNERS enforcement |
| MOLT_STATE.md | Z2 ratifies molts | Molt candidate → ratified | CI: anti-cascade lint |
| NF_LEDGER.jsonl | Code (append-only) | Measurement window close | CI: hash-chain validation |
| system_graph.json | Z2 (via blueprint) | Node/edge change | CI: consistency + regeneration lint |
| constants/*.json | Z2 (via molt) | Molt applied | CI: molt_id + prior version tracking |

### **CI/CD Gates**

**z2_ratification_gate.yml:**
- Falsifier present on hypotheses? YES → proceed; NO → block
- Z2 hash on RATIFY event? YES → proceed; NO → block
- Merkle root consistency? YES → proceed; NO → block
- Anti-cascade rules 1–5 enforced? YES → proceed; NO → block

**CODEOWNERS:**
```yaml
# Governance-adjacent (Z2 seal required)
/REGISTERED.md operations-team
/PRIORITY_QUEUE.md operations-team
/ZONE_REGISTRY.md operations-team
/CLAUDE.md operations-team
/MOLT_STATE.md operations-team
/NF_LEDGER.jsonl operations-team
/system_graph.* operations-team

# Zone-specific (Z3 executor + Z2 approval)
/src/** @zone-executor
/docs/GOVERNANCE.md @z2-ratifier
/tests/** @zone-executor
```

---

## Session Rituals (§A / §B)

### **§A: Session Open**

**Mandatory before any work:**
1. `git fetch && git rev-parse HEAD` — pin SHA
2. Read `REGISTERED.md` at that SHA (IC-030: live-fetch, pin)
3. Read `PRIORITY_QUEUE.md` (or queue patch in z1-inbox/*)
4. Verify each file's sha256 against manifest
5. State position · destination · probability

**Example:**
```
Position: REGISTERED.md pinned at abc123def456.
Destination: Implement Q-IC030-REPIN-01 (re-pin REGISTERED.md) and Q-GOVERNANCE-02 (create PRIORITY_QUEUE.md).
Probability: 85% Phase 0 complete by 2026-09-15 if Z2 ratification obtained.
```

### **§B: Session Close**

**B.0: Empirical Verification Block**
- Code ran? If no, close refused.
- Prereg hash verified in REGISTERED.md? If no, close refused.

**B.6: Receipt Reconciliation**
- Walk claim vs. tree (every statement in transcript)
- Generate receipt (claim → matched ledger entry)
- Report RECEIPT-GAP (claim not in tree) → Priority Queue
- Z2 confirms or flags discrepancy

**Findings Scan**
- Harvest F/IC/H candidates from events, molt ledger, RECEIPT-GAP callouts
- Emit candidate blocks → REGISTERED.md
- Z2 ratifies or contests

**Handoff Block**
- Write z1-inbox/<date>/HANDOFF.md
- Include pinned SHA, findings, receipt walk-back, next blockers
- Z2 signs handoff (ratifies findings and next priority)

---

## Callout Mandatory Triggers

When these occur, emit callout immediately:

| Callout | Trigger | Route | Z2 Response |
|:--------|:--------|:------|:-----------|
| **GAP** | Blocked row in Priority Queue without unblock action | Q | Accept/edit/reject unblock |
| **STALE** | Constant unchanged >half-life (set per constant) | Q + MOLT | Re-read constant or retire |
| **RECEIPT-GAP** | Claim in transcript not found in tree | Q + FS | Verify or file IC-CAND |
| **GAUGE** | Z3 reports Z2 assumption violated in field | Q + OM | Re-evaluate context |
| **AMBIGUITY** | Two Z2 decisions conflict on same topic | FS | Clarify or amend prior |
| **VOID** | Experiment runs but all outcomes null/unevaluable | FS | Falsify or retire claim |
| **DRIFT** | Behavior dial changed; reply score vs dial | Q | Adjust dial or update dials |
| **DISPUTED** | Z1 or Z3 contests Z2 decision | Z2 + FS | Re-read and re-sign |
| **MOLT** | Molt candidate proposed | Z2 | Ratify, edit, or reject |
| **REVERT** | Molt falsifier tripped; constant reverted | FS + Q | File F/IC candidate; rank in Q |

---

## Appended Events

```
2026-09-10 22:13 UTC — Z1 proposed Q-FRAMEWORK-MAPPING-01 (FRAMEWORK_MAPPING.md: 5 AI engineering concepts → Z-roles)
2026-09-10 22:17 UTC — PR #264 merged (FRAMEWORK_MAPPING.md content); awaiting Z2 RATIFY signature for Q-FRAMEWORK-MAPPING-01
2026-09-09 18:49 CST — Z2 (Night) ratified ORGANIZATION_BLUEPRINT_v1.md | CLAUDE.md ratified | Phase 0 READY
2026-09-09 — Z1 created CLAUDE.md from blueprint authority map spec
```

---

## How to Use This Document

**For proposers (Z1):** Read "Z1: Proposers" section. Know your cap. File candidate blocks. Wait for Z2 signature.

**For ratifier (Z2/Night):** Read "Admiral" + "Decision Routing" sections. Watch for 48h windows. Document all decisions as RATIFY events.

**For executors (Z3):** Read "Z3: Executors" section. Merge only with Z2 hash. Emit VERDICT/CYCLE events. Send receipts.

**For CI/CD:** Use CODEOWNERS rules. Run falsifier_lint, z2_hash_verify, registry_consistency, molt_anti_cascade gates.

**Per-repo CLAUDE.md files** should link to this document as authoritative and state repo-specific constraints (zone, proposer cap, executor assignment, escalation).

**Framework Reference:** See [`FRAMEWORK_MAPPING.md`](./FRAMEWORK_MAPPING.md) for unified mental model mapping 5 Modern AI Engineering Concepts (Graph, Loop, Context, Harness, Prompt Engineering) to HumanAIOS Z-roles, governance files, and CI/CD gates. All proposers, ratifiers, and executors should reference this mapping when designing or evaluating work across the 31-repo ecosystem.

