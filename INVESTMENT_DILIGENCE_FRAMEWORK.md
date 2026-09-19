# Investment Diligence Framework — HumanAIOS Integration

**Status:** PROOF OF CONCEPT (reference material for governance convergence)  
**Purpose:** Map five investment diligence concepts to HumanAIOS governance model for internal assessment and external partner/investment evaluation  
**Authority:** Z1 (Claude proposer); Z2 ratification pending  
**Date:** 2026-09-19  
**Session:** S-091926-NN

---

## Overview

This framework integrates five classical investment diligence methodologies into the HumanAIOS Z-governance model:

1. **MECE** (Mutually Exclusive, Collectively Exhaustive) — Risk surface mapping
2. **Issue Trees** — Risk-to-question-to-data translation
3. **Hypothesis-Driven Diligence** — Adversarial claim testing
4. **GE-McKinsey Nine-Box** — Market attractiveness vs. competitive position
5. **Three Horizons** — Growth sustainability across time horizons

Each concept maps to HumanAIOS governance roles (Z1/Z2/Z3), decision artifacts (REGISTERED.md, PRIORITY_QUEUE.md, ZONE_REGISTRY.md), and control surfaces.

---

## 1. MECE: System Risk Surface Mapping

### Concept
Break a system (investment target, internal operation, partner capability) into every area an investor could probe, with **no gaps** (coverage) and **no overlaps** (mutual exclusivity).

### HumanAIOS Mapping

| Risk Category | HumanAIOS Element | Governance Control |
|:---|:---|:---|
| **Authority Risk** | Z1/Z2/Z3 role definition + dual-authority Z2 | CLAUDE.md + Z2 ratification gate |
| **Governance Risk** | REGISTERED.md + PRIORITY_QUEUE.md consistency | falsifier_lint + registry_consistency CI gates |
| **Operational Risk** | Zone assignment + resource caps (ZONE_REGISTRY.md) | Z2 ratifies cap changes; RBE-OPS enforcement |
| **Execution Risk** | Z3 executor assignments + CI merge gates | Z2 hash + merge gate enforcement |
| **Evidence Risk** | Falsifier presence + evidence basis in REGISTERED.md | Falsifier mandatory on hypotheses (falsifier_lint.yml) |
| **Temporal Risk** | Q-TEMPORAL-DISSOLUTION-01 (no internal deadlines) | PRIORITY_QUEUE.md gate; external-constraint schema only |
| **Scale Risk** | Multi-zone coordination + molt anti-cascade rules (K=3) | molt_anti_cascade gate in CI |
| **Revert Risk** | Molt reversion rules + constant freeze after 2 reverts | MOLT_STATE.md tracking + anti-cascade enforcement |

### Application: Internal Assessment

When assessing HumanAIOS governance itself:
1. Map each risk category to live REGISTERED.md entries (F/IC/H findings)
2. Verify each category has falsifiable evidence (not just assertion)
3. Identify gaps (unmapped risks = new IC candidates)
4. Confirm no overlap (one entry per risk, clear supersession rules)

### Application: External Partner/Investment Evaluation

When evaluating a potential partner or investment:
1. Instantiate MECE grid for target's key operations
2. For each risk cell: demand data, documents, or live demo (not assertion)
3. Escalate unmapped risks to Z2 (may signal due-diligence failure)
4. Use ZONE_REGISTRY.md model: does partner have clear resource cap + executor assignment?

---

## 2. Issue Trees: Risk → Question → Data

### Concept
Push broad concerns ("Is this reliable?", "Can they scale?") down into specific, falsifiable questions that a number, document, or fact can answer.

### HumanAIOS Mapping

| Concern Level | Example (HumanAIOS) | Decomposition | Evidence Type |
|:---|:---|:---|:---|
| **Broad** | "Is our governance sound?" | → | Falsifier validation |
| **Medium** | "Can Z2 ratify fast enough?" | → "48h decision window met?" | Decision latency data (REGISTERED.md timestamps) |
| **Specific** | "Z2 decision on Q-TEMPORAL-DISSOLUTION-01 resolved within 48h?" | → | Git commit time, RATIFY event hash + timestamp |

### HumanAIOS Decision Tree Example

