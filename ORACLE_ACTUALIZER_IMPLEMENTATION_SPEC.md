# Q-ORACLE-ACTUALIZER-01: Implementation Specification

**Z2 Ratified Decisions:** 2a–2f (See PHASE_1_RATIFICATION_PACKAGE.md)  
**Authority:** Night (carly.r.anderson@gmail.com)  
**Status:** DRAFT — Ready for Z2 Signature + Z3 Implementation  
**Stage:** 4 (Z2 Ratification) → 5 (Z3 Implementation)

---

## Core Decision Summary

| Decision | Ratified Value | Impact |
|----------|---|---|
| **2a. Oracle Data Model** | Derivative (REGISTERED.md canonical) | Oracle is fast-read cache; prevents data-consistency chaos |
| **2b. Actualizer Precondition** | Operator authorization + guardrails | Cannot auto-execute on DISPUTED/UNKNOWN warrants |
| **2c. Cross-Substrate Tiebreaker** | Preserve disagreement | DISPUTED warrant → escalation, operator decides |
| **2d. Molt Authority** | Z1 proposes, Z2 ratifies | Constitutional amendments follow explicit path |
| **2e. Human Authority Boundaries** | Explicit no-delegate list (hardcoded) | Authority grants, data deletion, constitutional changes never delegated |
| **2f. Falsifiers** | 10-item checklist (state-driven) | Unknown claims in escalation state, unauthorized actions exceeding threshold, disagreement >30% trigger audit |

---

## Implementation Part 1: Oracle State Schema Operationalization

### Oracle Data Model (2a: Derivative Authority)

**File:** `oracle_state.json` (read-only cache, regenerated from REGISTERED.md)

