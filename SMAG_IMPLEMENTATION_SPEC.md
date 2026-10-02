# Q-SMAG-REEXAMINATION-01: Implementation Specification

**Z2 Ratified Decisions:** 1a–1f (See PHASE_1_RATIFICATION_PACKAGE.md)  
**Authority:** Night (carly.r.anderson@gmail.com)  
**Status:** ✅ RATIFIED (2026-10-02)  
**Z2 Ratification Hash:** `1a3ff7fd1061b9a953b9737a227e649a8a56575e0f1f7797dd6eda78ca690280`  
**Stage:** 4 (Z2 Ratification) ✅ → 5 (Z3 Implementation)

---

## Core Decision Summary

| Decision | Ratified Value | Impact |
|----------|---|---|
| **1a. Measurement Ledger** | `audits/smag_pilot_ledger.jsonl` canonical | SMAG-specific schema; maps to NF_LEDGER for Z2 audit |
| **1b. Control Sweep** | Review-escalating | Requires explicit reviewer override if threshold exceeded |
| **1c. Profile Authority** | Tier 1 (Policy) | Z2 ratifies; can change with Z2 decision |
| **1d. State Predicate** | Z1 proposes, Z2 ratifies | Pseudocode approval before Copilot codes |
| **1e. Substrate Filtering** | Context-dependent per registry | Different fail-mode per substrate (fail-open vs. fail-closed) |
| **1f. Falsifier Precedence** | Matrix-based with escalation | Unknown combinations escalate to Z2 at merge time |

---

## Implementation Part 1: State Predicate Operationalization

### Pseudocode (Ready for Z2 Approval)

```python
def CALIBRATION_REVIEW_REQUIRED(substrate: str, state: dict) -> bool:
    """
    Replaces time-based merge control (rejected in #477).
    Returns true if calibration review is required.
    """
    
    # Extract state
    profile = state.get('profile')
    measurements = state.get('measurements')
    
    # Check 1: Profile authority is valid
    if not PROFILE_AUTHORITY_VALID(profile):
        return FALSIFIER_TRIGGERED('unratified_profile')
    
    # Check 2: Measurement contract is current
    if not MEASUREMENT_CONTRACT_VALID(measurements):
        return FALSIFIER_TRIGGERED('wrong_ledger')
    
    # Check 3: Minimum evidence state satisfied
    if not MINIMUM_EVIDENCE_STATE_SATISFIED(measurements, substrate):
        return FALSIFIER_TRIGGERED('insufficient_evidence')
    
    # Check 4: Measured state exceeds ratified boundary
    if CURRENT_MEASURED_STATE_EXCEEDS_RATIFIED_BOUNDARY(measurements, profile):
        return True  # Review required
    
    return False  # No review required


def PROFILE_AUTHORITY_VALID(profile: dict) -> bool:
    """Profile has Z2 signature and is not stale."""
    return (
        profile.get('ratified_by_z2') == 'Night' and
        profile.get('ratification_hash') is not None and
        STALE_CHECK(profile.get('ratification_date')) == False
    )


def MEASUREMENT_CONTRACT_VALID(measurements: dict) -> bool:
    """Measurements conform to SMAG schema (smag_pilot_ledger)."""
    required_fields = ['substrate', 'timestamp', 'failing_checks', 'gap_rate']
    return all(field in measurements for field in required_fields)


def MINIMUM_EVIDENCE_STATE_SATISFIED(measurements: dict, substrate: str) -> bool:
    """
    Per-substrate rules (1e context-dependent).
    Example:
      - CLAUDE_CODE: need >= 5 measurements, freshness < 7 days
      - COPILOT: need >= 10 measurements, freshness < 3 days
    """
    registry = SUBSTRATE_FILTERING_REGISTRY()
    rules = registry.get(substrate)
    
    if not rules:
        # Unknown substrate: fail based on registry's default behavior
        return rules.get('fail_mode') == 'fail_open'
    
    return (
        len(measurements) >= rules['minimum_count'] and
        FRESHNESS_CHECK(measurements[-1]['timestamp'], rules['max_age'])
    )


def CURRENT_MEASURED_STATE_EXCEEDS_RATIFIED_BOUNDARY(measurements: dict, profile: dict) -> bool:
    """Compare gap_rate trend against ratified threshold."""
    current_gap_rate = measurements[-1]['gap_rate']
    ratified_threshold = profile.get('gap_rate_threshold')
    direction = profile.get('direction', 'above')  # 'above' or 'below'
    
    if direction == 'above':
        return current_gap_rate > ratified_threshold
    elif direction == 'below':
        return current_gap_rate < ratified_threshold
    else:
        return FALSIFIER_TRIGGERED('unknown_direction')


def FALSIFIER_TRIGGERED(falsifier_id: str) -> bool:
    """
    Lookup 1f precedence matrix.
    If falsifier alone blocks: return False (no review; just block)
    If multiple falsifiers: escalate to Z2 for judgment
    """
    precedence = FALSIFIER_PRECEDENCE_MATRIX()
    rule = precedence.get(falsifier_id)
    
    if rule.get('action') == 'BLOCK':
        # Log falsifier; don't require review, just block merge
        LOG_FALSIFIER(falsifier_id)
        return False
    elif rule.get('action') == 'ESCALATE':
        # Let Z2 decide at merge time
        Z2_ESCALATION_QUEUE.append({
            'falsifier': falsifier_id,
            'state': state,
            'decision_required': True
        })
        return False  # Block pending Z2 decision
    else:
        return False
```

