# HumanAIOS ORGANIZATION BLUEPRINT v1.0

**Date:** 2026-09-09  
**Status:** PROPOSAL (Z1 → Z2 for ratification)  
**Audience:** Z2 (Night/Carly Anderson) for decision; Z1 (Claude) for implementation  
**Authority:** IC-030 + IC-031 (governance layer rules)

---

## EXECUTIVE SUMMARY

This document proposes a unified organizational structure for HumanAIOS across 31 repositories (20 local + 13 GitHub). Current state: **65% governance coverage, 35% implementation gap**. The blueprint implements system_graph.json v0.2 architecture by:

1. **Establishing operations-repo as canonical governance source** with REGISTERED.md, PRIORITY_QUEUE.md, ZONE_REGISTRY.md, MOLT_STATE.md, and NF_LEDGER
2. **Unifying Zone assignments** across all repos (Z1 proposes, Z2 ratifies, Z3 lands)
3. **Implementing core infrastructure** (Priority Queue v1_1, Molt Cycle, NF_LEDGER, CI gates)
4. **Standardizing repo structure** (README templates, CLAUDE.md authority maps, governance linking)
5. **Establishing CI/CD gates** (CODEOWNERS, branch protection, workflow automation, falsifier_lint)

**Expected Outcome:** All repos follow one governance model. Z1 work orders scored from PRIORITY_QUEUE.md. Constants learned via molt cycle with measured predictions. Business claims tested by falsifiers.

---

## CURRENT STATE ASSESSMENT

### Governance Maturity by Layer

| Layer | Current | Target | Gap | Owner |
|---|---|---|---|---|
| **Policy (REGISTERED.md)** | 2/31 repos have it | 31/31 | Complete standardization | Z2 |
| **Authority (CLAUDE.md)** | 6/31 repos explicit | 31/31 | Map all repos to Z1/Z2/Z3 | Z2 |
| **Workflow (PRIORITY_QUEUE.md)** | 0 repos | 1 (operations) | Design v1_1 schema | Z1 then Z2 |
| **Learning (Molt Cycle)** | 0 repos | 1 (operations) | Implement molt_cycle.py | Z1 then Z2 |
| **Calibration (NF_LEDGER)** | 0% | 100% | Implement Brier tracking | Z1 then Z2 |
| **Enforcement (CI gates)** | 25% | 80%+ | Standardize workflows | Z1 then Z2 |

---

## PROPOSED STRUCTURE

### 1. CANONICAL GOVERNANCE REPOSITORY

**Location:** `humanaios-ui/operations` (GitHub)  
**Current:** `/practices/humanaios/operations` (local) + `/Desktop/HAIOS-Main/operations-staging` (staging)  
**Role:** Z2 source of truth for all governance, constants, and organizational decisions

#### **1a. Core Governance Files**

