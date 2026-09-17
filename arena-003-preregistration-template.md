# ARENA-003 Preregistration Template

**Purpose:** SOLO measurement protocol with mechanical output validation (fixes ARENA-002 output-channel defect)  
**Status:** Draft (awaiting Z2 ratification)  
**Version:** 1.0  
**Date:** 2026-09-17

---

## Protocol Changes from ARENA-002

### Output-Channel Validation (BREAKING CHANGE)

**ARENA-002 defect:** Copilot created zero-file PRs; complete outputs in body summaries only.

**ARENA-003 requirement:** All participant outputs must be mechanically validated BEFORE run freeze.

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

## Timeline

- **ARENA-003 Protocol Ratified:** Pending Z2 decision (Night)
- **First ARENA-003 task:** After close of ARENA-002
- **Mechanical validator deployed:** `.arena-control/validate-output.py` + schema files
- **Round A target:** N=5 pairs (mixed substrates: Copilot, Claude, GPT-4)
- **Round B unlock:** Post-ARENA-003 analysis + independent audit

---

*Template drafted by Claude Z1; awaiting Z2 ratification.*
*Reference: arena-validity-and-confounds.md (Mitigation for ARENA-003)*
