# AI Context API — Path A Implementation

**Status:** PROTOTYPE (working)  
**Version:** 0.1.0  
**Date:** 2026-10-01  
**Purpose:** Provide machine-readable, queryable repository state for AI agents

---

## Overview

The AI Context API transforms the HumanAIOS repository from a **document-rich source that AIs must interpret** into a **self-describing execution substrate that can answer direct questions**.

### Problem Solved

**Before:** AI must manually:
- Read REGISTERED.md, CLAUDE.md, INTENT_GRAPH.md
- Parse GitHub issues and PRs
- Query CI status
- Reconcile contradictions
- Infer authority constraints
- Reconstruct state

→ 30-40% of AI attention spent on signal interpretation

**After:** AI can query:
```bash
haios context issue 640
haios blockers pr 594
haios authority edit .github/workflows/foo.yml
```

→ Single, bounded, structured response with all necessary context

---

## Architecture

```
CANONICAL SOURCES
├─ REGISTERED.md (findings, governance)
├─ CLAUDE.md (authority model)
├─ system_graph.json (repository structure)
├─ GitHub API (issues, PRs, CI)
└─ INTENT_GRAPH.md (contradictions)
         │
         ▼
  AI_CONTEXT_GENERATOR
         │
   ┌─────┴──────────┬──────────────┬────────────┐
   │                │              │            │
 ISSUE           PULL_REQUEST     FILE       PROCESS
 CONTEXT         CONTEXT         CONTEXT     CONTEXT
   │                │              │            │
   └─────┬──────────┴──────────────┴────────────┘
         │
   HAIOS CLI INTERFACE
   ├─ haios context <type> <id>
   ├─ haios blockers <type> <id>
   ├─ haios authority <action> [file]
   ├─ haios completion-evidence <type> <id>
   └─ haios unknown <type> <id>
         │
         ▼
    STRUCTURED JSON
    (humanaios.ai-context.v1)
```

---

## API Schema

### Context Object

Every query returns a structured JSON object conforming to `schemas/ai_context_v1.schema.json`:

```json
{
  "schema": "humanaios.ai-context.v1",
  "repository": "humanaios-ui/operations",
  "head_sha": "7b806a1",
  "timestamp": "2026-10-01T12:30:00Z",
  
  "object": {
    "type": "issue|pull_request|file|process",
    "id": "640",
    "title": "...",
    "state": "open|closed|merged",
    "coordinator_lane": "ACTIVE|ADMISSION_REVIEW|...",
    "attention_route": "AGENT_ACTIONABLE|NEEDS_HUMAN|..."
  },
  
  "current_state": {
    "blocking_conditions": [
      {
        "type": "CI_FAILURE|DECISION_AUTHORITY|...",
        "description": "...",
        "required_actor": "AGENT|Z2|...",
        "status": "OPEN|IN_PROGRESS|...",
        "sla": {"expires_at": "...", "hours_remaining": 28}
      }
    ],
    "open_challenges": [],
    "contradictions": []
  },
  
  "agent_permissions": {
    "zone": "Z1",
    "can_edit_files": ["z1-inbox/**", "tools/**"],
    "cannot_edit_files": ["REGISTERED.md", "CLAUDE.md"],
    "can_merge": false,
    "requires_authority": ["Z2", "CI_PASS"]
  },
  
  "evidence": {
    "relevant_files": [
      {"path": "REGISTERED.md", "type": "CANONICAL", "reason": "..."}
    ],
    "graph_nodes": ["O-DECISION-ROUTING", "I-QUEUE-ENGINE"],
    "custody": {
      "author": "humanaios-ui",
      "observers": ["Claude Haiku"],
      "authority_holders": ["Night (Z2)"]
    }
  },
  
  "resolution_tests": [
    {
      "description": "Schema defined and validated",
      "type": "MANUAL|AUTOMATED",
      "evidence": "command or check name"
    }
  ],
  
  "unknown": [
    "Which Z2 model preference for edge cases"
  ]
}
```