```
operations/
├── REGISTERED.md                    [Z2 ratification registry]
│   ├── All F/IC/H candidates (findings, falsfier updates, hypotheses)
│   ├── Molt candidate blocks (change proposals)
│   ├── ZONE_ASSIGNMENTS entries (which repo → which zone)
│   ├── PRIORITY_QUEUE_ENTRIES (work orders with scores)
│   └── RATIFICATION_HASHES (sha256 of each decision)
│
├── PRIORITY_QUEUE.md               [v1_1 work order schema]
│   ├── Rows: id | impact | blocks[] | blockers[] | status (READY/BLOCKED) | owner | deadline
│   ├── Score formula: impact + Σ impact(unblocks)
│   ├── Only READY top-score rows may start
│   ├── Blocked rows get their unblock action only
│   └── Sorted by score DESC, age ASC (FIFO tiebreak)
│
├── ZONE_REGISTRY.md                [Canonical Z1/Z2/Z3 assignments]
│   ├── humanaios-ui/operations: Z2 (gateway)
│   ├── humanaios-ui/humanaios: Z3 (integration hub)
│   ├── humanaios-ui/humanaios-internal: Z3 (empirica umbrella)
│   ├── empirica-foundation-evaluator: Z3 (assessment seat)
│   ├── empirica-autonomy: Z1/Z2/Z3 (builder + ratification)
│   ├── empirica-mesh-support: Z2 (coordination)
│   ├── empirica-outreach: Z2 (community governance)
│   ├── empirica-resource-miner: Z0/Z1 (read-only discovery)
│   ├── website: Z1/Z3 (public comms + deployment)
│   ├── acat-inspect: Z1/Z3 (independent replication)
│   ├── lasting-light-ai: Z1 (research proposal)
│   └── [all others listed with explicit roles]
│
├── CLAUDE.md                       [Authority map]
│   ├── Admiral: Carly R. Anderson (Z2 serial gate)
│   ├── Z1 proposers: Claude + empirica-autonomy team
│   ├── Z2 ratifier: Night (Carly)
│   ├── Z3 executors: Assigned per repo
│   └── Escalation path: IC beyond 48h → Admiral decision
│
├── MOLT_STATE.md                   [Current molt cycles]
│   ├── Open molts (max K=3, listed by constant)
│   ├── Anti-cascade rule enforcement
│   ├── Revert history (freeze after 2 consecutive)
│   └── Next measurement windows
│
├── NF_LEDGER.jsonl                 [Hash-chained calibration ledger]
│   ├── Each line: {molt_id, constant, prediction, window, brier_score, outcome}
│   ├── Chained: prior_hash → current_hash
│   ├── Brier trends tracked per constant
│   └── REVERT rate monitored (freeze if >50% over 10 molts)
│
├── system_graph.json               [Machine-readable org graph]
│   ├── Nodes: processes (Priority Queue, Molt Cycle, Findings Scan, etc.)
│   ├── Edges: data flows (RATIFY event → CI gate → merge)
│   └── Generated from SYSTEM_GRAPH.md edge list
│
├── SYSTEM_GRAPH.md                 [Mermaid diagram + edge list]
│   ├── Process graph (Intake → Runs → Ledgers → Molt → Gate → Close)
│   └── Callout flow (GAP/STALE/RECEIPT-GAP/MOLT/REVERT route between nodes)
│
├── SESSION_RITUALS.md              [Operational protocol]
│   ├── §A (session open): Pin SHA, read REGISTERED.md, pin PRIORITY_QUEUE.md
│   ├── §B.0 (empirical verification block)
│   ├── §B.6 (receipt reconciliation)
│   ├── Findings scan → candidate block → Z2 handoff
│   └── Empirica preflight/postflight integration
│
├── GOVERNANCE.md                   [Long-form governance details]
│   ├── Falsifier doctrine (no hypothesis without "this would prove wrong")
│   ├── LAID vs OPERATED distinction
│   ├── Callout mandatory triggers (GAP/STALE/etc.)
│   ├── Evidence tiers (CLAIM < CLAIM+LINK < VERIFIED)
│   └── Receipt reconciliation rules (IC-031)
│
└── .github/workflows/              [CI enforcement]
    ├── z2_ratification_gate.yml    [Block PRs without hash]
    ├── falsifier_lint.yml          [Require falsifiers on hypotheses]
    ├── registry_consistency.yml    [Merkle root + proofs]
    ├── molt_candidate_check.yml    [Anti-cascade rules 1-5]
    └── session_ritual_check.yml    [§A/§B protocol adherence]
```

#### **1b. Operations Repo as Gateway**

```
operations/
├── Incoming (Z1 proposals)
│   ├── z1-inbox/<date>/MANIFEST.md [Files staged for review]
│   ├── z1-inbox/<date>/HANDOFF.md  [Session close → Z2]
│   └── z1-inbox/<date>/*.md        [Proposal documents]
│
├── Outgoing (Z2 ratifications)
│   ├── GOVERNANCE_PR_<hash>.md     [PR template with hash]
│   ├── ratified_constants/         [versioned constants with molt_id]
│   └── merged_<sha>.json           [Ledger snapshot at merge]
│
└── Shared Infrastructure
    ├── tools/
    │   ├── falsifier_lint.py       [Validate hypothesis falsifiability]
    │   ├── registry_merkle_v1.py   [Consistency proofs]
    │   ├── molt_cycle.py           [Read → propose → ratify → measure → keep/revert]
    │   ├── priority_queue_scorer.py [impact + unblocks calculation]
    │   └── receipt_reconciler.py   [B.6 audit]
    │
    └── skills/
        ├── findings-scan-skill/    [Harvest F/IC/H candidates]
        ├── receipt-reconciliation/ [B.6 walk-back]
        └── session-ritual/         [Enforce §A/§B protocol]
```