```json
{
  "schema_version": "1.0",
  "metadata": {
    "canonical_source": "REGISTERED.md",
    "last_sync": "2026-09-28T14:32:00Z",
    "sync_hash": "sha256(REGISTERED.md:SHA)",
    "cache_ttl_minutes": 5,
    "authority_note": "This is a derivative cache. All writes to state go to REGISTERED.md first; Oracle reflects within TTL."
  },
  
  "system_state": {
    "boot_stage": "string (BOOT_STAGE_ENUM: SECURE_BOOT|BOOTLOADER|KERNEL|DEVICE_ENUM|INIT|PERMISSION_MODEL|LOGIN|RUNTIME_TUNING|SHUTDOWN)",
    "z_role_assignments": {
      "z1_proposers": ["Claude", "empirica-autonomy"],
      "z2_ratifier": "Night (carly.r.anderson@gmail.com, aioshuman@gmail.com)",
      "z3_executors": {}
    },
    "governance_contracts": {
      "k_cascade_limit": 3,
      "time_window_hours_routine": 48,
      "time_window_hours_urgent": 24,
      "revert_freeze_threshold": 2
    }
  },
  
  "constitutional_state": {
    "framework_mapping_version": "1.0",
    "boot_process_map_version": "1.0",
    "zone_registry_version": "1.0",
    "planned_repos_version": "1.0",
    "active_repos_count": 7,
    "planned_repos_count": 24
  },
  
  "agents": [
    {
      "id": "claude-z1",
      "name": "Claude",
      "role": "Z1_PROPOSER",
      "authority_scope": ["propose_candidates", "flag_blockers", "request_z2_reread"],
      "substrate_coverage": ["CLAUDE_CODE"],
      "last_activity": "ISO8601_timestamp"
    },
    {
      "id": "copilot-z3",
      "name": "Copilot",
      "role": "Z3_EXECUTOR",
      "authority_scope": ["merge_ratified", "emit_verdicts", "log_receipts"],
      "substrate_coverage": ["COPILOT"],
      "last_activity": "ISO8601_timestamp"
    }
  ],
  
  "claims": [
    {
      "claim_id": "CLM-001",
      "text": "SMAG calibration review required predicate operationalizes decisions 1a-1f",
      "epistemic_status": "VERIFIED | INFERRED | DISPUTED | UNKNOWN | DEFEATED",
      "substrate": "CLAUDE_CODE",
      "created_at": "ISO8601_timestamp",
      "evidence_ids": ["EVD-001", "EVD-002"],
      "warrant_id": "WRT-001"
    }
  ],
  
  "evidence": [
    {
      "evidence_id": "EVD-001",
      "type": "code_artifact | measurement | observation | reasoning",
      "content": "Pseudocode for CALIBRATION_REVIEW_REQUIRED()",
      "source": "SMAG_IMPLEMENTATION_SPEC.md",
      "timestamp": "ISO8601_timestamp",
      "quality_assessment": "primary | secondary | tertiary",
      "contradicts": []
    }
  ],
  
  "warrants": [
    {
      "warrant_id": "WRT-001",
      "claim_id": "CLM-001",
      "authority_basis": "Decision 1a-1f ratification",
      "preconditions": ["Z2 signature present", "Profile ratified"],
      "epistemic_status": "VERIFIED | INFERRED | DISPUTED | UNKNOWN",
      "z2_ratification_hash": "sha256(...)",
      "reversibility": "High (Molt candidate to revert)"
    }
  ],
  
  "challenges": [
    {
      "challenge_id": "CHG-001",
      "claim_id": "CLM-001",
      "challenger": "Z1 | Z2 | Z3",
      "reason": "Falsifier tripped | Assumption violation | Gap found",
      "timestamp": "ISO8601_timestamp",
      "status": "OPEN | RESOLVED"
    }
  ],
  
  "unknowns": [
    {
      "unknown_id": "UNK-001",
      "description": "Actual gap_rate distribution under COPILOT substrate",
      "relevant_to_claims": ["CLM-001"],
      "days_unknown": 0,
      "falsifier_threshold": 14,
      "escalation_required_at": "ISO8601_timestamp (day 14)"
    }
  ],
  
  "experiments": [
    {
      "experiment_id": "EXP-001",
      "hypothesis": "SMAG calibration review required reduces unauthorized merges by ≥5%",
      "phase": "Phase 1 (implementation stage; not calendar-driven)",
      "status": "PROPOSED | RUNNING | COMPLETED | REVERTED",
      "measurement_window": "30 days",
      "expected_observation": "gap_rate distribution over baseline",
      "falsifier": "False negative rate >10% | Unknown state in escalation (state-tracked in REGISTERED.md)"
    }
  ],
  
  "precedents": [
    {
      "precedent_id": "PRC-001",
      "decision": "Review-escalating gate (Decision 1b)",
      "ratification_date": "2026-09-28",
      "applies_to": ["CLAUDE_CODE", "COPILOT"],
      "next_review_trigger": "Upon completion of 3-month measurement cycle (state-gated, not calendar-driven)"
    }
  ],
  
  "amendments": [
    {
      "amendment_id": "AMD-001",
      "description": "Add new substrate to filtering registry",
      "type": "MOLT_CANDIDATE | Z2_DECISION | Z1_PROPOSAL",
      "status": "PROPOSED | RATIFIED | REJECTED",
      "ratification_hash": "sha256(...)"
    }
  ],
  
  "actions": [
    {
      "action_id": "ACT-001",
      "description": "Apply Molt 1: Update SMAG profile threshold from 0.20 to 0.25",
      "warrant": "WRT-001",
      "authority_basis": "Decision 1b (review-escalating)",
      "human_approval_required": true,
      "required_preconditions": ["Z2 signature on molt", "Profile timestamp current"],
      "affected_artifacts": ["calibration_profiles/BASELINE_S092126_v2.yaml"],
      "execution_plan": "Merge ratified PR; regenerate Oracle; log to NF_LEDGER",
      "reversibility": "High (revert Molt)",
      "expected_observation": "Merge gate escalates to 5% more PRs",
      "success_condition": "Observation matches prediction ±2%",
      "falsifier": "False positive rate >15%"
    }
  ],
  
  "execution_receipts": [
    {
      "receipt_id": "RCP-001",
      "action_id": "ACT-001",
      "executed_by": "Z3 (Copilot)",
      "timestamp": "ISO8601_timestamp",
      "status": "SUCCESS | BLOCKED | FAILED",
      "evidence": "Merge commit SHA, log entry hash",
      "claim_vs_tree_match": "All claims in transcript found in NF_LEDGER"
    }
  ],
  
  "human_attention": [
    {
      "attention_id": "ATN-001",
      "type": "ESCALATION | REVIEW_REQUIRED | BLOCKED_ACTION | DISPUTED_WARRANT",
      "description": "Cross-substrate disagreement on gap_rate measurement",
      "severity": "CRITICAL | HIGH | MEDIUM | LOW",
      "required_by": "ISO8601_timestamp",
      "responsible_authority": "Z2 | Z3",
      "status": "OPEN | ACKNOWLEDGED | RESOLVED"
    }
  ]
}
```

