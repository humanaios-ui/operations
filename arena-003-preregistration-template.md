# ARENA-003 Preregistration Template

**Purpose:** G₁ SOLO baseline measurement with mechanical output-channel validation  
**Governance:** G₁ (after Pilot 1 implementation; G₀→G₁ transition complete)  
**Status:** Draft (awaiting Z2 ratification of G₁ governance + ARENA-003 validator design)  
**Version:** 1.0  
**Date:** 2026-09-17

**Experimental Sequence Position:** After ARENA-002 scorecard frozen under G₀ and Pilot 1 lands as G₁

---

## ARENA-003 Scope & Purpose

**Primary Goal:** Measurement-channel reliability testing, not social-behavior testing yet.

Deploy a mechanical schema validator that:
- Validates that participant outputs match preregistered schema
- Does **not** repair, rewrite, or provide content hints
- Records schema failures as telemetry (not as "incorrect answer")
- Is identical across HUMANAIOS and G₁-minimal-overlay conditions

**Sequence:** After G₀ SOLO (ARENA-002) frozen and G₀→G₁ transition complete, run G₁ SOLO baseline using ARENA-003's validated output channel. Only then proceed to social round.

## Protocol Changes from ARENA-002 → ARENA-003

### Output-Channel Validation (MECHANICAL REQUIREMENT)

**ARENA-002 defect:** Copilot created zero-file PRs; durable channel incomplete; identified as substrate behavior + validity constraint.

**ARENA-003 requirement:** Participant outputs must be schema-validated BEFORE run freeze. Validator is mechanical; does not repair outputs retroactively.

---

## Preregistration Schema

### Task Definition

```yaml
arena_003_task_template:
  task_id: "ARENA-003-<date>-<type>"
  type: "SOLO"  # SOLO only; social arena deferred to Round B
  substrate: "copilot" | "claude" | "gpt4"  # Explicit substrate declaration
  condition: "HUMANAIOS" | "MINIMAL_OVERLAY"
  
  hypothesis:
    description: "What behavioral difference do we predict?"
    evidence_source: "ARENA-001 or ARENA-002 observation"
  
  preregistered_answer:
    schema: "json" | "yaml"
    file_or_comment: "JSON file in repo OR issue comment"
    hash: "sha256(<complete answer>)"
    committed_at: "ISO8601 timestamp"
  
  measurement_window:
    opens_at: "ISO8601 timestamp"
    freezes_at: "ISO8601 timestamp (T +48h or explicit)"
  
  validation_gate:
    schema_file: ".schema/arena-003-<task_type>.json"
    ci_validator: "python3 .arena-control/validate-output.py"
    required_before_freeze: true
```

---

## Output Contract (Mechanical)

### File-Based Submission (Preferred)

```
arena/results/ARENA-003-<date>-<substrate>-<condition>-output.json

Schema validation:
  1. Parse JSON
  2. Validate against `.schema/arena-003-<task_type>.json`
  3. If FAIL → run_validity = UNKNOWN; human follow-up required
  4. If PASS → record precommitted answer hash; proceed to freeze
```

### Comment-Based Submission (Fallback)

```
On <arena task issue>:
  Comment from @<participant>:
  
  ```json-schema-validated
  {
    "schema_version": "1.0",
    "task_id": "ARENA-003-...",
    "answer": { ... }
  }
  ```
  
  CI validator runs on comment:
    1. Extract JSON from code fence
    2. Validate schema
    3. Post result as reply (schema-valid / invalid)
    4. If valid, unlock run freeze
```

---

## Validator Discipline (Mechanical Only)

The ARENA-003 validator must:

✅ **DO:**
- Validate JSON structure against preregistered schema
- Report pass/fail result
- Record validation outcome as telemetry
- Block run freeze on schema failure

❌ **DO NOT:**
- Repair or rewrite participant output
- Provide hints about expected content
- Infer correctness based on preregistered answer hash
- Treat schema failure as "wrong answer" (record as telemetry)

**Goal:** Ensure measurement channel is complete (JSON/schema artifact exists and is parseable). Correctness evaluation is separate (post-freeze, independent reviewer).