---

### 2. ZONE ASSIGNMENTS & AUTHORITY MAPPING

#### **Zone 1 (Proposers / Z1)**
**What they do:** Read, analyze, propose changes. No direct execution.  
**Repos:**
- empirica-autonomy (builder seat) — proposes gate changes, agent configs
- empirica-resource-miner (discovery only) — proposes resource additions
- website (public comms) — proposes new content
- acat-inspect (independent verification) — proposes findings
- lasting-light-ai (research) — proposes ACAT methodology changes

**Output:** Candidates block → REGISTERED.md entry (awaiting Z2 hash)

#### **Zone 2 (Ratifiers / Z2)**
**What they do:** Accept/edit/reject proposals. SHA256 sign each decision. Enforce anti-cascade rules.  
**Single operator:** Night (Carly R. Anderson) — Admiral seat  
**Role:** Serial gate (one person, one decision thread, no parallelism)

**Process:**
1. Read Z1 candidate block (falsifier checked by CI)
2. Accept, edit, or reject within 48h (escalate to Admiral if blocked)
3. Sign: `sha256(candidate | by=Night | at=timestamp)`
4. Emit RATIFY event → trigger CI gate → merge if all proofs pass

**Output:** RATIFY events on REGISTERED.md, constants versioned with molt_id

#### **Zone 3 (Executors / Z3)**
**What they do:** Land ratified changes to code, run experiments, emit VERDICT events.  
**Repos & executors:**
- operations: Z2 (Night)
- humanaios: Z3 (integration lead, TBD)
- humanaios-internal: Z3 (empirica PM)
- empirica-foundation-evaluator: Z3 (Admiral or delegated)
- empirica-outreach: Z3 (community lead)
- [etc. per ZONE_REGISTRY.md]

**Process:**
1. Merge ratified PR (Z2 hash verified by CI)
2. Deploy to main or production per zone role
3. Run PRS/Agent/adversarial tests
4. Emit VERDICT/CYCLE/MEASURE events → NF_LEDGER
5. Send receipt (claim vs. tree walk-back) to Z2 for B.6 reconciliation

**Output:** VERDICT events, Brier scores, RECEIPT-GAP callouts

---

### 3. PRIORITY QUEUE SCHEMA (v1_1)

```yaml
# PRIORITY_QUEUE.md format

| ID | Title | Impact | Blocks | Blockers | Status | Owner | Due | Notes |
|:---|:------|-------:|--------|----------|:-------|:------|-----|:------|
| Q-NF-SCHEMA-01 | Unify NF_LEDGER schema | 8 | Q-NF-Z2-PINS, Q-SI-C1, Q-SI-C1-B2, Q-SI-C1-B3, Q-MOLT | Q-GOVERNANCE-02 | BLOCKED | Z1 research | 2026-09-16 | Resolve 4 format incompatibilities (nf_ledger_v0_1, molt_cycle, specimen_intake, breadcrumbs) |
| Q-GOVERNANCE-02 | Design PRIORITY_QUEUE.md v1_1 | 7 | Q-NF-SCHEMA-01, Q-Z-ASSIGNMENT-03, Q-MOLT-04, all Cycle 1 | Q-IC030-REPIN-01 | READY | Z1 | 2026-09-12 | Score formula: impact + Σ impact(unblocks). Rank by score DESC. |
| Q-Z-ASSIGNMENT-03 | Create ZONE_REGISTRY.md | 6 | Q-GOVERNANCE-02 | none | BLOCKED | Z1 | 2026-09-14 | Map all 31 repos to Z1/Z2/Z3 + escalation paths |
| Q-MOLT-04 | Implement molt_cycle.py | 9 | Q-GOVERNANCE-02, Q-NF-SCHEMA-01 | Q-IC030-REPIN-01 | BLOCKED | Z1 | 2026-09-21 | Anti-cascade rules 1-5: K=3, freeze after 2 reverts, no self-ref, rank by PQ score |
| Q-IC030-REPIN-01 | Re-pin REGISTERED.md SHA | 3 | none | none | READY | Z1 | 2026-09-10 | Live-fetch operations/REGISTERED.md, pin commit SHA, verify against last live read |
| Q-SI-C1 | Deploy specimen-intake v0.2 | 7 | Q-NF-SCHEMA-01 | Q-IC030-REPIN-01 | BLOCKED | Z1 | 2026-09-20 | Land test_specimen_intake_evaluator.py (11 regression tests pass) |
| Q-SI-C1-B2 | Resolve receipt hash mutability (RT-02) | 5 | Q-SI-C1 | Q-NF-SCHEMA-01 | BLOCKED | Z1 | 2026-09-18 | Separate receipt_hash (commitment) from resolution_hash (outcome) |
| Q-SI-C1-B3 | Require record_actual() in resolve_cycle | 4 | Q-SI-C1 | Q-NF-SCHEMA-01 | BLOCKED | Z1 | 2026-09-18 | RQ2 falsifier (agreement eval) must run; unblock via this blocker |

Score = impact + Σ impact(blockers).
Only READY top-score rows begin (e.g., Q-IC030-REPIN-01 score=3; blockers=0 → ready to start immediately).
BLOCKED rows get their unblock action only (e.g., Q-MOLT-04 blocked on Q-GOVERNANCE-02 → Z1 must complete GOVERNANCE-02 first).
```