### Oracle Consistency Rules

**Invariant 1 (2a: Derivative Authority):** Oracle schema matches REGISTERED.md structure or divergence is logged as DISPUTED warrant
**Invariant 2 (2b: Preconditions):** Every action in Oracle has preconditions; no action auto-executes without Z2 signature
**Invariant 3 (2e: Human Authority):** Oracle schema has hardcoded no-delegate list (see below)
**Invariant 4 (2f: Audit):** Oracle tracks unknown_ids with escalation_state; escalates when state_tracked in REGISTERED.md (not calendar-driven)

---

## Implementation Part 2: Actualizer Action Contract

### Actualizer Preconditions (2b: Operator Authorization + Guardrails)

**File:** `actualizer_contract.py` (Pseudocode)

```python
def ACTUALIZER_CAN_EXECUTE(action: dict, state: dict) -> tuple[bool, str]:
    """
    Decides whether Actualizer can execute a proposed action.
    Returns (can_execute: bool, reason: str)
    
    Decision 2b: Operator authorization required; guardrails prevent auto-execution.
    """
    
    # Precondition 1: No execute on DISPUTED warrant
    if action['warrant']['epistemic_status'] == 'DISPUTED':
        return (False, "DISPUTED warrant; operator decides; no auto-execute")
    
    # Precondition 2: No execute on UNKNOWN warrant
    if action['warrant']['epistemic_status'] == 'UNKNOWN':
        # Check if unknown >14 days (2f falsifier)
        days_unknown = (NOW - action['warrant']['unknown_since']).days
        if days_unknown > 14:
            return (False, "UNKNOWN >14 days; escalate to Z2; no auto-execute")
        else:
            return (False, "UNKNOWN warrant; operator decides; no auto-execute")
    
    # Precondition 3: Check human authority boundaries (2e)
    if action['category'] in HARD_NO_DELEGATE_LIST:
        return (False, f"Action category {action['category']} requires human approval; no auto-execute")
    
    # Precondition 4: Verify Z2 signature on action warrant
    if not Z2_SIGNATURE_VALID(action['warrant']['ratification_hash']):
        return (False, "No Z2 signature on warrant; no auto-execute")
    
    # Precondition 5: Check operator authorization
    if action['requires_operator_approval'] and not OPERATOR_APPROVED(action['action_id']):
        return (False, "Operator approval required; pending")
    
    # If all preconditions pass:
    return (True, "All preconditions met; execution authorized")


def HARD_NO_DELEGATE_LIST() -> list[str]:
    """
    Decision 2e: Human authority boundaries (hardcoded, never delegated).
    """
    return [
        "AUTHORITY_GRANT",           # Z2 only
        "DATA_DELETION",             # Z2 only
        "CONSTITUTIONAL_AMENDMENT",  # Z2 (via molt)
        "ESCALATION_DECISION",       # Z2 only
        "Z_ROLE_ASSIGNMENT",         # Z2 only
        "MOLLIFICATION",             # Z2 ratifies; Z1 proposes
        "FALSIFIER_OVERRIDE"         # Z2 only
    ]


def CROSS_SUBSTRATE_TIEBREAKER(claims: list[dict], substrates: list[str]) -> dict:
    """
    Decision 2c: Preserve disagreement.
    When two substrates disagree on warrant epistemic status, mark as DISPUTED.
    """
    
    claim_statuses = {}
    for substrate in substrates:
        substrate_warrant = ORACLE_STATE.find_warrant_for_substrate(claim['id'], substrate)
        if substrate_warrant:
            claim_statuses[substrate] = substrate_warrant['epistemic_status']
    
    # Check for disagreement
    unique_statuses = set(claim_statuses.values())
    if len(unique_statuses) > 1:
        # Disagreement found
        return {
            'claim_id': claim['id'],
            'status': 'DISPUTED',
            'disagreement_by_substrate': claim_statuses,
            'action_required': 'operator_decides',
            'escalation_reason': 'Cross-substrate disagreement on warrant epistemic status'
        }
    
    return {
        'claim_id': claim['id'],
        'status': unique_statuses.pop(),
        'disagreement_by_substrate': claim_statuses,
        'action_required': None
    }


def EXECUTE_ACTION_WITH_RECEIPT(action: dict, state: dict) -> dict:
    """
    Execute an Actualizer action and record execution receipt.
    Decision 2b: Logs receipt to oracle_state['execution_receipts'].
    """
    
    can_execute, reason = ACTUALIZER_CAN_EXECUTE(action, state)
    
    if not can_execute:
        receipt = {
            'receipt_id': f"RCP-{uuid()}",
            'action_id': action['action_id'],
            'status': 'BLOCKED',
            'reason': reason,
            'timestamp': NOW,
            'escalation_required': True
        }
        ORACLE_STATE['human_attention'].append({
            'type': 'BLOCKED_ACTION',
            'receipt_id': receipt['receipt_id'],
            'action_id': action['action_id']
        })
        return receipt
    
    # Execute
    try:
        result = EXECUTE_TOOL(action['tool'], action['params'])
        receipt = {
            'receipt_id': f"RCP-{uuid()}",
            'action_id': action['action_id'],
            'executed_by': 'Actualizer (Z3)',
            'timestamp': NOW,
            'status': 'SUCCESS',
            'evidence': result['commit_sha'] or result['log_hash'],
            'claim_vs_tree_match': VERIFY_RECEIPT_WALK_BACK(action)
        }
    except Exception as e:
        receipt = {
            'receipt_id': f"RCP-{uuid()}",
            'action_id': action['action_id'],
            'status': 'FAILED',
            'error': str(e),
            'timestamp': NOW
        }
    
    ORACLE_STATE['execution_receipts'].append(receipt)
    LOG_TO_NF_LEDGER(receipt)
    
    return receipt
```

