# INTENT-OS RNOLA Integration: Theory and Governance

**Status:** Ratified (Q-INTENT-OS-RNOLA-INTEGRATION-01)  
**Last Updated:** 2026-09-25  
**Audience:** Z1 (proposers), Z2 (ratifiers), Z3 (executors), operators using RNOLA  
**Related:** `tools/skills/repository_native_operator_learning/SKILL.md`, `docs/RNOLA_FAILURE_MODES.md`

---

## 1. Conceptual Foundation

### What is RNOLA?

Repository-Native Operator Learning Audit (RNOLA) is an **advisory Zone 1 learning and calibration layer** that sits atop INTENT-OS governance infrastructure. RNOLA teaches repository operators by analyzing real artifacts in real context—exact commit SHAs, actual diffs, live CI results, and concrete evidence—rather than abstract curricula.

RNOLA's core premise:

> An operator who understands the actual repository artifact under review can make safer independent decisions than one who relies on AI interpretation alone.

### Authority Boundaries (Hard Constraints)

RNOLA **has NO authority** to:
- Merge or approve pull requests
- Ratify governance decisions (Z2 acts)
- Execute deployments (Z3 acts)
- Grant permissions or sign artifacts
- Treat an operator-check record as authorization
- Bypass Z2 or Z3 decision boundaries

RNOLA **is designed to**:
- Teach repository context and mechanics
- Calibrate operator understanding against evidence
- Generate advisory learning records (operator-checks)
- Identify evidence gaps and knowledge risks
- Support (not replace) Z2/Z3 decision-making

### Integration with INTENT-OS Layers