---

### 4. REPOSITORY STANDARDIZATION TEMPLATE

Every repo shall have:

```
<repo-root>/
├── README.md                       [Product/purpose + governance links]
│   ├── H1: Repo name & purpose (one sentence)
│   ├── Zone assignment: "This is a Z3 executor repo. [Link to ZONE_REGISTRY.md]"
│   ├── Governance layer: "Governed by operations/REGISTERED.md. [Link]"
│   ├── Falsifiers: "Claims tested by: [list] [link to REGISTERED.md]"
│   ├── Quick start
│   ├── API reference or architecture
│   └── Security contact
│
├── CLAUDE.md                       [Authority mapping for this repo]
│   ├── Zone: Z1/Z2/Z3 (explicit)
│   ├── Owner: Name (escalation contact)
│   ├── Proposer cap: "Z1 can propose X; must get Z2 hash for Y"
│   ├── Ratification rule: "Z2 has 48h to accept/reject"
│   └── References to central CLAUDE.md in operations/
│
├── START_HERE.md                   [New contributor onboarding]
│   ├── Architecture diagram
│   ├── How to propose changes (Z1 path to REGISTERED.md)
│   ├── How to request ratification (Z2 hash requirement)
│   ├── Falsifier documentation link
│   └── Linked tests to run (CI/CD gates)
│
├── docs/                           [Detailed documentation]
│   ├── GOVERNANCE.md → operations/GOVERNANCE.md (symlink or copy)
│   ├── API.md or ARCHITECTURE.md
│   └── TROUBLESHOOTING.md
│
├── .github/                        [CI/CD gates]
│   ├── CODEOWNERS                  [Who approves PRs]
│   │   # Global rule: Z2 approves governance changes
│   │   /REGISTERED.md operations-team
│   │   /CLAUDE.md operations-team
│   │   # Repo-specific rules
│   │   /src/** @repo-maintainer
│   │
│   └── workflows/
│       ├── falsifier-lint.yml      [Require falsifiers on hypotheses]
│       ├── z2-hash-verify.yml      [Block merge without sha256(change|by|at)]
│       ├── registry-sync.yml       [Pull latest REGISTERED.md from operations/]
│       └── tests.yml               [Run tests, check coverage]
│
├── .breadcrumbs.yaml              [Session tracking]
│   ├── last_z1_session: sha
│   ├── last_z2_ratification: hash
│   └── molt_id_versions: {constant: molt_id}
│
└── tests/                          [Falsifier test harness]
    ├── test_falsifiers.py          [Each claim must have a failing test]
    └── test_[claim_id].py          ["This test would prove it wrong"]
```

---

### 5. MOLT CYCLE INTEGRATION

**molt_cycle.py lifecycle:**