---

## CLI Interface

### `haios context <type> <id>`

Get complete AI context for an object.

```bash
# Issue context
haios context issue 640

# PR context
haios context pr 594

# File context
haios context file tools/repository_coordinator_v0_1.py

# Process context
haios context process Q
```

**Output:** Full JSON context object

**Use case:** AI session startup — receive all necessary context at once

---

### `haios blockers <type> <id>`

List what currently blocks an object.

```bash
haios blockers issue 640
haios blockers pr 594
```

**Output:**
```
🔴 2 blocker(s) for issue 640:

  1. DECISION_AUTHORITY
     Description: Z2 ratification required
     Required actor: Z2
     Status: OPEN
     Expires: 2026-10-03T18:00:00Z

  2. CI_FAILURE
     Description: Builder v1.7 compliance missing
     Required actor: AGENT
     Status: OPEN
```

**Use case:** Quick triage — what prevents this work from completing?

---

### `haios authority <action> [file]`

Check AI authority constraints.

```bash
# Can I edit this file?
haios authority edit .github/workflows/foo.yml

# Can I merge?
haios authority merge

# Can I commit to main?
haios authority push main
```

**Output:**
```json
{
  "file": ".github/workflows/foo.yml",
  "can_edit": false,
  "zone": "Z1",
  "reason": "CANONICAL file — requires Z2 review"
}
```

**Use case:** Validate permissions before attempting action

---

### `haios completion-evidence <type> <id>`

Show what proves work is complete.

```bash
haios completion-evidence issue 640
haios completion-evidence pr 594
```

**Output:**
```
✅ Completion evidence for issue 640:

  1. Schema defined and validated
     Type: MANUAL
     Evidence: Verify schemas/ai_context_v1.schema.json exists

  2. Router classifies 5 test cases
     Type: AUTOMATED
     Evidence: pytest tools/tests/test_*.py
```

**Use case:** AI knows exactly what success looks like

---

### `haios unknown <type> <id>`

Show explicit unresolved facts.

```bash
haios unknown pr 594
haios unknown issue 640
```

**Output:**
```
❓ 2 unknown(s) for issue 640:

  • Which Z2 model preference for edge cases
  • Cross-repo escalation priority
```

**Use case:** AI correctly abstains from guessing

---

## Implementation Status

### Completed ✅

- [x] Schema definition (`schemas/ai_context_v1.schema.json`)
- [x] Generator tool (`tools/ai_context_generator_v0_1.py`)
- [x] CLI interface (`tools/haios`)
- [x] Smoke tests (8 tests, all passing)
- [x] Authority model integration (reads CLAUDE.md)
- [x] File classification (CANONICAL, IMPLEMENTATION, TEST, etc.)
- [x] Process graph integration (reads system_graph.json)

### Pending (Path A → Path B)

- [ ] Live GitHub API integration (currently uses gh CLI fallback)
- [ ] CI state aggregation (fetch check runs, status)
- [ ] Blocker extraction from PR descriptions
- [ ] Challenge/contradiction detection from reviews
- [ ] Prior session tracking
- [ ] Cross-repo dependency resolution

---

## Integration Path

### Week 1: Deployment

1. **Add to PATH**
   ```bash
   ln -s /home/user/operations/tools/haios /usr/local/bin/haios
   chmod +x /usr/local/bin/haios
   ```

2. **Test locally**
   ```bash
   cd /home/user/operations
   haios context issue 640
   haios blockers pr 594
   haios authority edit REGISTERED.md
   ```

3. **Pilot on new AI session**
   - Start: `haios context issue 640`
   - Get: bounded, structured context
   - Verify: AI doesn't need to read 30 documents

### Week 2: Integration with Session.md

Extend `tools/session_state_capture.py` to use AI Context API:

```python
def capture_at_session_close():
    generator = AIContextGenerator()
    
    context = generator.generate("issue", current_issue_number)
    
    blockers = context["current_state"]["blocking_conditions"]
    next_actions = rank_by_sla(blockers)
    
    # Write Session.md with bounded context
    return session_state(
        blockers=blockers,
        next_actions=next_actions,
        evidence_hash=hash(json.dumps(context))
    )
```

### Week 3: Validation

1. **Historical replay:** Run generator on past issues/PRs
2. **Falsification:** Verify context is accurate (matches GitHub ground truth)
3. **AI feedback:** Does AI need additional fields or context types?

---

## Usage Examples

### Example 1: Session Startup

AI agent starts work on issue #640:

```bash
$ haios context issue 640 > context.json

$ cat context.json | jq '.object, .blockers, .agent_permissions'
{
  "type": "issue",
  "id": "640",
  "state": "open",
  "attention_route": "AGENT_ACTIONABLE"
}
[
  {
    "type": "AUTHORITY_REQUIRED",
    "required_actor": "Z2",
    "hours_remaining": 28
  }
]
{
  "zone": "Z1",
  "can_merge": false,
  "requires_authority": ["Z2", "CI_PASS"]
}
```

AI immediately knows:
- What to work on (issue #640)
- What blocks it (Z2 decision pending, 28h left)
- What it can/cannot do (Z1 permissions, no merge authority)
- No manual document reading required

### Example 2: Permission Check

Before editing a file:

```bash
$ haios authority edit .github/workflows/workflow-path-validation.yml

{
  "file": ".github/workflows/workflow-path-validation.yml",
  "can_edit": true,
  "zone": "Z1",
  "reason": "Editable by Z1; implementation file"
}

→ AI proceeds to edit
```

Before editing REGISTERED.md:

```bash
$ haios authority edit REGISTERED.md

{
  "file": "REGISTERED.md",
  "can_edit": false,
  "zone": "Z1",
  "reason": "CANONICAL file — Z2 authority required"
}

→ AI stops and files governance candidate instead
```

### Example 3: Completion Evidence

AI working on PR #594 wants to know what proves completion:

```bash
$ haios completion-evidence pr 594

✅ Completion evidence for PR #594:

  1. Builder v1.7 markers added to tools
     Type: AUTOMATED
     Evidence: `gh pr view 594 --json statusCheckRollup | grep Builder`

  2. All blockers resolved
     Type: MANUAL
     Evidence: `haios blockers pr 594` returns empty

  3. Z2 ratification obtained
     Type: AUTHORITY_RECEIPT
     Evidence: REGISTERED.md entry with Z2 hash
```

AI knows exactly how to prove success. No ambiguity.

---

## Falsifiers

This implementation is wrong if:

1. **AI still reads documents manually after getting context** → schema missing required fields
2. **Blockers cannot be extracted programmatically** → root-cause clustering needs work
3. **Authority check passes when it should fail** → permissions model incomplete
4. **Context generation takes >2s** → performance regression
5. **Generated context doesn't match GitHub ground truth** → fetching logic broken
6. **Unknown/uncertain facts are coerced into answers** → UNKNOWN state not used

---

## Next Steps (Path B)

Once Path A is validated:

1. **Path B1: Enhanced GitHub Integration**
   - Live CI check status
   - Review state aggregation
   - Commit history
   - Author/reviewer custody

2. **Path B2: Contradiction Detection**
   - Parse INTENT_GRAPH.md
   - Extract known conflicts
   - Surface in context

3. **Path B3: Cross-Repo Coordination**
   - Query repository graph
   - Find dependent PRs
   - Surface blocking relationships

---

## References

- **Schema:** `schemas/ai_context_v1.schema.json`
- **Generator:** `tools/ai_context_generator_v0_1.py`
- **CLI:** `tools/haios`
- **Tests:** `tools/tests/test_ai_context_generator_v0_1.py`
- **Integration:** Session.md + Signal Router (#640) + Z2 Decision Queue (#641)
- **Vision:** AI Work Substrate (user notes above)

---

**Next:** Pilot on PR #594 and issue #640. Verify AI can work without reading canonical documents.