---

## Implementation Part 3: Molt Procedure

### Constitutional Amendment Process (Decision 2d: Z1 proposes, Z2 ratifies)

**File:** `.github/workflows/molt-ratification.yml`

```yaml
name: Molt Ratification Gate

on:
  pull_request:
    paths:
      - 'MOLT_STATE.md'
      - 'constants/**'

jobs:
  molt_validation:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: "Detect molt candidate in MOLT_STATE.md"
        run: |
          if grep -q "MOLT_CANDIDATE" MOLT_STATE.md; then
            echo "molt_detected=true" >> $GITHUB_ENV
          else
            echo "molt_detected=false" >> $GITHUB_ENV
          fi
      
      - name: "Verify Z2 decision present"
        if: env.molt_detected == 'true'
        run: |
          # Check for Z2 signature in molt candidate
          if grep -q "ratification_hash.*sha256" MOLT_STATE.md; then
            echo "z2_signature=true" >> $GITHUB_ENV
          else
            echo "ERROR: Molt candidate missing Z2 signature hash"
            exit 1
          fi
      
      - name: "Enforce anti-cascade rules"
        if: env.molt_detected == 'true'
        run: |
          # Rule 1: One open molt per constant
          open_molts=$(grep -c "status.*PROPOSED\|RATIFIED" MOLT_STATE.md || echo 0)
          if [ "$open_molts" -gt 1 ]; then
            echo "ERROR: More than one open molt; anti-cascade rule 1 violated"
            exit 1
          fi
          
          # Rule 3: At most K=3 molts open system-wide
          # (checked across all repos; this gate checks local repo)
          
          # Rule 4: Constant reverted twice in a row?
          reverts=$(grep "REVERT" MOLT_STATE.md | tail -n 2 | wc -l)
          if [ "$reverts" -eq 2 ]; then
            echo "ERROR: Constant reverted twice; frozen per anti-cascade rule 4"
            exit 1
          fi
          
          echo "PASS: Anti-cascade rules enforced"
      
      - name: "Prioritize molt by Priority Queue score"
        if: env.molt_detected == 'true'
        run: |
          # Check that molt candidate is highest-priority open item
          molt_priority=$(grep "priority_score" MOLT_STATE.md | head -n 1 | cut -d: -f2)
          echo "Molt priority score: $molt_priority"
      
      - name: "Create comment requesting Z2 ratification"
        if: env.molt_detected == 'true'
        run: |
          gh pr comment ${{ github.event.pull_request.number }} \
            --body "⚙️ Molt Candidate Detected (Decision 2d)\n\nZ2 ratification required before merge.\nCandidate: $(grep 'description' MOLT_STATE.md | head -n 1)\nHash pending: $(grep 'ratification_hash' MOLT_STATE.md)"
```

