# PR Manager Agent

**Standing:** STUB / SPECIFIED — GitHub fetchers not wired; Phase 1 deliverable.  
Do not treat dashboard commands as live until `_fetch_open_prs` / `_fetch_pr_status` return real data.

Governance-aware PR tracking and progression for the HumanAIOS operations repository.

## Quick Start

```bash
# Show all open PRs with status (STUB: empty until Phase 1)
/pr-manager status

# Show only PRs with blockers
/pr-manager blockers

# Get detailed action plan for a specific PR
/pr-manager action-plan 445

# Filter by governance zone
/pr-manager zone Z2

# Batch operations
/pr-manager batch-assign Z2 review
```

## Features (designed; live data Phase 1)

### 1. Dashboard (`status`)

Displays open PRs with zone, status, blockers, next action, SMAG, molt tier.

### 2. Blocker Analysis (`blockers`)

Ranks PRs with active blockers by severity (CRITICAL / MAJOR / MINOR).

### 3. Action Plans (`action-plan <PR#>`)

Current state, blocker analysis, suggested steps, expected outcome.

### 4. Zone Filtering (`zone <Z1|Z2|Z3>`)

Filter and summarize by governance zone.

### 5. Batch Operations (`batch-assign <ZONE> <ACTION>`)

Batch review / merge / fix guidance.

## Molt tier rule

```
effective = max(claimed, observed)
if claimed < observed → undershoot blocker / escalate
```

Claimed tier alone never suppresses observed path classification.

## Blockers

| Severity | Type | Resolution | Time |
|----------|------|-----------|------|
| CRITICAL | CI Red, Merge Conflict, Receipt Gap | Fix code, resolve conflict | 15m–2h |
| MAJOR | Review Pending, Review Comment, Z2 Await | Wait or address | 1h–48h |
| MINOR | CI Flake, Z3 Await Deploy | Investigate or wait | 5m–2h |
| Governance | Molt Undershoot | Correct claim or escalate | 15m–2h |

## Related

- **OI-BRIDGE-01_CONTROL_SURFACE_v0.1.md** — Bridge control surface (SPEC ONLY)
- **SKILL.md** — Command reference (STUB standing)
- **CLAUDE.md** — Authority & Z-role governance
- **REGISTERED.md** — Findings & Z2 signatures
- **tools/molting_protocol_diff_v1_0.py** — Molt tier classification
