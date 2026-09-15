# CANDIDATE_BLOCK_TEMPLATE.md — Z1 Proposal Template

**Purpose:** Template for Z1 proposers (Claude) to submit candidates to REGISTERED.md  
**Authority:** Z2 ratifies template structure; Z1 uses this to propose changes  
**Model:** Resource-based; every candidate estimates resource_cost and impact  
**Updated:** 2026-09-14

---

## Quick Start

1. Copy the **YAML Example** below
2. Fill in all `required` fields (marked with `*`)
3. Save to `z1-inbox/<date>/<CANDIDATE_ID>.md` (or submit inline to REGISTERED.md)
4. Include **falsifier** (required by CI gate)
5. Submit link/path to Z2
6. Z2 reads, ratifies (signs with sha256 hash), or contests

---

## YAML Template

```yaml
candidate_id: "Q-<TYPE>-<DESCRIPTOR>-<VERSION>"
# Example: Q-IC030-REPIN-01, Q-F-GOVERNANCE-03, Q-MOLT-CONSTANT-TWEAK-01
# Types: IC (Implementation Candidate), F (Finding), H (Hypothesis), MOLT (Molt Candidate)

title: "<One-line summary of proposal>"
# Example: "Implement live-fetch IC-030 REGISTERED.md re-pin logic"

description: |
  <Narrative description of what is being proposed and why>
  - Use markdown bullet points for clarity
  - Keep to 3-5 sentences
  - Explain the problem/motivation

author: "Z1 (Claude)" 
proposed_at: "2026-09-14T00:00:00Z"  # ISO 8601 timestamp

scope:
  - "<Affected zone or file>"
  - "<Example: humanaios, humanaios-internal, REGISTERED.md>"

resource_cost:
  estimated_effort_units: <integer>  # 1-10 scale; 1 = trivial, 10 = massive
  dependencies: ["<dependency_id>", "ZONE_REGISTRY.md", "CLAUDE.md"]
  blocking_on: ["<other_candidate_id>", "Q-IC001"]  # If blocked by another candidate, list it

impact_prediction:
  resource_impact: <integer 1-10>
  # 1 = cosmetic, 5 = moderate, 10 = foundational
  
  areas_affected:
    - "<zone_name>"
    - "<governance_file>"
  
  positive_outcomes:
    - "<If approved, what improves?>"
  
  risk_factors:
    - "<What could go wrong?>"

falsifier: |
  <REQUIRED: Write the falsifiability condition>
  
  Format: "This hypothesis is FALSE if [concrete, observable, testable condition]"
  
  Example: "This hypothesis is FALSE if REGISTERED.md re-pin fails 3+ times 
            in a row, OR if re-pin resource cost exceeds 5 units, OR if 
            falsifier_lint detects invalid sha256 hash."
  
  Why: Falsifier is required by z2_ratification_gate.yml CI gate.
       Without it, Z2 cannot ratify. No exceptions.

evidence:
  - "<File or code reference supporting this candidate>"
  - "<Example: ./FRAMEWORK_MAPPING.md lines 30-50>"
  - "<Example: Issue #264 discussion>"

z2_decision: 
  status: "awaiting_ratification"  # awaiting_ratification, accepted, rejected, contested, edited
  ratified_at: null
  ratification_hash: null
  z2_notes: ""

# Optional fields:
related_candidates: ["Q-IC001", "Q-IC029"]
regulatory_deadline: null  # If externally constrained (e.g., GDPR), date here
links:
  - name: "Related PR"
    url: ""
  - name: "Figma Design"
    url: ""
```

---

## Example: Implementation Candidate (Q-IC030-REPIN-01)