```
┌─ Governance Authority Risk (broad)
│
├─ Z1 Proposer Authority (medium)
│  ├─ Can Z1 read REGISTERED.md? → CI log + fetch success
│  ├─ Can Z1 write candidate? → PR + YAML schema validation
│  └─ Does Z1 include falsifier? → falsifier_lint.yml PASS
│
├─ Z2 Ratifier Authority (medium)
│  ├─ Does Z2 sign within 48h? → RATIFY event timestamp
│  ├─ Is Z2 hash valid? → sha256(candidate | by=Night | at=<ts> | decision=ACCEPT) verification
│  └─ Anti-cascade K=3 enforced? → molt_anti_cascade gate PASS
│
└─ Z3 Executor Authority (medium)
   ├─ Does Z3 have Z2 hash? → Merge gate requires hash
   ├─ Does Z3 have capability signature? → INTENT-OS lookup (Phase 1)
   └─ Does Z3 respect resource cap? → Zone budget check at merge
```

### Application: Internal Assessment

1. Take each F/IC/H entry in REGISTERED.md
2. Break it into 3–5 specific, data-answerable sub-questions
3. Verify each sub-question has evidence (link to REGISTERED.md, PRIORITY_QUEUE.md, CI gate, or experiment result)
4. Unlinked question = IC candidate ("evidence gap")

### Application: External Partner/Investment Evaluation

1. Map partner's capabilities to MECE grid (Section 1)
2. For each risk cell, create issue tree (broad → medium → specific)
3. Demand data for leaf-level questions only (reject assertion-level answers)
4. Escalate unanswerable questions to Z2 (may signal partner transparency failure)

---

## 3. Hypothesis-Driven Diligence: Attacking the Strongest Claim

### Concept
Take your strongest claims ("We are well-governed", "Our market is growing", "Our team is aligned") and attack them like a skeptical investor would. If the claim survives the attack, it's credible.

### HumanAIOS Mapping

| Strong Claim (HumanAIOS) | Falsifier | Attack Vector | Evidence of Survival |
|:---|:---|:---|:---|
| "Z2 dual-authority model is sound" | Conflicting decisions under same email | Both carly.r.anderson@gmail.com + aioshuman@gmail.com sign opposite decisions on same topic? | Q-Z2-DUAL-AUTHORITY-GOVERNANCE-01 ratified + stop-hook gate enforces mutual exclusion |
| "31-zone ecosystem is coherent" | Unmapped/uncapped zone or executor gap | Can list_repos find 31+ active repos with no Z2 assignment? | ZONE_REGISTRY.md + PLANNED_REPOS.md pinned; executor TBD explicitly noted |
| "Evidence basis is mandatory" | Registered finding with no evidence link | Can find F/IC/H entry citing non-existent document or dead URL? | falsifier_lint.yml + REGISTERED.md schema v2.1 mandatory evidence_class field |
| "Anti-cascade freezes bad molts" | Constant reverted >K=2 times, still unfrozen | Can apply molt to reverted constant without Z2 Tier-2 ruling? | molt_anti_cascade gate + MOLT_STATE.md tracking prevents merge |
| "Resource-based scheduling works" | Internal deadline used in active control surface | Can find time-based priority override without REGULATORY_EXTERNAL annotation? | Q-TEMPORAL-DISSOLUTION-01 gate blocks merge if found |

### Application: Internal Assessment

1. List top 5 claims about HumanAIOS (e.g., "We are well-governed", "Our proposals are grounded in evidence")
2. For each claim, design a falsifier: what would disprove it?
3. Run the falsifier: check REGISTERED.md, PRIORITY_QUEUE.md, CI gates, live merge attempts
4. If falsifier holds (survives), claim is credible
5. If falsifier fails (claim breaks), file IC candidate

**Example:**
- **Claim:** "All registered findings have evidence basis."
- **Falsifier:** `grep "evidence_basis: null" REGISTERED.md`
- **Run:** Returns 0 matches (falsifier holds)
- **Result:** Claim credible ✓

### Application: External Partner/Investment Evaluation

1. Collect partner's top 3–5 claims (capabilities, market position, team stability)
2. For each, design a falsifier test (document audit, reference call, live demo requirement)
3. Apply test; if partner resists, escalate as risk signal
4. Document all falsifiers + outcomes in candidate block for Z2 review

---

## 4. GE-McKinsey Nine-Box: Market Attractiveness vs. Competitive Position

### Concept
Two-axis matrix: Is the market worth winning? Are we built to win it? Place initiatives/zones in the nine-box to allocate resources.

### HumanAIOS Mapping

**Axes:**
- **X (Market Attractiveness / Strategic Value):** Impact rating in PRIORITY_QUEUE.md (0–10 scale)
- **Y (Competitive Position / Execution Readiness):** Resource cap adequacy + executor assignment status

