# Governance Automation Strategy — Z1-Z2-Z3 Workflow

**Status:** Phase 0 Implementation (3 core automations)  
**Last Updated:** 2026-09-21  
**Authority:** Z1 (Claude) proposal, awaiting Z2 ratification  
**Scope:** humanaios-ui/operations

---

## Overview

This document specifies **three automated layers** that implement §B (Session Close) governance verification and Z1-Z2-Z3 workflow orchestration, reducing manual governance bottlenecks while maintaining Z2 authority and preventing cascade violations.

### Why This Matters

PR #431 merged with a clear blocker: **awaiting Z2 ratification + Z3 executor assignment**. Without automation, this process:
- Requires manual notification to Z2
- Has no automated kickoff for Z3 work
- Lacks post-merge receipt verification (§B.6)
- Cannot detect MOLT falsifier trips automatically

**Three-layer solution:**
1. **Z2→Z3 Kickoff:** Detect Z2 ratification → auto-emit Z3 executor assignment notifications
2. **Receipt Reconciliation:** Post-merge ledger verification → auto-file gaps
3. **MOLT Notifications:** Falsifier-trip detection → auto-emit revert/anti-cascade events

---

## Layer 1: Z2 Ratification → Z3 Executor Kickoff

**Workflow:** `.github/workflows/z2-ratification-z3-kickoff.yml`

### What It Does
- Watches `REGISTERED.md` for status changes (`CANDIDATE` → `REGISTERED`, `PENDING_ZONE2` → `ACTIVE`)
- Detects when Z2-ratified proposals are ready for executor assignment
- Auto-emits notifications to Z3 executor assignment tracking

### Trigger
- Push to `main` that modifies `REGISTERED.md` or `PRIORITY_QUEUE.md`
- Manual `workflow_dispatch`