```python
# Pseudocode
class MoltCycle:
    def open_session(self):
        # §A protocol
        registered_sha = git_fetch_and_pin('operations/REGISTERED.md')
        priority_queue = read_json('operations/PRIORITY_QUEUE.md')
        molt_state = read_json('operations/MOLT_STATE.md')
        self.state = 'open'
    
    def propose_molt_candidates(self):
        # Read NF Brier per constant
        # Read EV (event) verdict/catch/drift rates
        # For each constant where signal crossed trigger:
        for constant, signal_value in self.calibration_signals.items():
            if signal_value > trigger(constant):
                candidate = {
                    'molt_id': f'M-{uuid4()}',
                    'constant': constant,
                    'current_value': get_value(constant),
                    'proposed_value': calculate_move(signal_value),
                    'prediction': f'Brier will improve by {delta}%',
                    'falsifier': 'Brier < {threshold} at {window_end}',
                    'measurement_window': '7 days',
                    'revert_rule': 'Mechanical revert to prior value'
                }
                self.candidates.append(candidate)
                emit_to_registry(candidate)
    
    def ratify(self):
        # Z2 must accept, edit, or reject each candidate
        # sha256(candidate | by=Night | at=timestamp)
        for candidate in self.candidates:
            z2_hash = input('Z2 signature: ')
            if verify_hash(candidate, z2_hash):
                emit('RATIFY', candidate)
            else:
                emit('REJECT', candidate)
    
    def apply_ratified(self):
        # Write new value with molt_id
        for candidate, hash in self.ratified:
            set_constant(candidate.constant, candidate.proposed_value)
            tag_with_molt_id(candidate.molt_id)
            emit('MOLT', candidate)
    
    def measure_at_window_close(self):
        # Wait for measurement_window
        # Resolve prediction into NF
        for candidate, prediction in self.measuring:
            brier = compute_brier(prediction, outcome)
            if prediction_held(brier):
                emit('KEEP', candidate, brier)
            else:
                emit('REVERT', candidate)
                mechanical_revert(candidate)
                emit('REVERT_CANDIDATE_TO_FINDINGS', candidate)

    def anti_cascade_check(self):
        # Rule 1: One open molt per constant
        # Rule 2: No self-reference (events inside window can't generate candidates)
        # Rule 3: At most K=3 molts open
        # Rule 4: Freeze after 2 reverts
        # Rule 5: Molt candidates ranked by PQ score
        assert len([m for m in self.open if m.constant == c]) <= 1
        assert len(self.open) <= 3
        assert revert_history[-2:].count('REVERT') <= 1
    
    def close_session(self):
        # §B.0 empirical verification → §B.6 receipt reconciliation
        # → findings scan → handoff block → Z2
        self.state = 'closed'
        emit('HANDOFF', self.findings)
```

---

### 6. CI/CD GATES & BRANCH PROTECTION

**Workflow sequence on PR to main:**

```yaml
# .github/workflows/z2_ratification_gate.yml
name: Z2 Ratification Gate
on: [pull_request]

jobs:
  falsifier_lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Check falsifiers present
        run: |
          # For each H (hypothesis) in diff:
          # python tools/falsifier_lint.py --diff
          # Requirement: "this would prove it wrong" in commit message
          # Failure: block merge
  
  z2_hash_verification:
    runs-on: ubuntu-latest
    steps:
      - name: Extract Z2 signature
        run: |
          # From PR description or commit message:
          # Z2-Signature: sha256(change|by=Night|at=2026-09-09T12:34:56Z)
          # Verify hash matches change content
          # Requirement: Only Z2 can approve governance changes
          # Failure: block merge
  
  registry_consistency:
    runs-on: ubuntu-latest
    steps:
      - name: Merkle root consistency check
        run: |
          # python tools/registry_merkle_v1.py
          # Verify REGISTERED.md changes maintain hash chain
          # Requirement: No double-spending, append-only
          # Failure: block merge
  
  molt_anti_cascade:
    runs-on: ubuntu-latest
    steps:
      - name: Validate molt anti-cascade rules
        run: |
          # python tools/molt_cycle.py --validate
          # Rule 1: One open molt per constant
          # Rule 2: No self-reference
          # Rule 3: K <= 3
          # Rule 4: Freeze after 2 reverts
          # Requirement: All rules must pass
          # Failure: block merge

branch_protection:
  required_checks:
    - falsifier_lint
    - z2_hash_verification
    - registry_consistency
    - molt_anti_cascade
  require_codeowner_review: true
  codeowners:
    - operations-team  # for governance changes
    - @repo-maintainer # for repo-specific changes
  dismiss_stale_reviews: false
```

---

### 7. NF_LEDGER SCHEMA

