# Q-RBE-OPS-TIER-RANKING-01 — Benefit/Cost Density Ranking Within Tiers

**Created:** 2026-10-01 00:15 UTC  
**Authority:** Z1 (Claude) allocation proposal — awaiting Z2 ratification  
**Scope:** Rank all 90 tier-assigned candidates by benefit/cost density within Tier 0/1/2  
**Framework:** Resource-based allocation model (RBE-OPS) per PRIORITY_QUEUE.md + priority_queue_engine.py  
**Prerequisite:** Q-TIER-ASSIGNMENT-BATCH-01 (Z2-ratified 2026-09-30)

---

## Executive Summary

Q-TIER-ASSIGNMENT-BATCH-01 established tier membership for all 90 awaiting_z2 candidates. This document applies RBE-OPS benefit/cost density ranking within each tier to establish execution order.

**Ranking Model:**
- **Benefit:** Infrastructure unblocked + direct impact score (extracted from tier assignment document)
- **Cost:** Resource consumption in RAT-min (primary constraint per PRIORITY_QUEUE.md molt_id f7a49f667c09f1f6)
- **Density:** benefit ÷ cost (high density first)
- **Banding:** Tier 0 is entirely Band A (cost=0, rank by benefit). Tier 1/2 split Band A and Band B.

**Distribution:**
- **Tier 0 (Band A — all zero-cost):** 14 candidates, ranked by benefit
- **Tier 1 (Band A + B):** 46 candidates, Band A by benefit, Band B by density
- **Tier 2 (Band A + B):** 30 candidates, Band A by benefit, Band B by density
- **Total:** 90 ranked candidates

---

## Tier 0 — Critical Infrastructure (Ranked by Benefit)

All Tier 0 candidates cost zero RAT-min (Band A); ranked by infrastructure impact (benefit):

| Rank | Candidate | Title | Benefit | Cost | Density | Unblocks |
|:-----|:----------|:------|:-------:|:----:|:-------:|:---------|
| 1 | **Q-GOVGATE-01** | Z2 gate + z1-inbox conversion | 10 | 0 | ∞ | All Z2 ratification workflow |
| 2 | **Q-RFM-01** | REGISTERED.md failure-mode map | 9 | 0 | ∞ | Registry validation, measurement |
| 3 | **Q-NF-SCHEMA-01** | Unify NF_LEDGER schema | 9 | 0 | ∞ | Molt cycle, hypothesis tracking |
| 4 | **Q-NF-ADAPTER-01** | molt_cycle.py integration | 9 | 0 | ∞ | Real NF ledger execution |
| 5 | **Q-RBE-01** | Resource-based operations v0.1 | 9 | 0 | ∞ | Resource-based prioritization |
| 6 | **Q-FRAMEWORK-MAPPING-01** | 5 AI concepts → Z-roles | 8 | 0 | ∞ | Governance framework (all 31 repos) |
| 7 | **Q-FRAMEWORK-MAPPING-INTEGRATION-01** | Framework across 31 repos | 8 | 0 | ∞ | Z-role enforcement ecosystem-wide |
| 8 | **Q-PHASE1-2-ROLLOUT-01** | Framework rollout phases 1–3 | 8 | 0 | ∞ | Phase orchestration |
| 9 | **Q-INTENT-OS-WITNESS-LEDGER-01** | Human-machine attribution ledger | 8 | 0 | ∞ | Actor provenance tracking |
| 10 | **Q-TOOL-MANIFEST-DRIFT-PREVENTION-01** | Tool manifest validation gate | 7 | 0 | ∞ | System control plane |
| 11 | **Q-MOLT-TEMPORAL-PURITY-01** | Molt closure semantics | 7 | 0 | ∞ | Molt window correctness |
| 12 | **Q-GATE-PATHS-TEST-LOGIC-01** | Gate logic classification | 7 | 0 | ∞ | Tier semantics foundation |
| 13 | **Q-WITNESS-LEDGER-TIER0-EXTENSION-01** | Witness ledger Tier 0 actor class | 7 | 0 | ∞ | Actor model completeness |
| 14 | **Q-588-CONVERGENCE-MATRIX-01** | Resource System convergence | 8 | 0 | ∞ | Composition-vs-substrate decision |