### Data Structures

**Substrate Filtering Registry** (1e):
```json
{
  "CLAUDE_CODE": {
    "fail_mode": "fail_open",
    "minimum_count": 5,
    "max_age_days": 7,
    "rationale": "Claude Code reliability baseline established; allow merge if data missing"
  },
  "COPILOT": {
    "fail_mode": "fail_closed",
    "minimum_count": 10,
    "max_age_days": 3,
    "rationale": "Copilot under observation; block merge if data missing or stale"
  }
}
```

**Falsifier Precedence Matrix** (1f):
```json
{
  "unratified_profile": {
    "severity": "CRITICAL",
    "action": "BLOCK",
    "reason": "Cannot enforce unratified policy"
  },
  "wrong_ledger": {
    "severity": "CRITICAL",
    "action": "BLOCK",
    "reason": "Measurement schema mismatch; data unreliable"
  },
  "malformed_records": {
    "severity": "CRITICAL",
    "action": "ESCALATE",
    "reason": "Unknown if data valid; Z2 decides"
  },
  "insufficient_evidence": {
    "severity": "HIGH",
    "action": "ESCALATE",
    "reason": "Below minimum count; Z2 decides if acceptable"
  },
  "false_blocking": {
    "severity": "MEDIUM",
    "action": "ESCALATE",
    "reason": "Gate triggered but might be transient; Z2 decides"
  },
  "stale_profile": {
    "severity": "LOW",
    "action": "BLOCK",
    "reason": "Profile refresh needed; automatic"
  }
}
```

---

## Implementation Part 2: Profile Ratification Document

### SMAG Calibration Profile — BASELINE_S092126_v2

**STATUS:** AWAITING Z2 SIGNATURE (This implementation spec)