```
┌─────────────────────────────────────────────────────────────┐
│ INTENT-OS Layered Architecture                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Z2 (Ratification Layer)      ← Authority & final decisions │
│  Z3 (Execution Layer)          ← Implementation & results    │
│  ─────────────────────                                       │
│  RNOLA (Learning Layer)        ← OPERATOR CALIBRATION ONLY  │
│  (advisory, Zone 1 only)                                     │
│                                                              │
│  Repository Artifacts          ← Commit, PR, CI, tests      │
│  (immutable, versioned)                                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

RNOLA sits **below** ratification and execution. It reads from repository artifacts and emits learning records (operator-checks), but cannot itself decide, authorize, or execute.

---

## 2. Operator-Check Records (Learning Evidence)

### Anatomy of an Operator-Check

An operator-check is a structured learning record that documents:

```json
{
  "version": "intentos/operator_check_v1",
  "ref": "64c26cb058cf20eb5145c5ccfb9d4cc9c929871f",
  "subject": "humanaios-ui/operations#538",
  "evidence_inspected": [
    "PR-538#comment-123456",
    "commit:64c26cb058cf20eb5145c5ccfb9d4cc9c929871f",
    "file:schemas/intent_os_operator_check_v1.schema.json:line:42"
  ],
  "observation": "Schema validation includes const constraints on advisory_only=true, can_authorize=false, ensuring operator-checks cannot be misused as merge authorization.",
  "calibration": {
    "demonstrated": ["understands schema hard constraints", "can identify boundary violations"],
    "partial": ["schema composition patterns"],
    "not_tested": [],
    "unknown": []
  },
  "by": "claude",
  "at": "2026-09-25T18:00:00Z"
}
```

**Key properties:**
- `ref`: Git SHA of the artifact under review (not a branch name)
- `subject`: What the operator learned about (PR/issue/commit)
- `evidence_inspected`: Exact, line-specific references to evidence
- `observation`: What was learned (free text, ≥10 chars, no placeholders)
- `calibration`: Evidence-based assessment of operator understanding
- `advisory_only`: is constrained to true by schema validation; not treated as authorization
- `can_authorize`: is constrained to false by schema validation; does not satisfy merge gates

### What Operator-Checks Are NOT

Operator-checks are **explicitly not**:
- Approval or review votes
- Authorization signatures
- Merge gate credentials
- Sufficient grounds for Z2 ratification
- Proof of code safety or correctness

An operator-check says: *"I taught this operator, and they demonstrated understanding of X. Whether that understanding is sufficient for this decision is up to governance."*

---

## 3. Failure Modes and Detection

RNOLA fails when boundaries blur. Eight documented failure modes:

| Mode | Detection | Mitigation |
|:-----|:----------|:-----------|
| **Operator-check as authorization** | `can_authorize=true` or used in merge gate | Schema const, CI gate, zone enforcement |
| **Checkbox patterns** | "☑ approved" in observation field | minLength validation, semantics review |
| **Evidence without specificity** | Generic "PR-999" instead of "PR-999#comment-123456" | Regex pattern enforcement in schema |
| **Cognitive load increase** | Operator skips reading actual artifacts | Teach-back requirement, falsifier doctrine |
| **Authority boundary obscured** | References to "ratification" or "decision" | $comment annotations, boundary statement |
| **Unaudited scaling** | Multiple concurrent RNOLA runs without coordination | Operator cap, context limit checks |
| **Z3 executor bleed** | RNOLA records treated as deployment approval | CI gate rejects execution without Z2 hash |
| **Undefined witness ledger** | Operator-checks linked to governance without separate Z2 decision | `linked_to_witness_ledger` default false, requires explicit signal |

Full analysis: `docs/RNOLA_FAILURE_MODES.md`

---

## 4. CI/CD Integration

### Validation Gates

Three new governance tools enforce RNOLA boundaries:

| Tool | Location | Function | Gate? |
|:-----|:---------|:---------|:------|
| `enforce_z2_z3_boundary.py` | scripts/ | Blocks operator-checks with authority overreach | YES (added to tool-manifest gate) |
| `lint_canonical_skills.py` | scripts/ | Validates SKILL.md canonical implementations | YES (scans substrate drift) |
| `scan_rnola_misuse.py` | scripts/ | Detects falsifier violations in records | YES (runs on PR events) |

### How These Are Invoked

1. **PR merge gate** (`.github/workflows/tool-manifest.yml`):
   - Runs `enforce_z2_z3_boundary.py` on all changed schema files
   - Validates no `can_authorize=true` or advisory misuse
   - Blocks merge if boundary violation detected

2. **Skill registration gate** (`.github/workflows/skills.yml`):
   - Runs `lint_canonical_skills.py` on any SKILL.md changes
   - Ensures substrate stubs match canonical implementation
   - Catches drift between .claude/, .agents/, tools/skills/

3. **RNOLA event scanner** (`.github/workflows/governance.yml` Phase 2):
   - Runs `scan_rnola_misuse.py` on PR records
   - Detects falsifier patterns (checkbox usage, undefined artifacts)
   - Flags stale records or generic observations

---

## 5. Operator Responsibilities

An operator using RNOLA must:

1. **Read the actual artifact**, not just the RNOLA summary
2. **Verify evidence locations** against the repository  
3. **Distinguish observation from inference** in teach-backs
4. **Request Z2/Z3 decision** when governance is unclear
5. **Report understanding gaps** if they emerge during merge
6. **Never skip** governance checks because "RNOLA said it's safe"

---

## 6. Examples

### Example 1: Schema Validation (PR #538)

**Learning Object:** `schemas/intent_os_operator_check_v1.schema.json`

**Operator-Check Generated:**
```json
{
  "ref": "64c26cb058cf20eb5145c5ccfb9d4cc9c929871f",
  "subject": "PR-538",
  "observation": "Schema enforces const: advisory_only=true and can_authorize=false on all operator-checks. Pattern also validated: ref field requires SHA (7-40 hex chars), rejecting branch names. Minimum observation length set to 10 chars to discourage placeholder evidence.",
  "evidence_inspected": [
    "PR-538#comment-12345 (review comment discussing schema constraint rationale)",
    "file:schemas/intent_os_operator_check_v1.schema.json:line:18-25 (const definitions)",
    "file:tests/test_intent_os_operator_check_schema.py:line:45-67 (test demonstrating violation detection)"
  ],
  "calibration": {
    "demonstrated": ["understands why const is used for authority boundary", "can read JSON schema patterns"],
    "partial": [],
    "not_tested": ["composing schemas with allOf"],
    "unknown": []
  }
}
```

This operator-check documents that the operator understands the boundary mechanism. Whether the schema is "correct" is a separate Z2 question.

### Example 2: Authority Boundary (PR #534)

**Learning Object:** `tools/skills/repository_native_operator_learning/SKILL.md`

**Operator Teach-Back (Before Merge):**  
*"This PR adds validation that RNOLA operator-checks have `can_authorize=false`. That stops someone from treating an operator-check as a merge vote."*

**RNOLA Calibration:**
- **Demonstrated:** Operator understands the boundary violation this prevents
- **Partial:** Operator unclear on what happens when violation is detected
- **Unknown:** Operator hasn't yet reviewed the CI gate that enforces this

**Recommendation to Z2:**  
Operator has demonstrated sufficient understanding of the boundary. The partial gap (gate behavior) is resolved by the existing test suite and documentation. Safe for Z2 review/ratification.

---

## 7. Falsifier Doctrine

RNOLA is working if:
- Operator understanding grows without skipping evidence
- Operator can explain merge consequences independently
- Required AI interpretation decreases as complexity grows
- Cognitive load per evidence-bearing decision decreases

RNOLA is failing if:
- Operator repeats "RNOLA said X" without reading artifacts
- Operator cannot explain CI/test/deployment distinctions
- Vocabulary grows but ability to trace code doesn't
- Operator delegates decisions without independent causal understanding

---

## 8. Ratification Status

This integration document is **ratified** under:
- **Decision:** Q-INTENT-OS-RNOLA-INTEGRATION-01
- **Ratifier:** Z2 (Night)
- **Authority:** Governance boundary definition between Zone 1 learning and Zone 2 ratification
- **Falsifier:** Any operator-check treated as authorization in live PR merge gate (violation triggers immediate remediation candidate)

---

## 9. Next Steps for Operators

1. Read `tools/skills/repository_native_operator_learning/SKILL.md` (operational guide)
2. Review `docs/RNOLA_FAILURE_MODES.md` (what can go wrong)
3. Inspect a recent operator-check in `outputs/rnola/` (see the record format)
4. Ask RNOLA to teach you a real artifact in this repository
5. Calibrate your understanding against the actual code/PR/test
6. Request Z2 review when governance questions arise

---

**End of RNOLA Integration Document**