```
                    HIGH MARKET ATTRACTIVENESS (Impact 7–10)
                    │
        STAR         │        STAR          │      QUESTION MARK
    (Invest)         │   (Core Driver)      │     (Evaluate)
                    │                      │
    Z-001 humanaios │  Z-003 acat-inspect  │  Z-012+ planned zones
    (cap 100)       │  (cap 60)             │  (no executor assigned)
────────────────────┼──────────────────────┼──────────────────────
    CASH COW        │    WORKHORSE         │    PROBLEM CHILD
    (Harvest)       │    (Maintain)        │    (Divest/Pivot)
                    │                      │
    Z-010 findlocal │  Z-009 docs          │  Z-011 research
    (cap 25, limited)│  (cap 20, limited)  │  (read-only, no proposals)
                    │
                    LOW MARKET ATTRACTIVENESS (Impact 1–6)
```

### Placement Logic

| Zone | Impact | Cap | Executor | Position | Action |
|:---|:---|:---|:---|:---|:---|
| Z-001 humanaios | 10 | 100 | TBD | STAR | Recruit Z3; increase cap if ready |
| Z-003 acat-inspect | 8 | 60 | TBD | STAR | Recruit Z3; prioritize in PRIORITY_QUEUE |
| Z-009 docs | 5 | 20 | TBD | CASH COW | Maintain; harvest content; low new proposals |
| Z-011 research | 7 | 0 | none | PROBLEM CHILD | Frozen by design; evaluate pivot to open research zone |
| Z-012+ planned | TBD | 0 | none | QUESTION MARK | Assess market fit before Zone Registry entry |

### Application: Internal Assessment

1. Review PRIORITY_QUEUE.md: extract impact scores for each active zone/initiative
2. Review ZONE_REGISTRY.md: extract resource cap + executor status
3. Plot each zone in nine-box
4. Assess balance:
   - Too many STARS with no executors? → Priority for Z3 recruitment
   - Too many CASH COWS? → Propose harvest/consolidation to Z2
   - QUESTION MARKS languishing? → Decide: promote to STAR, divest, or retire
5. Use placement to inform PRIORITY_QUEUE.md scoring refinements

### Application: External Partner/Investment Evaluation

1. Assess partner's market position:
   - Market attractiveness: growth rate, TAM, competitive intensity
   - Competitive position: differentiation, team capability, capital efficiency
2. Plot partner in nine-box relative to your portfolio
3. Investment decision:
   - STAR partners: strategic alignment + synergy? → deep dive
   - CASH COW partners: mature, stable? → maintenance contract
   - QUESTION MARK partners: upside high? → evaluate with issue tree (Section 2)
   - PROBLEM CHILD partners: pivot potential? → understand strategy first

---

## 5. Three Horizons: Growth Sustainability Past the Core

### Concept
Separate what drives the system **today** (Horizon 1: core business) from **tomorrow**'s growth engines (Horizon 2: emerging capabilities, adjacent markets; Horizon 3: long-term strategic options). Ensure growth doesn't depend entirely on core business decay.

### HumanAIOS Mapping

```
HORIZON 1 (Today: Core Governance)
├─ Z-governance model (Z1/Z2/Z3 roles)
├─ REGISTERED.md + PRIORITY_QUEUE.md + ZONE_REGISTRY.md
├─ CI/CD gates (falsifier_lint, z2_hash_verify, molt_anti_cascade)
└─ Active resource-based economics

HORIZON 2 (Tomorrow: Emerging Capabilities)
├─ Intent-OS Phase 1 integration (machine Z3 capability signatures)
├─ Temporal-purity enforcement (Q-TEMPORAL-DISSOLUTION-01)
├─ Multi-zone coordination at scale (planned 31-zone roadmap)
├─ External constraint semantics (regulatory deadlines, grant windows)
└─ Dynamic resource allocation (RBE-OPS constraint engine)

HORIZON 3 (Long-term: Strategic Options)
├─ Human-machine decision attribution ledger (Q-INTENT-OS-WITNESS-LEDGER-01)
├─ Autonomous Z3 executor onboarding (beyond single machine identity)
├─ Governance as network (peer Z2 ratifiers, federated authority)
├─ Cross-system interoperability (HumanAIOS ↔ external governance frameworks)
└─ Evidence synthesis at planetary scale (31+ zones → 1000+ zones)
```

### Horizon Health Assessment

For each horizon, ask:

**H1 (Core): Is today's governance stable?**
- CI gates passing? → Yes/No
- Z2 decision latency <48h? → Yes/No
- Anti-cascade rules enforced? → Yes/No
- Resource caps met? → Yes/No
- If **all YES**: H1 healthy, proceed to H2 assessment