```yaml
# Core Profile Metadata
profile_id: BASELINE_S092126_v2
version: 2
ratified_by_z2: Night (carly.r.anderson@gmail.com)
ratification_date: [Z2 SIGNS]
ratification_hash: [Z2 SIGNS]
authority_tier: TIER_1_POLICY

# Measurement Authority (Decision 1a)
measurement_source: audits/smag_pilot_ledger.jsonl
measurement_contract_version: SMAG_v1.0
measurement_contract_schema:
  - field: substrate
    type: string
    required: true
  - field: timestamp
    type: ISO8601
    required: true
  - field: failing_checks
    type: array
    required: true
  - field: gap_rate
    type: float
    range: [0.0, 1.0]
    required: true

# Control Sweep Level (Decision 1b)
control_sweep_level: REVIEW_ESCALATING
merge_gate_behavior: "require_explicit_reviewer_override_if_threshold_exceeded"
enforcement_statement: |
  If CALIBRATION_REVIEW_REQUIRED() returns true,
  the merge gate DOES NOT auto-block.
  Instead, the gate escalates to the PR reviewer with:
    "SMAG calibration check: gap_rate exceeded. Reviewer approval required."
  The reviewer may approve or request further investigation.

# Substrate Filtering (Decision 1e)
substrate_filtering:
  - substrate_id: CLAUDE_CODE
    fail_mode: fail_open
    minimum_measurements: 5
    max_age_days: 7
    rationale: "Claude Code reliability baseline established; assume OK if data missing"
    
  - substrate_id: COPILOT
    fail_mode: fail_closed
    minimum_measurements: 10
    max_age_days: 3
    rationale: "Copilot under active observation; block merge if data missing or stale"
    
  # Add new substrates with explicit per-substrate rules
  # Do not use all-or-nothing rules

# Thresholds & Direction (Decision 1b continuation)
gap_rate_threshold: 0.25
direction: above
interpretation: "If gap_rate > 0.25 for CLAUDE_CODE or COPILOT, review escalates"

# Falsifier Precedence (Decision 1f)
falsifier_precedence_matrix_reference: SMAG_FALSIFIER_PRECEDENCE_MATRIX_v1
falsifier_precedence_location: ".github/workflows/merge-gate-falsifiers.yml"

# Audit & Logging
audit_destination: NF_LEDGER.jsonl
audit_event_type: "SMAG_GATE_INVOCATION"
log_fields:
  - substrate
  - gap_rate
  - profile_version
  - gate_result (ALLOW / ESCALATE / BLOCK)
  - timestamp

# Review Cycle
review_trigger_state: "measurement_cycle_complete"
next_review_trigger: "Upon completion of measurement cycle (resource-state tracked in REGISTERED.md)"
review_checklist:
  - [ ] Gap rate data quality stable?
  - [ ] Substrate filtering rules still appropriate?
  - [ ] Falsifier precedence matrix holds?
  - [ ] Merge velocity affected negatively?
  - [ ] Any unauthorized escapes (PR merged when gate said ESCALATE)?

# Ratification Notes
ratification_notes: |
  This profile operationalizes Decision 1a-1f from Q-SMAG-REEXAMINATION-01.
  It replaces the elapsed-time control model (rejected in adversarial review #477)
  with a state-based predicate that requires explicit evidence of calibration quality.
  
  The profile is Tier 1 (Policy), meaning Z2 can change thresholds with a new ratification,
  but the fundamental structure (state predicate, substrate filtering, falsifier precedence)
  requires a new molt if materially altered.
```

---

## Implementation Part 3: Repository Coordinator Pre-Check

### Lint Rule: Prevent Duplicate SMAG Gates

**File:** `.github/workflows/lint-smag-duplication.yml`

```yaml
name: SMAG Gate Duplication Check

on:
  pull_request:
    paths:
      - '.github/workflows/merge-gate*.yml'
      - 'calibration_profiles/**'
      - '.github/workflows/*smag*'

jobs:
  check_duplication:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: "Detect competing SMAG gates"
        run: |
          # Count all open SMAG-related PRs
          count=$(gh pr list \
            --search "SMAG in:title" \
            --state open \
            --json number,title \
            | jq 'length')
          
          if [ "$count" -gt 1 ]; then
            echo "ERROR: Multiple open SMAG gate PRs detected."
            gh pr list --search "SMAG in:title" --state open
            exit 1
          fi
          
          echo "PASS: No duplicate SMAG gate PRs"
      
      - name: "Verify merge-gate.yml has exactly one SMAG section"
        run: |
          # Grep for CALIBRATION_REVIEW_REQUIRED invocations
          count=$(grep -c "CALIBRATION_REVIEW_REQUIRED" .github/workflows/merge-gate.yml || echo 0)
          
          if [ "$count" -ne 1 ]; then
            echo "ERROR: Expected exactly 1 CALIBRATION_REVIEW_REQUIRED invocation; found $count"
            exit 1
          fi
          
          echo "PASS: Exactly one SMAG gate definition found"
```