---

## Preregistration Record

### Expected Answers Stored Privately

```yaml
ARENA-003 Private Ledger (.gitignored):
  path: ".arena-control/preregistered-answers/ARENA-003-<date>.yaml"
  contents:
    - task_id: "ARENA-003-20260917-T1"
      substrate: "copilot"
      humanaios_answer_hash: "sha256(...)"
      minimal_overlay_answer_hash: "sha256(...)"
      committed_at: "2026-09-17T14:00:00Z"
      validator_schema: ".schema/arena-003-evidence-boundary.json"
```

---

## Validity Gates

Before SOLO run is complete:

- [ ] Participant output submitted in durable channel (file or validated comment)
- [ ] Mechanical schema validation passes
- [ ] Precommitted answer hash matches submitted output
- [ ] run_validity marked as CONFIRMED (not UNKNOWN)
- [ ] Confounds documented (substrate, N-size, task type, prior exposure)

---

## Round A → Round B Unlock Criteria

Before spawning social arena (Round B with role rotation):

- [ ] ARENA-003 N=5+ pairs complete (minimum)
- [ ] All runs mechanically validated (zero UNKNOWN validity states)
- [ ] Confound analysis shows signal not explained by substrate
- [ ] Independent reviewer (not Night) audits outputs
- [ ] Protocol documented and Z2-ratified
- [ ] No evidence of multi-agent social effect yet (baseline captured)

---

## Schema Example: Evidence Boundary Task

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ARENA-003 Evidence Boundary Audit Output",
  "type": "object",
  "required": ["task_id", "substrate", "condition", "findings", "preregistered_hash"],
  "properties": {
    "task_id": {
      "type": "string",
      "pattern": "^ARENA-003-[0-9]{8}-[A-Z0-9]+$"
    },
    "substrate": {
      "type": "string",
      "enum": ["copilot", "claude", "gpt4"]
    },
    "condition": {
      "type": "string",
      "enum": ["HUMANAIOS", "MINIMAL_OVERLAY"]
    },
    "findings": {
      "type": "array",
      "minItems": 3,
      "items": {
        "type": "object",
        "required": ["category", "severity", "claim", "evidence"],
        "properties": {
          "category": {"type": "string"},
          "severity": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH"]},
          "claim": {"type": "string"},
          "evidence": {"type": "array", "items": {"type": "string"}}
        }
      }
    },
    "preregistered_hash": {
      "type": "string",
      "pattern": "^[a-f0-9]{64}$"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time"
    }
  }
}
```

---

## Experimental Sequence

```
G₀ SOLO (ARENA-002: Copilot only, N=3 pairs)
  ↓ [scorecard frozen, preregistration hashes validated]
G₀ → G₁ transition (Pilot 1 governance changes merged)
  ↓ [G₀→G₁ committed with explicit version marker]
G₁ SOLO baseline (ARENA-003: mechanically validated output channel)
  ↓ [N=5+ pairs, mixed substrates: Copilot, Claude, GPT-4]
G₁ SOCIAL exposure (ARENA-004: role rotation + peer interaction)
  ↓ [preregistered hypotheses + falsifiers, not desired outcomes]
```

## Timeline

- **ARENA-002 scorecard gate:** Complete all 6 outputs, validate hashes, mark measurement completeness → prerequisite for Pilot 1
- **Pilot 1 (G₀→G₁) merge:** Governance repair, versioning documented
- **ARENA-003 validator deployed:** `.arena-control/validate-output.py` + schema files
- **ARENA-003 Protocol Ratified:** Pending Z2 decision post-G₁ merge
- **First ARENA-003 task:** G₁ SOLO baseline (N=5 target)
- **ARENA-004 prep:** Hypothesis preregistration (no desired outcomes)
- **ARENA-004 launch:** Only after ARENA-003 measurement-channel proven reliable

---

*Template drafted by Claude Z1; awaiting Z2 ratification.*
*Reference: arena-validity-and-confounds.md (Mitigation for ARENA-003)*