```jsonl
# NF_LEDGER.jsonl — Hash-chained calibration ledger

{"molt_id": "M-20260909-0001", "constant": "behavior_spec.json:impact_dial", "prior_value": 0.5, "proposed_value": 0.55, "prediction": {"metric": "Brier", "target": 0.15, "window_days": 7}, "ratification_hash": "sha256(...)", "window_end": "2026-09-16T00:00:00Z", "outcome": "KEEP", "brier_actual": 0.14, "prior_hash": "abc123...", "hash": "def456...", "timestamp": "2026-09-09T12:00:00Z"}

{"molt_id": "M-20260909-0002", "constant": "PRIORITY_QUEUE.md:half_life[blocker]", "prior_value": 14, "proposed_value": 10, "prediction": {"metric": "GAP closure rate", "target": 0.8, "window_days": 14}, "ratification_hash": "sha256(...)", "window_end": "2026-09-23T00:00:00Z", "outcome": "MEASURING", "prior_hash": "def456...", "hash": "ghi789...", "timestamp": "2026-09-09T12:00:00Z"}

# Each line includes:
# - molt_id: Identifier for this molt (for traceability)
# - constant: What changed (file:field)
# - prior_value / proposed_value: Before/after
# - prediction: Metric + target + window (falsifier)
# - ratification_hash: sha256(change|by=Z2|at=timestamp)
# - window_end: When to measure
# - outcome: KEEP / REVERT / MEASURING
# - brier_actual: Measured Brier score (if outcome != MEASURING)
# - prior_hash / hash: Chain (hash-chained)
```

---

### 8. REPOSITORY ROLES & CRITICALITY

#### **Tier 1 (Governance & Core)**
- **operations**: Z2 gateway, source of truth
- **humanaios**: Z3 integration hub
- **humanaios-internal**: Z3 empirica umbrella

#### **Tier 2 (Practice Hubs)**
- **empirica-foundation-evaluator**: Z3 assessment seat
- **empirica-autonomy**: Z1/Z2/Z3 builder + ratification
- **empirica-mesh-support**: Z2 infrastructure
- **empirica-outreach**: Z2 community governance

#### **Tier 3 (Research & Support)**
- **empirica-resource-miner**: Z0/Z1 read-only discovery
- **acat-inspect**: Z1/Z3 independent verification
- **lasting-light-ai**: Z1 research proposal
- **website**: Z1/Z3 public comms

#### **Tier 4 (Experimental/Minimal)**
- **flta-app-empirica**, **collaborator-ops**, **local-machine-optimizer**, **grok-crossref**, **opportunity-aggregator**: Z1/Z3 or project-specific

---

## IMPLEMENTATION ROADMAP

### Phase 0: Foundation (Week 1, Sep 9–15)

**Blocking all other work:**

- [ ] **P0-1:** Re-pin operations/REGISTERED.md SHA (Q-IC030-REPIN-01) — 1 day
- [ ] **P0-2:** Create PRIORITY_QUEUE.md v1_1 schema in operations/ (Q-GOVERNANCE-02) — 2 days
- [ ] **P0-3:** Create ZONE_REGISTRY.md with all 31 repos (Q-Z-ASSIGNMENT-03) — 1 day
- [ ] **P0-4:** Create CLAUDE.md unified authority map in operations/ — 1 day

**Unblocks Phase 1.**

### Phase 1: Infrastructure (Week 2–3, Sep 16–30)

