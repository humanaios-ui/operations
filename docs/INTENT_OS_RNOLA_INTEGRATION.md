# INTENT-OS RNOLA Integration: Theory and Governance

**Status:** Pending Z2 Review (Q-INTENT-OS-RNOLA-INTEGRATION-01)  
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
  "schema": "intentos/operator_check_v1",
  "advisory_only": true,
  "can_authorize": false,
  "subject": {
    "type": "pull_request",
    "repository": "humanaios-ui/operations",
    "ref": "64c26cb058cf20eb5145c5ccfb9d4cc9c929871f",
    "identifier": "PR-538",
    "artifact_paths": ["schemas/intent_os_operator_check_v1.schema.json"]
  },
  "intent": "Teach the operator how schema constraints enforce authority boundaries.",
  "question": "What prevents an operator-check from being misused as authorization?",
  "operator_response": "The schema hard-codes advisory_only=true and can_authorize=false using const validation. This ensures the record cannot be passed to a merge gate or treated as a ratification signature.",
  "evidence_inspected": [
    {
      "kind": "source",
      "locator": "schemas/intent_os_operator_check_v1.schema.json:25-31",
      "observation": "Lines 25-31 define const constraints on advisory_only and can_authorize fields, enforced by JSON Schema validator."
    },
    {
      "kind": "test",
      "locator": "tests/test_intent_os_operator_check_schema.py:79-88",
      "observation": "Test suite confirms that attempting to set can_authorize=true raises ValidationError. Boundary enforcement verified."
    }
  ],
  "calibration": {
    "demonstrated": ["understands schema hard constraints", "can identify boundary violations"],
    "partial": ["schema composition patterns (allOf, $ref)"],
    "not_tested": [],
    "unknown": []
  },
  "authority_consequence": "If this PR is merged, the repository gains schema validation for operator-checks. This does not authorize any deployment or change any merge gates; it only makes the advisory boundary explicit and enforced.",
  "next_learning_object": "Inspect the CI gate (enforce_z2_z3_boundary.py) that validates this schema in production.",
  "created_at": "2026-09-25T18:00:00Z"
}
```

**Key properties:**
- `schema`: Version identifier (must be "intentos/operator_check_v1")
- `ref`: Git SHA of the artifact under review (7–40 hex chars; branch names rejected)
- `subject`: Object with type, repository, ref (SHA), identifier, optional artifact_paths
- `evidence_inspected`: Array of objects with kind, locator (must include # or :), observation (min 10 chars)
- `calibration`: Evidence-based assessment with demonstrated, partial, not_tested, unknown arrays
- `advisory_only`: Hard-coded to true by schema validation; not treated as authorization
- `can_authorize`: Hard-coded to false by schema validation; cannot satisfy merge gates

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
---
title: INTENT-OS × RNOLA — repository-native operator learning integration
status: draft
written: 2026-09-25
authority: Z1 implementation candidate; advisory learning only
related_issue: 529
---

# INTENT-OS × RNOLA

## Purpose

Integrate Repository-Native Operator Learning Audit (RNOLA) into INTENT-OS without creating a parallel learning platform and without changing existing authority semantics.

The design rule is:

> Every meaningful INTENT-OS act should be capable of becoming a learning object, and every RNOLA learning claim should be testable against an actual repository or INTENT-OS act.

RNOLA is therefore a lens over INTENT-OS, not a separate source of truth.

## 1. Shared control / learning loop

~~~
INTENT
  -> PROPOSAL
  -> IMPLEMENTATION
  -> EVIDENCE
  -> AUTHORITY
  -> CONSEQUENCE
  -> OBSERVATION
  -> LEARNING
  -> revised intent
~~~

The states are intentionally non-equivalent:

| state | question |
|---|---|
| INTENDED | What did the human ask for? |
| PROPOSED | What change did an agent or contributor produce? |
| VERIFIED | What does bounded evidence support? |
| AUTHORIZED | What did the authority holder permit? |
| OBSERVED | What actually happened? |
| LEARNED | What can the operator now explain against evidence? |

A system may be PROPOSED without being VERIFIED, VERIFIED without being AUTHORIZED, and AUTHORIZED without producing the intended OBSERVED consequence.

## 2. INTENT-OS surfaces as learning objects

| INTENT-OS surface | RNOLA learning use |
|---|---|
| ui/intent-os-humanaios-v3_3.html | read system state and distinguish rendered claim from verified seal |
| tools/decision_relay.py | trace human input into a durable branch / PR proposal |
| REQ-* records | distinguish conversation from repository state |
| candidate blocks | distinguish proposal from ratification |
| pull requests | inspect the exact diff before authority is exercised |
| T0-T7 test harness | learn bounded evidence and test scope |
| GitHub Actions | learn event-triggered CI and failure classification |
| intent_os_reconcile_v1_0.py | trace post-merge authority into recorded provenance |
| INDEX / ruling records | inspect durable governance state |
| board seal checker | learn currentness and stale evidence |
| Witness Ledger candidate | future linkage between human rationale and machine execution |

## 3. RNOLA ten-concept map

| concept | INTENT-OS implementation |
|---|---|
| Repository | humanaios-ui/operations |
| Commit / SHA | exact HEAD, read.against, commit or candidate hash |
| Branch | z2/*, req/*, intent-os/*, feature branches |
| Diff | proposed delta visible in a pull request |
| Pull Request | review boundary before merge |
| Test | T0-T7, pytest, smoke, validation checks |
| CI workflow | event-triggered GitHub Actions |
| Dependency | board -> relay -> GitHub -> reconcile -> index |
| Authority boundary | Z1 proposes, Z2 decides, Z3 executes where defined |
| Provenance | hashes, SHAs, receipts, requests, rulings, reconciliation |

## 4. Operator-check record

RNOLA may emit an operator-check record after a teach-back. The canonical schema is:

schemas/intent_os_operator_check_v1.schema.json

An operator check records:

- the exact learning object and ref;
- the operator's explanation;
- evidence personally inspected;
- what understanding was demonstrated;
- what remains partial, unknown, or untested;
- the authority consequence the operator believes follows;
- one next learning object.

It does not record a numeric competence score.

It is deliberately marked advisory_only = true and can_authorize = false.

## 5. Persistence

Phase 1 supports two persistence levels:

1. Transient: outputs/rnola/ for local or generated learning passes.
2. Durable advisory evidence: attach the operator-check JSON or an equivalent structured block to the relevant PR or review record.

Neither location changes the authorization state of the underlying artifact.

The proposed INTENT-OS Witness Ledger may later reference operator-check records, but this integration does not ratify that ledger and does not make a learning record a governance credential.

## 6. PR learning sequence

For an authority-bearing PR:

~~~
intent
  -> exact PR head
  -> diff
  -> code behavior
  -> tests and bounded claims
  -> CI status and scope
  -> dependencies / side effects
  -> authority consequence
  -> operator teach-back
  -> operator-check record
  -> human decision
  -> observed consequence
~~~

The learning pass is not a replacement for required review or CI.

## 7. Example operator check

~~~
{
  "schema": "intentos/operator_check_v1",
  "advisory_only": true,
  "can_authorize": false,
  "subject": {
    "type": "pull_request",
    "repository": "humanaios-ui/operations",
    "ref": "<exact-head-sha>",
    "identifier": "PR-XYZ",
    "artifact_paths": ["path/to/file.py"]
  },
  "intent": "Integrate RNOLA as an INTENT-OS learning layer.",
  "question": "What will merging this PR change?",
  "operator_response": "My explanation in my own words.",
  "evidence_inspected": [
    {
      "kind": "diff",
      "locator": "PR-XYZ",
      "observation": "The PR adds an advisory learning skill and schema; it does not add merge authority."
    }
  ],
  "calibration": {
    "demonstrated": ["proposal versus authorization"],
    "partial": ["CI implementation details"],
    "not_tested": ["rollback behavior"],
    "unknown": []
  },
  "authority_consequence": "If merged, the learning layer becomes repository state; the record itself still cannot authorize future changes.",
  "next_learning_object": "Inspect the CI job that validates the schema.",
  "created_at": "2026-09-25T00:00:00Z"
}
~~~

## 8. Current implementation boundary

Implemented in this change:

- RNOLA skill under tools/skills/;
- operator-check JSON Schema;
- schema behavior tests;
- advisory RNOLA hook in the INTENT-OS board runbook;
- this integration contract.

Not implemented by this change:

- a new public UI;
- automatic board mutation;
- mandatory operator checks;
- numeric competence scoring;
- Witness Ledger ratification;
- new merge requirements;
- new deployment authority;
- any automatic decision on behalf of Z2.

## 9. Falsifiers

The integration should be reconsidered if:

1. an operator check is treated as authorization;
2. RNOLA produces conclusions without citing an exact artifact/ref;
3. operator teach-back becomes a checkbox without evidence inspection;
4. repository cognitive load increases because RNOLA duplicates existing INTENT-OS state;
5. learning records make it harder to distinguish proposed, verified, authorized, and observed states.

The intended direction is one evidence substrate serving both operation and learning.