---

## Implementation Part 4: Falsifier Monitor

### Audit Checklist (Decision 2f: 10-item checklist, state-driven)

**File:** `.github/workflows/falsifier-monitor.yml`

```yaml
name: Oracle Falsifier Monitor (State-Driven)

on:
  schedule:
    - cron: '0 0 1 * *'  # Polling schedule: first day of each month, UTC (TECHNICAL_SAFETY timeout, not work deadline)
  workflow_dispatch:

jobs:
  falsifier_check:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: "Falsifier 1: Unknown claims in escalation state"
        run: |
          python3 -c "
            import json
            
            unknown_count = 0
            escalation_list = []
            
            with open('oracle_state.json') as f:
              oracle = json.load(f)
            
            for unknown in oracle.get('unknowns', []):
              # Query REGISTERED.md for escalation state per 2f falsifier
              # Elapsed-time logic replaced with state-tracked checks (not calendar-driven)
              escalation_state = unknown.get('escalation_state', 'ACTIVE')
              if escalation_state == 'ESCALATE_TO_Z2':
                unknown_count += 1
                escalation_list.append(f\"  - {unknown['description']} (state: ESCALATE_TO_Z2)\")
            
            if unknown_count > 0:
              print(f'FALSIFIER TRIPPED: {unknown_count} unknowns in escalation state')
              for item in escalation_list:
                print(item)
              exit(1)
            else:
              print('PASS: No unknowns in escalation state')
          "
      
      - name: "Falsifier 2: Unauthorized action threshold exceeded"
        run: |
          python3 -c "
            import json
            
            with open('oracle_state.json') as f:
              oracle = json.load(f)
            
            # Query REGISTERED.md for authorization state per Decision 2f
            # Elapsed-time logic replaced with state-tracked checks (not calendar-driven)
            unauthorized = [r for r in oracle.get('execution_receipts', [])
              if r['status'] == 'BLOCKED' and r.get('authorization_state') == 'UNAUTHORIZED']
            
            threshold = oracle.get('unauthorized_action_threshold', 1)
            if len(unauthorized) > threshold:
              print(f'FALSIFIER TRIPPED: {len(unauthorized)} unauthorized actions exceed threshold')
              for r in unauthorized:
                print(f\"  - {r['action_id']}: {r['reason']}\")
              exit(1)
            else:
              print(f'PASS: {len(unauthorized)} unauthorized actions (threshold: {threshold})')
          "
      
      - name: "Falsifier 3: Disagreement rate >30%"
        run: |
          python3 -c "
            import json
            
            with open('oracle_state.json') as f:
              oracle = json.load(f)
            
            disputed = [c for c in oracle.get('challenges', [])
              if 'disagreement' in c.get('reason', '').lower()]
            
            total_claims = len(oracle.get('claims', []))
            if total_claims == 0:
              print('PASS: No claims yet; disagreement rate N/A')
            else:
              rate = len(disputed) / total_claims
              if rate > 0.30:
                print(f'FALSIFIER TRIPPED: Disagreement rate {rate:.1%} >30%')
                print(f'  Disputed claims: {len(disputed)} / {total_claims}')
                exit(1)
              else:
                print(f'PASS: Disagreement rate {rate:.1%} <30%')
          "
      
      - name: "Falsifier 4-10: Manual review checklist"
        run: |
          cat > /tmp/falsifier_checklist.txt << 'CHECKLIST'
          [ ] Warrant chain integrity: all warrants have evidence_ids
          [ ] Precedent updates: any new precedents logged
          [ ] Amendment tracking: molt amendments reflected in MOLT_STATE
          [ ] Z2 signature validation: all ratification hashes present
          [ ] Receipt walk-back: execution receipts match claims in transcript
          [ ] Operator approval: all required-approval actions have operator sign-off
          [ ] Cross-substrate sync: Oracle matches REGISTERED.md HASH
          [ ] No-delegate list enforcement: HARD_NO_DELEGATE_LIST actions logged but not executed
          [ ] False positive rate: merge gate escalations validated by reviewer (≤15% false positive)
          [ ] Audit completeness: all events in NF_LEDGER, none missing
          CHECKLIST
          
          echo "Oracle falsifier checklist:"
          cat /tmp/falsifier_checklist.txt
          echo ""
          echo "ACTION: Z2 completes checklist and reports findings to Priority Queue (state-tracked execution)"
      
      - name: "Generate falsifier report"
        if: failure()
        run: |
          gh issue create \
            --title "🚨 Oracle Falsifier Alert" \
            --body "Oracle falsifier check detected issue.\n\nReview job logs: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}\n\nZ2 action required (state-tracked execution; no deadline)."
```