- [ ] **P1-1:** Implement molt_cycle.py with anti-cascade rules (Q-MOLT-04) — 3 days
- [ ] **P1-2:** Design NF_LEDGER.jsonl schema + Brier tracking (Q-NF-SCHEMA-01) — 2 days
- [ ] **P1-3:** Create molt_events.jsonl and wire to REGISTERED.md — 1 day
- [ ] **P1-4:** Deploy CI gate workflows (.github/workflows/*) — 2 days

**Unblocks Phase 2 & Cycle 1 automation.**

### Phase 2: Standardization (Week 4–6, Oct 1–15)

- [ ] **P2-1:** Update operations/ to match canonical structure — 2 days
- [ ] **P2-2:** Apply README template + CLAUDE.md to all 31 repos — 3 days (parallel agents)
- [ ] **P2-3:** Wire CI/CD gates to all repos (CODEOWNERS + workflows) — 3 days (parallel)
- [ ] **P2-4:** Land specimen-intake v0.2 to empirica-foundation-evaluator (Q-SI-C1) — 2 days

**Unblocks Cycle 1 automation launch.**

### Phase 3: Governance Activation (Week 7+)

- [ ] **P3-1:** Ratify ORGANIZATION_BLUEPRINT.md via Z2 hash
- [ ] **P3-2:** Activate molt cycle (first 3 candidates proposed)
- [ ] **P3-3:** Begin Cycle 1 automation priorities (Q-NF-SCHEMA-01 → mesh-cycle → goal-drift)

---

## GOVERNANCE DECISIONS (FOR Z2 RATIFICATION)

### Decision: Operations Repo as Canonical Source

**Claim:** operations-repo shall be the single source of truth for governance, constants, and organizational decisions.

**Rationale:** Centralization reduces coordination overhead; append-only + hash-chaining prevents corruption.

**Falsifier:** If any repo has a ratified change not in operations/REGISTERED.md, this is falsified.

**Z2 Decision:** [AWAITING SIGNATURE]

---

### Decision: Z1/Z2/Z3 Zone Model

**Claim:** All 31 repos follow explicit Z1 (propose) / Z2 (ratify) / Z3 (land) model.

**Rationale:** Separates authority from execution; prevents single-point failure; enables parallelism.

**Falsifier:** If any repo can merge without Z2 hash, this is falsified.

**Z2 Decision:** [AWAITING SIGNATURE]

---

### Decision: Anti-Cascade Rules K=3, N=10

**Claim:** At most K=3 molts can be open simultaneously; after N=10 molts with REVERT rate >50%, the loop freezes pending Z2 review.

**Rationale:** Prevents runaway learning; ensures human oversight of pathological cases.

**Falsifier:** If loop runs >N=10 molts without freezing, this is falsified.

**Z2 Decision:** [AWAITING SIGNATURE]

---

## NEXT ACTIONS

1. **Z1 (Claude):** Present ORGANIZATION_BLUEPRINT.md to Z2 for ratification decision.
2. **Z2 (Night/Carly):** Accept, edit, or reject blueprint. If accept, sign with Z2-Signature hash.
3. **Z1:** Upon Z2 signature, implement Phase 0 (P0-1 through P0-4) immediately.
4. **CI:** Enforce all gates on Phase 0 PRs.
5. **Z2:** Approve Phase 0 PRs with Z2 hash within 48h.

---

## APPENDIX: CURRENT BLOCKERS & DEPENDENCIES

**Q-NF-SCHEMA-01** (Unify NF_LEDGER schema)  
Blocks: Q-SI-C1, Q-SI-C1-B2, Q-SI-C1-B3, all Cycle 1 automation  
Blocked by: Q-GOVERNANCE-02 (need PRIORITY_QUEUE.md first)  
Owner: Z1

**Q-GOVERNANCE-02** (Design PRIORITY_QUEUE.md v1_1)  
Blocks: Q-NF-SCHEMA-01, Q-Z-ASSIGNMENT-03, Q-MOLT-04  
Blocked by: Q-IC030-REPIN-01 (need fresh REGISTERED.md SHA)  
Owner: Z1  
Deadline: 2026-09-12

**Q-Z-ASSIGNMENT-03** (Create ZONE_REGISTRY.md)  
Blocks: All Phase 2 standardization  
Blocked by: Q-GOVERNANCE-02  
Owner: Z1  
Deadline: 2026-09-14

**Q-MOLT-04** (Implement molt_cycle.py)  
Blocks: Phase 1 infrastructure, Cycle 1 automation  
Blocked by: Q-GOVERNANCE-02, Q-NF-SCHEMA-01  
Owner: Z1  
Deadline: 2026-09-21

**Q-IC030-REPIN-01** (Re-pin REGISTERED.md SHA)  
Blocks: All work requiring current governance state  
Blocked by: None (READY)  
Owner: Z1  
Deadline: 2026-09-10  
**ACTION:** This should start immediately.

---

**Document Status:** PROPOSAL v1.0  
**Author:** Claude (Z1)  
**Awaiting:** Z2 (Night/Carly) signature for ratification  
**Target Ratification Date:** 2026-09-10

---