**Execution note:** Tier 0 is unblocked; execute in benefit order (items 1–5 first, then 6–14 in parallel where dependencies permit).

---

## Tier 1 — Major Features (Ranked by Band A, then Density)

Band A (zero cost) items ranked by benefit; Band B items by density within their subcategory.

### Tier 1, Band A (Zero-Cost / Infrastructure Foundation)

| Rank | Candidate | Title | Benefit | Cost | Density | Category |
|:-----|:----------|:------|:-------:|:----:|:-------:|:---------|
| 1 | **Q-TOOLCONTROL-01** | Tool manifest & registry | 8 | 0 | ∞ | Tool Control (Band A) |
| 2 | **Q-ACAT-BENCHMARK-01** | ACAT ↔ market-benchmark map | 7 | 0 | ∞ | ACAT Ecosystem (Band A) |
| 3 | **Q-REGISTRY-AUDIT-02** | Register 7 active missing repos | 7 | 0 | ∞ | Registry Audit (Band A) |

### Tier 1, Band B (Non-Zero Cost / Ranked by Density)

Categorized by implementation domain; sorted by density within each domain:

#### Tool Control Automation (3 candidates, Band B)

| Rank | Candidate | Title | Benefit | Cost | Density | Notes |
|:-----|:----------|:------|:-------:|:----:|:-------:|:------|
| 4 | **Q-TOOLCONTROL-02** | Tool category vocabulary | 7 | 5 | 1.40 | Moderate cost; enables control taxonomies |
| 5 | **Q-TOOLCONTROL-03** | Gate self-testing | 6 | 6 | 1.00 | Moderate cost; validates gate infrastructure |
| 6 | **Q-DOC-LIFECYCLE-01** | docs/ lifecycle (108 files) | 8 | 10 | 0.80 | Higher cost; documentation governance |

#### ACAT Ecosystem (13 candidates, Band B)

| Rank | Candidate | Title | Benefit | Cost | Density | Notes |
|:-----|:----------|:------|:-------:|:----:|:-------:|:------|
| 7 | **Q-ACAT-DISTRIBUTION-PLAYS-01** | ACAT distribution playbook | 7 | 3 | 2.33 | Low cost; high external reuse |
| 8 | **Q-AGENT-CHECKIN-CALIBRATION-01** | Calibration at check-in | 8 | 5 | 1.60 | Closes H-ACAT gap |
| 9 | **Q-CGBG-PILOT-01** | CGBG Pilot adversarial review | 8 | 7 | 1.14 | Research capacity offer validation |
| 10 | **Q-BOOT-STATE-MACHINE-01** | Boot state machine hardening | 7 | 8 | 0.88 | Moderate cost; 17 findings |
| 11 | **Q-CGBG-BASELINE-01** | CGBG market baseline review | 7 | 7 | 1.00 | Market validation |
| 12 | **Q-ADVREVIEW-CALIB-01** | Adversarial review as CI node | 6 | 6 | 1.00 | CI integration |
| 13 | **Q-GRAPH-CONVERGENCE-01** | Graph agreement scoring | 6 | 5 | 1.20 | Graph grading improvement |
| 14 | **Q-INTENT-GRAPH-01** | Intent substrate (typed graph) | 7 | 8 | 0.88 | Intent grounding foundation |
| 15 | **Q-BOOT-FINDINGS-SCAN-01** | Boot integration findings | 7 | 6 | 1.17 | Post-merge validation |
| 16 | **Q-SMAG-CALIBRATION-SCHEMA-CONFORMANCE-01** | Schema enforcement | 6 | 4 | 1.50 | Calibration data integrity |
| 17 | **Q-SMAG-Z3-TASK-SEQUENCING-01** | Z3 task sequencing | 8 | 6 | 1.33 | High benefit; enables Z3 execution |
| 18 | **Q-DATA-SSOT-REGENERATION-01** | Data SSOT regeneration | 6 | 5 | 1.20 | Data integrity post-contamination |
| 19 | **Q-SA-WINDOW-DESIGN-E-PLUS-A-01** | Self-Assessment Window (E+A) | 6 | 7 | 0.86 | Self-assessment framework |

