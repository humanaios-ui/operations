# PR Manager Agent

**Status:** STUB / SPECIFIED (GitHub fetchers not wired; Phase 1 deliverable)  
**Scope:** Governance-aware PR tracking and progression  
**Authority:** Z1 (proposer) may read PR state and suggest actions; Z2/Z3 execute  
**Standing note:** LANGUAGE_IS_NOT_IMPLEMENTATION — do not treat this skill as Active/Real-time until `_fetch_open_prs` / `_fetch_pr_status` are wired and receipt validation is live.

---

## Overview

The PR Manager Agent helps you:

1. **Monitor PRs** — List open PRs with governance metadata (SMAG prediction, molt tier, zone)
2. **Identify Blockers** — CI failures, merge conflicts, review comments, receipt gaps
3. **Suggest Next Actions** — What needs to be done to move each PR forward
4. **Track Progress** — Predict merge probability, time to merge, action checklist
5. **Batch Operations** — Group PRs by status, zone, or blocker type for efficient dispatch

**Current limitation:** Dashboard commands return empty until GitHub MCP integration is completed in Phase 1.

---

## Commands

### `/pr-manager status`

Print a dashboard of all open PRs (STUB: returns empty list until wired).

### `/pr-manager blockers`

Show only PRs with active blockers, ranked by severity.

### `/pr-manager action-plan <PR#>`

Detailed next-steps plan for a specific PR.

### `/pr-manager zone <ZONE>`

Filter PRs by governance zone (Z1 / Z2 / Z3).

### `/pr-manager batch-assign <ZONE> <ACTION>`

Generate instructions for batch operations (review | merge | fix).

---

## Architecture

### Data Sources

- **GitHub API** (via mcp__github__*) — Phase 1 wiring required
- **REGISTERED.md** (live-fetch) — Phase 1 wiring required
- **PR diff** (file-based) — molt tier observation from paths
- **.github/workflows/** — CI gate state when available

### Molt tier rule (corrected)

```
observed = classify(changed_paths)
claimed = parse(PR body) or None
effective = max(claimed, observed) if claimed is not None else observed
if claimed is not None and claimed < observed:
    → undershoot blocker / escalate (do not accept claim as sole tier)
```

### Blockers Taxonomy

| Blocker | Type | Resolution | Time Est. |
|---------|------|-----------|-----------|
| CI Red | Actionable | Fix code, push, re-run | 15m–2h |
| CI Flake | Investigation | Confirm flake, re-run, comment | 5m–30m |
| Merge Conflict | Actionable | Merge base, resolve, push | 10m–1h |
| Review Pending | Waiting | Wait for reviewer decision | 1h–48h |
| Review Comment | Actionable | Address, reply, re-request | 15m–2h |
| Receipt Gap | Governance | File IC, await Z2 decision | 24h–48h |
| Z2 Await Hash | Waiting | Z2 ratifies via authenticated event | 1h–48h |
| Z3 Await Deploy | Waiting | Z3 executes merge, deploy | 5m–2h |
| Molt Undershoot | Governance | Correct claim or justify; escalate | 15m–2h |

---

## Integration with Governance

### Z1 (Proposer) Workflow

1. Create PR with governance metadata (smag_p, molt_tier_claimed, zone)
2. Monitor blockers; fix CI/conflicts; address review comments
3. Handoff to Z2 once ready (CI green, no conflicts, comments resolved)

### Z2 (Ratifier) Workflow

1. Review for governance compliance (SMAG sanity, molt effective tier, receipt gaps)
2. Ratify via authenticated external event or cryptographic signature — not a bare hash string claim
3. Monitor Z3 execution once merged

### Z3 (Executor) Workflow

1. Merge only with independently resolved authority + CI green
2. Emit VERDICT event
3. Deploy per zone role

---

## Configuration

### .claude/settings.json

```json
{
  "pr-manager": {
    "enabled": true,
    "standing": "STUB",
    "watch_zones": ["Z1", "Z2"],
    "blockers_threshold": "MAJOR",
    "auto_dashboard": false,
    "receipt_reconciliation": false,
    "smag_confidence_floor": 0.50
  }
}
```

### Environment Variables

- `GITHUB_OWNER=humanaios-ui`
- `GITHUB_REPO=operations`
- `Z2_CANONICAL_EMAIL=carly.r.anderson@gmail.com`
- `Z2_BUSINESS_EMAIL=aioshuman@gmail.com`

---

## Related

- **OI-BRIDGE-01_CONTROL_SURFACE_v0.1.md** — Bridge control surface (SPEC ONLY)
- **CLAUDE.md** — Governance authority & Z-role definitions
- **REGISTERED.md** — Live registry of F/IC/H/MOLT candidates & Z2 signatures
- **PRIORITY_QUEUE.md** — Impact scoring and Z2 ranked decisions
- **.github/workflows/z2_ratification_gate.yml** — CI enforcement
- **tools/molting_protocol_diff_v1_0.py** — Molt tier classification