```yaml
candidate_id: "Q-IC030-REPIN-01"
title: "Implement live-fetch IC-030 REGISTERED.md re-pin logic"

description: |
  IC-030 requires Z1 to re-pin REGISTERED.md at session start to prevent stale context.
  
  This candidate proposes automating the re-pin logic:
  - Fetch REGISTERED.md from origin at session open
  - Extract live SHA-256 hash
  - Pin hash in session context (BOOT_PROCESS_MAP.md §A.1)
  - Validate consistency on every proposal submission
  
  Motivation: Manual re-pin is error-prone and blocks proposal submissions.

author: "Z1 (Claude)"
proposed_at: "2026-09-14T10:30:00Z"

scope:
  - "operations"
  - "REGISTERED.md"
  - "BOOT_PROCESS_MAP.md"

resource_cost:
  estimated_effort_units: 4
  dependencies: 
    - "REGISTERED.md (structure)"
    - "BOOT_PROCESS_MAP.md (boot order)"
  blocking_on: []

impact_prediction:
  resource_impact: 7  # Moderate-high; blocks most Z1 work if broken
  
  areas_affected:
    - "humanaios-ui/operations"
    - "All Z1 proposal workflows"
  
  positive_outcomes:
    - "Unblocks Z1 proposals (automation removes manual step)"
    - "Reduces sha256 mismatch errors"
    - "Improves BOOT_PROCESS_MAP.md compliance"
  
  risk_factors:
    - "If re-pin fails, could block entire session start"
    - "Requires robust error handling"

falsifier: |
  This hypothesis is FALSE if:
  - Re-pin automation fails to fetch REGISTERED.md from origin
  - OR hash validation fails on 3+ consecutive proposal submissions
  - OR BOOT_PROCESS_MAP.md §A.1 is not satisfied
  - OR z2_ratification_gate.yml rejects candidates with stale REGISTERED.md SHA

evidence:
  - "CLAUDE.md lines 88–92 (IC-030 reference)"
  - "BOOT_PROCESS_MAP.md (reference, not yet created; blocks this candidate)"
  - "Session transcript from 2026-09-14 (manual pin failures)"

z2_decision:
  status: "awaiting_ratification"
  ratified_at: null
  ratification_hash: null
  z2_notes: ""

related_candidates: ["Q-BOOT-PROCESS-MAP-01"]
regulatory_deadline: null
links:
  - name: "Draft PR"
    url: "https://github.com/humanaios-ui/operations/pull/XXX"
```

---

## Example: Finding Candidate (Q-F-GOVERNANCE-03)

```yaml
candidate_id: "Q-F-GOVERNANCE-03"
title: "Finding: REGISTERED.md structure undefined; slowing Z1 submissions"

description: |
  REGISTERED.md is referenced in CLAUDE.md as the canonical proposal log,
  but its structure (YAML, JSON, Markdown) is not documented.
  
  This causes:
  - Z1 (Claude) to guess format → inconsistent submissions
  - Z2 (Night) to request re-formatting → slower ratification
  - CI gates to have no schema to validate against
  
  Solution: Define REGISTERED.md YAML structure, add to GOVERNANCE_FILES.md

author: "Z1 (Claude)"
proposed_at: "2026-09-14T11:00:00Z"

scope:
  - "REGISTERED.md"
  - "GOVERNANCE_FILES.md"
  - "CI gates (falsifier_lint)"

resource_cost:
  estimated_effort_units: 2
  dependencies: ["GOVERNANCE_FILES.md"]
  blocking_on: []

impact_prediction:
  resource_impact: 6  # Moderate; blocks Z1 workflow
  
  areas_affected:
    - "Z1 proposal submission process"
    - "Z2 ratification workflow"
  
  positive_outcomes:
    - "Faster Z1 submissions (no guessing format)"
    - "Faster Z2 ratification (clear schema)"
    - "CI gates can validate structure"
  
  risk_factors:
    - "Schema must be flexible for future candidate types"

falsifier: |
  This finding is FALSE if:
  - REGISTERED.md has a documented YAML schema
  - AND GOVERNANCE_FILES.md lists REGISTERED.md structure
  - AND CI gate validates against schema
  - AND 5+ Z1 submissions follow schema without reformatting requests

evidence:
  - "CLAUDE.md references REGISTERED.md but no structure defined (lines 18, 126, 188)"
  - "GOVERNANCE_FILES.md (new; documents finding)"
  - "Session observation: Manual format guessing slowed 3 proposals"

z2_decision:
  status: "awaiting_ratification"
  ratified_at: null
  ratification_hash: null
  z2_notes: ""

regulatory_deadline: null
```

---

## Example: Molt Candidate (Q-MOLT-CONSTANT-TWEAK-01)