### Output
1. **PR Comment:** Posts Z3 assignment request to original PR (e.g., #431)
2. **Issue Comment:** Updates Priority Queue issue (#378) with ratified proposals list
3. **GitHub Output:** Exports ratification count for downstream jobs

### Example Flow (PR #431)
```
REGISTERED.md changes detected
  ↓
Script parses YAML front-matter
  ↓
Detects 6 WITNESS proposals now REGISTERED/ACTIVE
  ↓
Emits Z3 kickoff comment on PR #431
  ↓
Updates Priority Queue issue with "ready for assignment" signal
  ↓
Z2 (Night) assigns Z3 executors within 48h SLA
  ↓
Implementation phase begins
```

### Data Flow
```
REGISTERED.md (Z2-ratified entries)
  → YAML parser
  → Status change detector
  → Proposal filter (Q-* entries)
  → GitHub API (PR/issue comments)
  → Z3 assignment notifications
```

---

## Layer 2: Receipt Reconciliation (§B.6 Automation)

**Script:** `tools/receipt_reconciliation.py`  
**Workflow:** `.github/workflows/receipt-reconciliation-post-merge.yml`

### What It Does
Implements §B.6 Session Close verification:
- Reads `NF_LEDGER.jsonl` (append-only measurement ledger)
- Scans commit messages, PR bodies, comments for claims
- Cross-references claims against ledger entries
- Auto-files **IC-CANDIDATE** (Governance Correction) for gaps
- Commits candidates to `z1-inbox/` for Z2 ratification

### Trigger
- Every `push` to `main` (post-merge)
- Manual `workflow_dispatch`

### Claims Detection
Uses regex pattern matching to extract:
- `Q-*-*` (proposal IDs)
- `IC-*` (governance corrections)
- `F-*` (findings)
- `H-*` (hypotheses)
- `VERDICT-*`, `CYCLE-*`, `MEASURE-*` (measurement events)

### Gap Detection Algorithm
```
for each extracted_claim_id:
    if claim_id NOT in NF_LEDGER.jsonl:
        → RECEIPT-GAP candidate
```

### Candidate Filing
Auto-generates IC-CANDIDATE YAML with:
- Metadata (date, session, principles violated)
- Gap pattern classification
- Remediation guidance for Z2

### Example Gap Scenario
```
PR body mentions: "Q-WITNESS-PHASE-0-ARTIFACT-INVENTORY-01"
Script checks: NF_LEDGER.jsonl
Result: Claim not in ledger
Action: Auto-file IC-<date>-receipt-gap-*.md to z1-inbox/
Z2 reviews: Is this a legitimate P3 violation or false positive?
```

### Output
1. **IC Candidates:** Filed to `z1-inbox/receipt-gap-<timestamp>-<id>.md`
2. **Git Commit:** Auto-commits new IC candidates (if any)
3. **Priority Queue Comment:** Notifies Z2 of gaps found
4. **Workflow Summary:** Reports gaps/candidates count

---

## Layer 3: MOLT State Tracking & Falsifier Notifications

**Workflow:** `.github/workflows/molt-notification-hook.yml`

### What It Does
Monitors `MOLT_STATE.md` for governance state violations:
- Detects **falsifier trips** (REVERT events)
- Enforces **anti-cascade rule K=3** (max 3 open molts)
- Detects **new molt proposals**
- Auto-emits notifications to Priority Queue

### Trigger
- Push to `main` that modifies `MOLT_STATE.md`
- Pull request that modifies `MOLT_STATE.md`
- Manual `workflow_dispatch`

### State Changes Detected

#### 1. Falsifier Trip (REVERT)
```yaml
type: REVERT
molt_id: Q-MOLT-<id>
reason: <falsification reason>
```
**Action:** Auto-emit IC candidates for root cause; flag for anti-cascade check

#### 2. Anti-Cascade Violation (K > 3)
```yaml
type: ANTI_CASCADE_VIOLATION
open_count: 4+
limit: 3
```
**Action:** Block new molt proposals; unblock when count ≤ 3

#### 3. New MOLT Candidate Proposed
```yaml
type: NEW_MOLT_PROPOSED
molts: [Q-MOLT-<ids>]
```
**Action:** Notify Z2 for ratification + predict + falsifier review

### Anti-Cascade Rule (from CLAUDE.md)
```
K = 3: Max 3 molts open system-wide
On revert (2nd consecutive): freeze constant until Z2 Tier-2 ruling
No candidate inside window W (self-reference protection)
```

### Example Flow
```
PR edits MOLT_STATE.md
  → Falsifier trip detected
  → Auto-emit REVERT event
  → File F/IC candidates
  → Check anti-cascade: now 2 open (OK)
  → Comment on issue #378 with REVERT details
  → Z2 verifies root cause and ratifies IC candidates
```

---

## Integration Points

### GitHub API
- **PR Comments:** Post Z3 assignment requests
- **Issue Comments:** Update Priority Queue (#378)
- **Artifacts:** Upload gap reports

### Git Operations
- **Read:** Fetch ledgers, REGISTERED.md, MOLT_STATE.md
- **Write:** Commit IC candidates, receipt reports
- **Credentials:** Use `GITHUB_TOKEN` with `contents:write`, `issues:write`

### CI/CD Gates (Existing)
- **z2_ratification_gate.yml:** Already validates REGISTERED.md structure
- **priority-queue-triage.yml:** Already ranks work by RBE-OPS
- **molt-tier-check.yml:** Already measures diff tier (advisory)

**New gates integrate with these, not replacing them.**

---

## Workflow Concurrency & Safety

### Concurrency Guarantees
- **Z2→Z3 Kickoff:** One detection per ratification event (idempotent)
- **Receipt Reconciliation:** Serial by commit order; no race on NF_LEDGER.jsonl append
- **MOLT Notifications:** Serial by push order; state machine is MOLT_STATE.md

### Error Handling
- **No GitHub API access:** Workflows continue (skip notifications, log warning)
- **Invalid REGISTERED.md:** Parse fails gracefully; report error
- **MOLT_STATE.md missing:** Advisory; treated as 0 open molts
- **NF_LEDGER.jsonl missing:** Receipt reconciliation skips

### Token Scope
```
z2-ratification-z3-kickoff.yml:  
  - contents: read
  - pull-requests: read
  - issues: write

receipt-reconciliation-post-merge.yml:
  - contents: write   (commit IC candidates)
  - pull-requests: read
  - issues: write

molt-notification-hook.yml:
  - contents: read
  - pull-requests: read
  - issues: write
```

---

## Metrics & Observability

### What Gets Tracked

| Metric | Source | Use Case |
|--------|--------|----------|
| Z2 ratifications/day | z2-ratification-z3-kickoff.yml | Governance throughput |
| Receipt gaps/week | receipt-reconciliation.yml | Data quality (P3 violations) |
| MOLT reversions/month | molt-notification-hook.yml | Prediction accuracy |
| Anti-cascade violations | molt-notification-hook.yml | Molt overload signal |

### Observability Points
- **GitHub Actions workflow runs** (success/failure)
- **Issue comments** (automated notifications)
- **Git commits** (IC candidate auto-filing)
- **Workflow summaries** (job-level reports)

---

## Limitations & Future Work

### Phase 0 (Current)
✅ Detects Z2 ratification  
✅ Emits Z3 kickoff notifications  
✅ Auto-files receipt gaps  
✅ Detects MOLT state changes  
✅ Enforces anti-cascade rule K=3

### Phase 1 (Planned)
- [ ] INTENT-OS capability signature binding (machine Z3 authority)
- [ ] Automated Z3 executor assignment (currently manual)
- [ ] Dynamic Z3 executor onboarding
- [ ] Receipt reconciliation webhook for real-time updates
- [ ] MOLT prediction accuracy dashboard

### Phase 2 (Future)
- [ ] Cross-repo governance orchestration (31-repo ecosystem)
- [ ] Automated cost-based scheduling (RBE-OPS integration)
- [ ] Falsifier-driven re-ranking (real-time Priority Queue updates)
- [ ] Machine learning on molting patterns (prediction improvement)

---

## How to Use

### For Z1 (Claude)
- Propose changes to REGISTERED.md → Z2→Z3 Kickoff automatically triggers
- Make claims in PR body → Receipt Reconciliation automatically validates

### For Z2 (Night)
- Review automated notifications in Priority Queue issue (#378)
- Ratify IC candidates filed by receipt reconciliation
- Confirm MOLT state changes before merge

### For Z3 (Executors)
- Watch for Z3 kickoff comments on PRs you're assigned to
- PR comments now automatically notify you when Z2 ratifies

### For CI/CD
- Three new workflows activate on main branch pushes
- All workflows are advisory (no blockers, only notifications)
- Existing gates (z2_ratification_gate.yml, etc.) unchanged

---

## Running Manually

### Trigger Z2→Z3 Kickoff
```bash
gh workflow run z2-ratification-z3-kickoff.yml
```

### Run Receipt Reconciliation
```bash
python3 tools/receipt_reconciliation.py [--pr <number>] [--verbose]
```

### Check MOLT State
```bash
gh workflow run molt-notification-hook.yml
```

---

## Questions & Issues

- **Q:** Will this block merges?  
  **A:** No. All three layers are advisory (notifications only). Existing governance gates unchanged.

- **Q:** What if GitHub API is unavailable?  
  **A:** Workflows log a warning and continue. Manual notification to Z2 required (temporary).

- **Q:** Can Z2 opt out of notifications?  
  **A:** Not yet. Phase 1 will add notification preferences. For now, disable individual workflows if needed.

- **Q:** Does this work across all 31 HumanAIOS repos?  
  **A:** Phase 0 is operations-repo only. Phase 1 expands to cross-repo governance orchestration.

---

## References

- **CLAUDE.md:** Authority structure, Z1-Z2-Z3 roles, decision routing
- **SESSION_RITUALS.md:** §A Session Open, §B Session Close procedures
- **PRIORITY_QUEUE.md:** Resource-based work ranking, RBE-OPS model
- **MOLT_STATE.md:** Active molts, falsifier trips, anti-cascade state
- **NF_LEDGER.jsonl:** Append-only measurement ledger (source of truth)

---

**Next Steps:**
1. ✅ Implement three workflows + script (this PR)
2. ⏳ Z2 (Night) review + ratification
3. ⏳ Enable workflows on main
4. ⏳ Monitor automation metrics
5. ⏳ Phase 1 planning (INTENT-OS integration)