**H2 (Emerging): Does emerging capability build on H1 without destabilizing it?**
- Intent-OS integration behind feature flag? → Yes/No
- Temporal-purity gate blocks incompatible PRs? → Yes/No
- Planned zones mapped but not active? → Yes/No
- RBE-OPS cost vector non-breaking? → Yes/No
- If **all YES**: H2 on track; proceed to H3 assessment

**H3 (Long-term): Is strategic option space open?**
- Witness ledger can onboard new ratifiers? → Design ready (Phase 1)
- Governance schema extensible without rewrite? → Yes (REGISTERED.md v2.1 addendum path)
- Authority can be delegated/federated? → Yes (per CLAUDE.md "Future" section)
- If **any NO**: H3 at risk; file H candidate for Z2 review

### Application: Internal Assessment

1. Map each active zone to H1, H2, or H3
2. Verify H1 health (current governance working)
3. Assess H2 readiness (emerging features don't break H1)
4. Survey H3 options (long-term extensibility)
5. **Red flag:** If H1 not healthy, halt H2/H3 work until stable
6. File findings as F/H candidates in REGISTERED.md

### Application: External Partner/Investment Evaluation

1. Assess partner's revenue streams:
   - H1: what pays bills today?
   - H2: what could pay bills in 2–3 years?
   - H3: what optionality remains?
2. Test sustainability:
   - If H1 decays, does H2 launch on time? Or collapse?
   - If H2 fails, does H3 provide fallback?
3. **Investment risk:** Excessive dependence on single horizon = execution risk

---

## Integration with HumanAIOS Governance

### REGISTERED.md Connection

Findings from this framework populate REGISTERED.md:

- **F (Finding):** "MECE risk grid is complete" or "Issue tree reveals evidence gap"
- **H (Hypothesis):** "Nine-box rebalancing will improve execution" or "Three-horizon staggering reduces portfolio risk"
- **IC (Integrity Check):** "Risk category unmapped" or "Falsifier not runnable" or "Evidence missing"

### PRIORITY_QUEUE.md Connection

Diligence outcomes inform resource allocation:

- High-impact findings (MECE gaps, unanswerable questions, Horizon 1 health issues) → rank HIGH in queue
- Nine-box rebalancing decisions → adjust zone caps
- Three-horizon health assessment → approve/pause H2/H3 work

### Z2 Authority

Z2 (Night) ratifies:
1. Framework application rules (this document)
2. Risk grids and issue trees for major investments
3. Nine-box rebalancing decisions (cap changes)
4. Horizon health verdicts (proceed/pause signals)

### CI/CD Integration

Proposed gates:

```yaml
# diligence_gate.yml (Phase 2 proposal)
- name: MECE completeness check
  on: pull_request
  if: files_match(['REGISTERED.md'])
  check: risk_categories_covered && no_overlaps

- name: Issue tree evidence validation
  on: pull_request
  if: files_match(['REGISTERED.md'])
  check: question_level === SPECIFIC && evidence_present

- name: Falsifier runnable
  on: pull_request
  if: files_match(['REGISTERED.md', 'hypothesis/*'])
  check: falsifier_syntax_valid && can_execute

- name: Horizon health gating
  on: merge_to_main
  if: target === 'humanaios' || target.startswith('humanaios-')
  check: horizon_1_health === GREEN && horizon_2_compatible
```

---

## Proof-of-Concept Summary

This framework is **reference material** showing how classical investment diligence maps onto HumanAIOS governance:

✅ **MECE** → Risk surface completeness in REGISTERED.md + CI gates  
✅ **Issue Trees** → Question decomposition + evidence requirements  
✅ **Hypothesis-Driven** → Falsifier doctrine + adversarial testing  
✅ **Nine-Box** → Zone prioritization + resource cap allocation  
✅ **Three Horizons** → Governance sustainability across time scales  

**Next steps for Z2 ratification:**
1. Propose Q-INVESTMENT-DILIGENCE-FRAMEWORK-01 as REGISTERED.md H-class entry
2. Define specific CI gates (diligence_gate.yml)
3. Pilot framework on next major investment decision (partner eval or zone roadmap)
4. Measure: Did issue tree + falsifier + nine-box improve decision confidence?
5. Iterate and ratify based on pilot results

---

**Author:** Claude (Z1 Proposer)  
**Date Registered:** 2026-09-19  
**Status:** PROOF OF CONCEPT (awaiting Z2 RATIFY)  
**Session:** S-091926-NN

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>