---

## Implementation Part 5: CI/CD Integration

### Stop Hook: Z2 Authorization Validation (Decision 2e: Hardcoded enforcement)

**File:** `.github/workflows/z2-authorization-gate.yml`

```yaml
name: Z2 Authorization Gate

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  verify_z2_authority:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: "Verify Z2 signature on all ratified actions"
        run: |
          python3 << 'PYTHON'
          import json, re
          
          AUTHORIZED_Z2 = {
              "carly.r.anderson@gmail.com": "canonical",
              "aioshuman@gmail.com": "authorized_business"
          }
          
          # Read oracle_state
          with open('oracle_state.json') as f:
              oracle = json.load(f)
          
          # Check all actions that require Z2 signature
          for action in oracle.get('actions', []):
              if action['human_approval_required']:
                  warrant = next((w for w in oracle['warrants'] 
                      if w['warrant_id'] == action['warrant']), None)
                  
                  if not warrant:
                      print(f"ERROR: Action {action['id']} missing warrant reference")
                      exit(1)
                  
                  if not warrant.get('z2_ratification_hash'):
                      print(f"ERROR: Action {action['id']} missing Z2 signature")
                      exit(1)
                  
                  # Validate hash format
                  if not re.match(r'sha256\([a-f0-9]{64}\)', warrant['z2_ratification_hash']):
                      print(f"ERROR: Action {action['id']} has invalid Z2 hash format")
                      exit(1)
          
          print("PASS: All Z2-required actions have valid signatures")
          PYTHON
      
      - name: "Enforce hard-no-delegate list (2e)"
        run: |
          python3 << 'PYTHON'
          import json
          
          HARD_NO_DELEGATE = [
              "AUTHORITY_GRANT",
              "DATA_DELETION",
              "CONSTITUTIONAL_AMENDMENT",
              "ESCALATION_DECISION",
              "Z_ROLE_ASSIGNMENT",
              "MOLLIFICATION",
              "FALSIFIER_OVERRIDE"
          ]
          
          with open('oracle_state.json') as f:
              oracle = json.load(f)
          
          # Scan all proposed actions
          for action in oracle.get('actions', []):
              if action.get('category') in HARD_NO_DELEGATE:
                  # These must have Z2 approval (checked above)
                  # and must be marked as requiring human approval
                  if not action.get('human_approval_required'):
                      print(f"ERROR: Action {action['id']} category {action['category']} must require human approval")
                      exit(1)
          
          print("PASS: Hard-no-delegate list enforced")
          PYTHON
```

---

## Success Criteria (§6 Process Review)

- [ ] oracle_state.json schema is complete and tracks all major claim/evidence/warrant/action categories
- [ ] Actualizer never auto-executes on DISPUTED or UNKNOWN warrants (2b-tested)
- [ ] Cross-substrate disagreement is marked DISPUTED + escalated (2c-tested)
- [ ] Molt procedure requires Z2 ratification; anti-cascade rules enforced (2d-tested)
- [ ] Hard-no-delegate list is hardcoded and prevents auto-execution (2e-tested)
- [ ] Falsifier monitor runs (state-driven); all 10 items audited (2f-tested)
- [ ] CI/CD gates enforce Z2 authorization on all required actions
- [ ] Execution receipts reconcile with claims in transcript (B.6 protocol)

---

## Next Steps

1. **Z2 reviews this spec** (you have it now)
2. **Z2 signs oracle state schema** with hash and timestamp
3. **Z3 (Copilot) implements:**
   - Oracle state schema in repository
   - Actualizer precondition logic in merge gate
   - Molt ratification CI/CD workflow
   - Falsifier monitor (state-driven automation + manual checklist)
   - Z2 authorization gate
   - Execution receipt logging to NF_LEDGER
4. **Process review (4 weeks out):** Measure whether oracle derivative model holds; whether Actualizer preconditions blocked inappropriate actions; whether falsifier monitor caught edge cases

---

**Document Version:** 1.0  
**Z2 Authority:** Night  
**Status:** AWAITING Z2 RATIFICATION SIGNATURE