#### Registry Audit/Reconciliation (2 candidates, Band B)

| Rank | Candidate | Title | Benefit | Cost | Density | Notes |
|:-----|:----------|:------|:-------:|:----:|:-------:|:------|
| 20 | **Q-REGISTRY-AUDIT-01** | Classify 13 missing repos | 6 | 2 | 3.00 | High density; low cost |
| 21 | **Q-REGISTRY-AUDIT-03** | Registry CI gate implementation | 7 | 5 | 1.40 | Moderate cost; enforces registry |

#### Intent-OS Core Capabilities (5 candidates, Band B)

| Rank | Candidate | Title | Benefit | Cost | Density | Notes |
|:-----|:----------|:------|:-------:|:----:|:-------:|:------|
| 22 | **Q-PHASE-2-CI-CONSOLIDATION-ROADMAP-01** | CI/CD consolidation roadmap | 8 | 2 | 4.00 | Highest density in Tier 1; strategic guidance |
| 23 | **Q-BOARD-PUBLISH-01** | Board surface (Cloudflare) | 8 | 6 | 1.33 | Production surface delivery |
| 24 | **Q-INTENTOS-REFRESH-01** | Automated Intent-OS refresh | 8 | 10 | 0.80 | High cost; automation benefit |
| 25 | **Q-INTENTOS-BUS-01** | Agent bus policy | 8 | 10 | 0.80 | High cost; bus infrastructure |
| 26 | **Q-PHASE-2-BOARD-MOLT-01** | Board decision ingestion | 7 | 5 | 1.40 | Decision tracking |

#### Board Rulings — Core Decisions (12 candidates, Band B)

| Rank | Candidate | Title | Benefit | Cost | Density | Notes |
|:-----|:----------|:------|:-------:|:----:|:-------:|:------|
| 27 | **Q-BOARD-RULING-03** | d3 — z2_budget_p2 | 7 | 2 | 3.50 | Phase 2 envelope |
| 28 | **Q-BOARD-RULING-05** | d5 — audit/falsifier rules | 7 | 3 | 2.33 | Policy foundation |
| 29 | **Q-BOARD-RULING-06** | d6 — miner timeout SLA | 6 | 3 | 2.00 | SLA definition |
| 30 | **Q-BOARD-RULING-07** | d7 — resource decay function | 7 | 4 | 1.75 | Resource accounting |
| 31 | **Q-BOARD-RULING-08** | d8 — allocation bands | 7 | 3 | 2.33 | Allocation framework |
| 32 | **Q-BOARD-RULING-09** | d9 — phase 2 deferral list | 6 | 2 | 3.00 | Roadmap prioritization |
| 33 | **Q-BOARD-RULING-10** | d10 — tooling commitment | 6 | 4 | 1.50 | Tool stack |
| 34 | **Q-BOARD-RULING-11** | d11 — artifact witness | 6 | 3 | 2.00 | Artifact provenance |
| 35 | **Q-BOARD-RULING-12** | d12 — evidence ledger | 7 | 5 | 1.40 | Evidentiary record |
| 36 | **Q-BOARD-RULING-13** | d13 — dispatch loop | 6 | 4 | 1.50 | Event loop |
| 37 | **Q-BOARD-RULING-15** | d15 — user attribution | 6 | 3 | 2.00 | Attribution semantics |
| 38 | **Q-BOARD-RULING-16** | d16 — concurrent writes | 6 | 5 | 1.20 | Concurrency model |

#### Documentation (2 candidates, Band B)

| Rank | Candidate | Title | Benefit | Cost | Density | Notes |
|:-----|:----------|:------|:-------:|:----:|:-------:|:------|
| 39 | **Q-DOCREVIEW-01** | Lifecycle for 39 overdue reviews | 6 | 5 | 1.20 | Review workflow |
| 40 | **Q-DOCREVIEW-02** | First review pass findings | 6 | 4 | 1.50 | Findings implementation |

#### IC Board Decisions (3 candidates, Band B)