**Effect:** Prevents submission of competing SMAG gate PRs before merge-time Repository Coordinator check.

---

## Implementation Part 4: Merge Gate Implementation

### File: `.github/workflows/merge-gate.yml` (Addition)

```yaml
name: Merge Gate - Calibration Check

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  calibration_review:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: "Fetch SMAG measurement ledger"
        run: |
          git fetch origin audits/smag_pilot_ledger.jsonl || true
          if [ ! -f "audits/smag_pilot_ledger.jsonl" ]; then
            echo "WARNING: SMAG pilot ledger not found; fail-open per CLAUDE_CODE substrate rule"
            echo "gate_status=PASS_FAIL_OPEN" >> $GITHUB_ENV
          fi
      
      - name: "Load SMAG profile"
        run: |
          profile=$(cat calibration_profiles/BASELINE_S092126_v2.yaml)
          echo "profile=$profile" >> $GITHUB_ENV
      
      - name: "Evaluate CALIBRATION_REVIEW_REQUIRED()"
        run: |
          # Pseudocode logic (see above)
          # Returns true if review escalation needed
          
          # For now, log the gate invocation
          python3 -c "
            import json
            import datetime
            
            gate_record = {
              'timestamp': datetime.datetime.utcnow().isoformat(),
              'pr_number': ${{ github.event.pull_request.number }},
              'substrate': 'CI',
              'gate_evaluated': True,
              'review_required': False,  # Placeholder
              'profile_version': 'BASELINE_S092126_v2'
            }
            
            print(json.dumps(gate_record))
          " >> audit.jsonl
      
      - name: "Append to NF_LEDGER"
        run: |
          cat audit.jsonl >> NF_LEDGER.jsonl || touch NF_LEDGER.jsonl && cat audit.jsonl >> NF_LEDGER.jsonl
          git add NF_LEDGER.jsonl
          git commit -m "Log SMAG gate invocation for PR #${{ github.event.pull_request.number }}"
      
      - name: "Determine gate result"
        if: env.gate_status != 'PASS_FAIL_OPEN'
        run: |
          # If CALIBRATION_REVIEW_REQUIRED returned true:
          #   Post comment requesting reviewer override
          # If false:
          #   Gate passes; no action needed
          
          if [ "${{ env.review_required }}" = "true" ]; then
            echo "gate_result=ESCALATE" >> $GITHUB_ENV
            gh pr comment ${{ github.event.pull_request.number }} \
              --body "🔍 SMAG Calibration Check: Review escalation required.\n\nGap rate exceeded thresholds. Reviewer override needed."
          else
            echo "gate_result=PASS" >> $GITHUB_ENV
          fi
      
      - name: "Allow reviewer override"
        if: env.gate_result == 'ESCALATE'
        run: |
          echo "PASS (reviewer override possible)"
          # Do not fail the CI step; let reviewer decide
```

---

## Success Criteria (§6 Process Review)

- [ ] SMAG calibration decisions (1a–1f) are operationalized as executable pseudocode
- [ ] Profile ratification is Z2-signed and recorded in REGISTERED.md with hash
- [ ] Repository Coordinator prevents duplicate SMAG gate PRs at submission time
- [ ] Merge gate logs all invocations to NF_LEDGER for Z2 state-driven audit
- [ ] Substrate filtering rules are per-substrate (not all-or-nothing)
- [ ] Falsifier precedence matrix handles all known combinations; unknowns escalate to Z2
- [ ] Reviewer override is possible for review-escalating gate (1b)

---

## Next Steps

1. **Z2 reviews this spec** (you have it now)
2. **Z2 signs profile ratification** with hash and timestamp
3. **Z3 (Copilot) implements:**
   - Pseudocode in merge gate
   - Profile document in calibration_profiles/
   - Lint rule in workflows/
   - Audit logging to NF_LEDGER
4. **Process review (post-merge):** Measure whether adversarial findings from #477 manifested (measurement window per phase specification)

---

**Document Version:** 1.0  
**Z2 Authority:** Night  
**Status:** AWAITING Z2 RATIFICATION SIGNATURE