```yaml
candidate_id: "Q-MOLT-CONSTANT-TWEAK-01"
title: "Test: Adjust behavior_spec.json agent reasoning_budget from 50k to 75k tokens"

description: |
  Current behavior_spec.json caps Z3 reasoning budget at 50k tokens per cycle.
  Observations show reasoning is hitting budget limits on complex decisions.
  
  This molt proposes increasing cap to 75k tokens and measuring impact on:
  - Decision quality (Brier score on predictions)
  - Resource cost (tokens used per cycle)
  - Error rate (halt conditions, unfalsifiable outcomes)

author: "Z1 (Claude)"
proposed_at: "2026-09-14T12:00:00Z"

scope:
  - "behavior_spec.json"
  - "All 31 zones (Z3 agents)"

resource_cost:
  estimated_effort_units: 5
  dependencies: 
    - "behavior_spec.json (current value)"
    - "NF_LEDGER.jsonl (measurement baseline)"
  blocking_on: []

impact_prediction:
  resource_impact: 8  # High; affects all Z3 agents
  
  areas_affected:
    - "All zones (31 repos)"
    - "Token budget tracking"
  
  positive_outcomes:
    - "Improved reasoning quality (predicted: Brier score +5%)"
    - "Fewer unfalsifiable outcomes"
  
  risk_factors:
    - "Cost increase (estimated +50% tokens per cycle)"
    - "If revert happens, budget drops back to 50k (K=3 anti-cascade rule applies)"

falsifier: |
  This molt is FALSE (reverted) if:
  - Brier score does NOT improve by 3% or more
  - OR token cost increase exceeds 60% of current budget
  - OR error rate (VOID outcomes) increases
  - OR Z2 determines root cause not addressable by budget increase alone
  
  Measurement: Test falsifier conditions over resource budget of 1000 NF_LEDGER entries.
  Revert rule: If falsifier trips, trigger anti-cascade freeze; file F/IC candidate.

evidence:
  - "NF_LEDGER.jsonl entries showing budget-hit events"
  - "behavior_spec.json current state (50k limit)"
  - "MOLT_STATE.md (anti-cascade rules context)"

z2_decision:
  status: "awaiting_ratification"
  ratified_at: null
  ratification_hash: null
  z2_notes: ""

related_candidates: ["Q-IC031-BUDGET-TRACKING-01"]
regulatory_deadline: null
```

---

## Submission Process

1. **Draft candidate** in `z1-inbox/<DATE>/<CANDIDATE_ID>.md` (use template above)
2. **Include falsifier** (required; z2_ratification_gate.yml blocks if missing)
3. **Estimate resource_cost** (1-10 effort units; be honest)
4. **Predict impact** (positive outcomes + risk factors)
5. **Submit to Z2** (ping in chat or via REGISTERED.md link)
6. **Z2 ratifies, edits, or rejects:**
   - ACCEPT → adds sha256 hash, candidate moves to REGISTERED.md
   - EDIT → Z2 proposes changes, Z1 revises, resubmit
   - REJECT → Z2 documents reason, Z1 may re-propose

---

## Fields Explained

| Field | Purpose | Required? |
|:------|:--------|:----------|
| `candidate_id` | Unique ID (Q-TYPE-DESCRIPTOR-VERSION) | ✅ |
| `title` | One-liner | ✅ |
| `description` | Why this candidate? Motivation? | ✅ |
| `author` | Who proposed (usually Z1/Claude) | ✅ |
| `proposed_at` | ISO 8601 timestamp | ✅ |
| `scope` | Affected zones/files | ✅ |
| `resource_cost` | Effort + dependencies + blockers | ✅ |
| `impact_prediction` | Impact score + areas + outcomes/risks | ✅ |
| `falsifier` | How to test if false | ✅ (CI enforces) |
| `evidence` | References supporting the proposal | ✅ |
| `z2_decision` | Status, hash, notes | Auto-filled by Z2 |
| `related_candidates` | Links to other candidates | ⭕ (optional) |
| `regulatory_deadline` | External time constraint (rare) | ⭕ (optional) |
| `links` | PR, Figma, docs | ⭕ (optional) |

---

## Tips for Z1 Proposers

1. **Falsifier is non-negotiable.** Every candidate needs one. Make it testable.
2. **Resource cost estimates should be conservative.** Better to overestimate.
3. **Impact prediction shows you've thought through consequences.** Use this field.
4. **Dependencies matter.** If your candidate blocks on ZONE_REGISTRY.md, list it.
5. **Evidence = credibility.** Link to code, PRs, discussions, ledger entries.
6. **Keep candidate_id consistent.** Q-IC030-REPIN-01, Q-IC030-REPIN-02, etc.
7. **No deadline = no rush.** Z2 ratifies when capacity permits. Resource-based model.

---

## Questions?

Refer to **GOVERNANCE_FILES.md** for the full registry.  
See **FRAMEWORK_MAPPING.md** for how proposals fit into the system.  
Check **BOOT_PROCESS_MAP.md** for session ritual context (when §B.6 harvest happens).