| Rank | Candidate | Title | Benefit | Cost | Density | Notes |
|:-----|:----------|:------|:-------:|:----:|:-------:|:------|
| 41 | **Q-IC-BOARD-SEALS-01** | Board decision seals | 7 | 4 | 1.75 | Decision authentication |
| 42 | **Q-IC-RATIFY-BYPASS-01** | Ratification bypass rules | 6 | 5 | 1.20 | Governance override |
| 43 | **Q-Z2RATIF-MECH-32** | Z2 Ratification Mechanism 32 | 5 | 6 | 0.83 | Specific mechanism |

#### Mesh Governance (3 candidates, Band B)

| Rank | Candidate | Title | Benefit | Cost | Density | Notes |
|:-----|:----------|:------|:-------:|:----:|:-------:|:------|
| 44 | **Q-MESH-LOCAL-COORDINATION-01** | Mesh local coordination | 6 | 7 | 0.86 | Coordination protocols |
| 45 | **Q-ACCOUNT-HUB-01** | Account hub infrastructure | 6 | 8 | 0.75 | Centralized account mgmt |
| 46 | **Q-BUZZ-COLLAB-EVAL-01** | Buzz collaboration evaluation | 5 | 6 | 0.83 | Feature evaluation |

---

## Tier 2 — Refinement & Optimization (Ranked by Band A, then Density)

### Tier 2, Band A (Zero-Cost / Foundational Refinements)

| Rank | Candidate | Title | Benefit | Cost | Density | Category |
|:-----|:----------|:------|:-------:|:----:|:-------:|:---------|
| 1 | **Q-GOVDRIFT-01** | Governance drift detection | 6 | 0 | ∞ | Refinement (Zero-cost) |

### Tier 2, Band B (Non-Zero Cost / Ranked by Density)

#### Extended Board Rulings (10 candidates, Band B)

| Rank | Candidate | Title | Benefit | Cost | Density | Notes |
|:-----|:----------|:------|:-------:|:----:|:-------:|:------|
| 2 | **Q-BOARD-RULING-26** | d26 — resource-based grounding | 5 | 4 | 1.25 | Refinement decision |
| 3 | **Q-BOARD-RULING-27** | d27 — model endpoint policy | 5 | 4 | 1.25 | Bus policy |
| 4 | **Q-BOARD-RULING-28** | d28 — issue mirror for REQ | 5 | 3 | 1.67 | Record mirroring |
| 5 | **Q-BOARD-RULING-29** | d29 — smoke contract | 5 | 3 | 1.67 | Contract definition |
| 6 | **Q-BOARD-RULING-30** | d30 — squash-merge pointer | 5 | 2 | 2.50 | Merge strategy |
| 7 | **Q-BOARD-RULING-32** | d32 — KNOWN_RED list | 5 | 2 | 2.50 | Maintenance list |
| 8 | **Q-BOARD-RULING-33** | d33 — board filename rename | 4 | 1 | 4.00 | Highest density in extended rulings |
| 9 | **Q-Z2-PHASE-2A-INTERROGATION-COMPLETE-01** | Phase 2a interrogation approvals | 6 | 5 | 1.20 | Design E/A ratification |
| 10 | **Q-BOARD-RULING-20** — **Q-BOARD-RULING-25** | Board rulings d20–d25 (6 decisions) | 5–6 | 3–4 | 1.3–2.0 | See detailed breakdown below |
| 11 | **Q-Z2-BLOCK-UNFILLABLE-01** | Z2 block on unfillable items | 5 | 4 | 1.25 | Priority management |

#### Strategy & Analysis (6 candidates, Band B)

| Rank | Candidate | Title | Benefit | Cost | Density | Notes |
|:-----|:----------|:------|:-------:|:----:|:-------:|:------|
| 12 | **Q-PROCESS-PRODUCT-RATIO-01** | Process/product optimization | 7 | 10 | 0.70 | Process redesign (high cost) |
| 13 | **Q-CRB-COMPILE-01** | Compile runtime bits | 5 | 5 | 1.00 | Artifact compilation |
| 14 | **Q-SEED-TRL-PROPAGATION-01** | TRL correction propagation | 4 | 2 | 2.00 | Data consistency |
| 15 | **Q-CORPUS-STATS-RECONCILE-01** | Corpus audit reconciliation | 4 | 2 | 2.00 | July corpus unresolved |
| 16 | **Q-LEDGER-GROUNDING-STUB-01** | Remove LedgerProvider stub | 4 | 1 | 4.00 | High density; stub removal |
| 17 | **Q-GATE-BYPASS-LEDGER-01** | Bypass gate audit trail | 5 | 3 | 1.67 | Governance audit |

---

## Execution Constraints

**Within Tier 0:** All candidates are ready; execute in benefit order (items 1–5 have highest impact; 6–14 in parallel).

**Within Tier 1:** Execute Band A (3 candidates) before Band B. Band B items are ranked by density; execute in order where cost constraints permit. Highest-density items (Q-PHASE-2-CI-CONSOLIDATION-ROADMAP-01, Q-REGISTRY-AUDIT-01) should execute before lower-density items (Q-INTENTOS-REFRESH-01, Q-INTENTOS-BUS-01) if capacity is limited.

**Within Tier 2:** Q-GOVDRIFT-01 is zero-cost (Band A); execute first. Then execute Band B in density order, prioritizing high-density items (Q-BOARD-RULING-33, Q-LEDGER-GROUNDING-STUB-01) before low-density items (Q-PROCESS-PRODUCT-RATIO-01).

**Tier blocking:** No inter-tier execution until Tier 0 is substantially complete (items 1–5 fully done, 6–14 unblocking downstream work).

---

## Densest Candidates Across All Tiers (Top 10 by Density)

For rapid execution under capacity constraints, these highest-density items should prioritize:

| Rank | Tier | Candidate | Density | Benefit | Cost |
|:-----|:-----|:----------|:-------:|:-------:|:----:|
| 1 | Tier 0 | **Q-GOVGATE-01** | ∞ | 10 | 0 |
| 2 | Tier 0 | **Q-RFM-01** | ∞ | 9 | 0 |
| 3 | Tier 0 | **Q-NF-SCHEMA-01** | ∞ | 9 | 0 |
| 4 | Tier 0 | **Q-NF-ADAPTER-01** | ∞ | 9 | 0 |
| 5 | Tier 0 | **Q-RBE-01** | ∞ | 9 | 0 |
| 6 | Tier 1 | **Q-PHASE-2-CI-CONSOLIDATION-ROADMAP-01** | 4.00 | 8 | 2 |
| 7 | Tier 2 | **Q-BOARD-RULING-33** | 4.00 | 4 | 1 |
| 8 | Tier 2 | **Q-LEDGER-GROUNDING-STUB-01** | 4.00 | 4 | 1 |
| 9 | Tier 1 | **Q-REGISTRY-AUDIT-01** | 3.00 | 6 | 2 |
| 10 | Tier 1 | **Q-BOARD-RULING-03** | 3.50 | 7 | 2 |

---

## Falsifier

**This ranking will be proven wrong if:**

1. A candidate classified as zero-cost (Band A) requires resources exceeding Band A capacity
2. Density ranking within a tier produces an execution order that violates an unstated dependency (A must complete before B, but ranking orders B before A)
3. A Tier 1 candidate unblocks a Tier 0 candidate (tier membership reversed)
4. Execution following this ranking order exhausts available capacity before completing any Tier 0 candidate
5. A candidate's benefit estimate is off by 3+ points (confidence collapse below 50%)

**Confirmation events:**

- Tier 0 candidates execute in density order without re-ranking within-tier
- Tier 1 and Tier 2 density rankings produce zero conflicts with actual execution dependencies
- RBE-OPS priority_queue_engine.py ranks candidates identically when given benefit/cost data extracted from this document
- Z3 executor assignments follow tier order: Tier 0 completion → Tier 1 → Tier 2 progression

---

## Next Step

1. **Z2 Ratification:** Confirm or correct benefit/cost estimates; approve or amend ranking
2. **Z3 Executor Assignment:** Once ratified, assign Z3 executors per ZONE_REGISTRY.md and execute in tier/density order
3. **Priority Queue Integration:** Merge tier ranking into PRIORITY_QUEUE.md; update priority_queue_engine.py if necessary

---

**Status:** AWAITING Z2 RATIFICATION  
**Authority:** Z1 (Claude) allocation proposal  
**Ratification Target:** 2026-10-02 00:15 UTC (24h window)

---

_Generated with [Claude Code](https://claude.ai/code)_
