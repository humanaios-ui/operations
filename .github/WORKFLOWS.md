# GitHub Actions Workflow Audit & Classification

**Last Updated:** 2026-09-21  
**Total Workflows:** 52 — `ls .github/workflows/*.yml .github/workflows/*.yaml 2>/dev/null | wc -l`  

> This count is hand-maintained and was 48 while 52 files were present. It is a
> derived view of a directory listing and belongs under a renderer like the other
> registries in this repository; see `Q-GOVDRIFT-01` ask 1. Until then, re-run the
> command above when adding or removing a workflow.
> 
> **Five of the 52 do not parse** as GitHub reads them, so they produce zero-job
> runs that read as failing gates but never execute a step: `drift-monitor.yml`,
> `receipt-reconciliation-post-merge.yml`, `sonarcloud-baseline-auto.yml`,
> `weekly-funding-rescore.yml`, `weekly-profile-sync.yml`. `workflow-lint.yml`
> reports them advisory; repairing them is its stated precondition for becoming
> blocking.

**Consolidation Phase:** Phase 1 Complete (findings-registry + sonarqube unified; 2 redundant workflows removed)

## Executive Summary

| Category | Count | Status |
|----------|-------|--------|
| Critical-Path Gates | 9 | Lean, required |
| Scheduled Audits | 23 | Intentional separation by scope/schedule |
| Specialized Frameworks | 5 | SMAG calibration (Stage 2), research, industry telemetry |
| Infrastructure/Maintenance | 12 | Ancillary support workflows |

### Quick Consolidation Facts
- **Completed:** 2 redundant workflows merged (findings-registry-gate → findings-registry; sonarqube → sonarcloud-baseline-auto)
- **Remaining:** 44 → 42 active workflows
- **Further Consolidation:** Candidates identified but architectural separation required (multi-stage pipelines, different audit scopes)

---

## Critical-Path Gates (Blocking PRs)

These 9 workflows must pass before a PR can merge to main:

| Workflow | Purpose | Trigger | Category |
|----------|---------|---------|----------|
| `findings-registry.yml` | Validate REGISTERED.md integrity (hard failures block; soft warnings tolerated per Z2 guidance) | PR to main | Governance |
| `molt-tier-check.yml` | Classify molt tier (Tier 0/1/2) and validate anti-cascade rules | PR changes | Governance |
| `quality-baseline.yml` | Run pytest baseline (29 test suites: intent_os, industry_telemetry, etc.) | PR to main | Testing |
| `security-gates.yml` | Run security checks (semgrep, component scanning, secret scanning) | PR to main | Security |
| `z2_ratification_gate.yml` | Verify Z2 ratification requirements on candidate blocks: z1-inbox integrity, rendered-index sync, recorded signatures, Seed Constitution Z2 hashes | PR to `z1-inbox/**`, `REGISTERED.md`, `seeds/`, `seed-publication/**` | Governance |
| `governance-files.yml` | Hold `GOVERNANCE_FILES.md` to `.gov-control/governance-files.yaml`: every declared path resolves in-tree, no hand-set status, rendered view in sync | every PR and push to main (no path filter — the gate reads the whole tree) | Governance |
| `temporal-dissolution-gate.yml` | Policy enforcement: reject unauthorized internal deadline semantics (audit-critical, S-070726) | PR to main | Policy |
| `builder-lint.yml` | Lint builders and infrastructure-as-code | PR to main | Linting |
| `workflow-lint.yml` | Lint GitHub Actions workflows themselves | PR to main | Linting |

**Why this stays small:** These gates cover the critical path (code quality, security, governance, policy). Additional audits run on schedule or event-trigger but do not block merges—by design, to prevent audit overhead from becoming a merge blocker.

---

## Scheduled Audits & Monitoring (21 workflows)

Intentionally separated by schedule and scope to enable fault isolation and independent alerting.

### Morning Window (Grounding Pre-Flight: 00:00–09:00 UTC)

| Time | Workflow | Purpose | Frequency |
|------|----------|---------|-----------|
| 00:00 | `divergence-detect.yml` | Consistency checks (daily) | Daily |
| 02:00 | `haios-corpus-integrity.yml` | Corpus/registry validation | Daily |
| 02:00 (Mon) | `drift-monitor.yml` | Document divergence, link rot, unregistered files | Biweekly |
| 03:00 (Mon) | `intake-pipeline.yml` | Inbox classification → dedup → reconcile → register | Weekly |
| 06:00 | `haios-system-audit.yml` | System pre-flight: verify operator mental model matches live state | Daily |
| 06:00 (Mon) | `research-agent.yml` | Autonomous research task execution (arxiv_scan, metaculus_check) | Weekly |
| 06:17 (Mon) | `smag-consolidate.yml` | SMAG ledger consolidation: drain issue comments → durable ledger → gap report PR | Weekly |
| 07:00 (Mon) | `governance-triage.yml` | Governance triage automation | Weekly |
| 08:00 | `acat-pipeline-trigger.yml` | ACAT agent assessment (sequential/single/perturbation modes) | Daily |
| 08:00 | `daily-deadline-alerts.yml` | Deadline notifications | Daily |
| 09:00 | `agent-api-monitor.yml` | API health monitoring | Daily |
| 09:00 | `haios-standing-audit.yml` | Standing audit (A1: stale dimension count, etc.) | Daily |

### Event-Driven & Continuous

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `smag-capture.yml` | PR close | Mechanical SMAG capture: post predicted/measured row to issue #103 |
| `mesh-sync-batch.yml` | Merge to governance files (GOVERNANCE_RATIFICATIONS_REGISTRY.yaml, AUTHORITY_ASSIGNMENTS.yaml, CONTROLLED_DOCUMENTS.md) | Dispatch governance changes to mesh repos |
| `intent-os-reconcile.yml` | Schedule (weekly) + dispatch | INTENT-OS state reconciliation |
| `scorecard.yml` | Event-driven | GitHub dependency scorecard |
| `haios-harmonizer-pulse.yml` | Every 8 hours (00:00, 08:00, 16:00 UTC) | System pulse monitoring (3x/day) |
| `industry-telemetry.yml` | Schedule (Monday 09:30 UTC) + manual | Industry telemetry capture and lead detection |

---

## Specialized Frameworks

### SMAG Calibration Loop (Stage 2)

Three intentionally separate workflows form a real-time prediction loop:

| Workflow | Trigger | Role |
|----------|---------|------|
| `ci-predict-pin.yml` | PR create | Pin prediction (smag_p) at proposal time |
| `ci-predict-resolve.yml` | PR merge | Resolve prediction: record measured outcome (CI pass/fail, checks) |
| `ci-predict-consolidate.yml` | Hourly (0 * * * *) | Consolidate ledger: compute gap report, feedback signal for next cycle |

**Why separate:** Real-time pin and resolve operate at PR boundary; consolidation must aggregate across all PRs hourly. Merging would create coupling between PR-boundary logic and batch aggregation.

### Research & Analysis

| Workflow | Purpose | Status |
|----------|---------|--------|
| `research-agent.yml` | Autonomous research (arxiv_scan, metaculus_check) | Scheduled weekly |
| `research-validation.yml` | Validate research framework (bio_framework_core_v1_2.py, etc.) | On bio framework changes |

**Zone Status:** Research zone is read-only per CLAUDE.md; workflows run as scheduled but do not gate merges.

---

## Infrastructure & Maintenance (12 workflows)

| Workflow | Purpose | Trigger |
|----------|---------|---------|
| `auto-request-copilot-review.yml` | Request GitHub Copilot review on new PRs | PR create |
| `copilot-base-guard.yml` | Base branch protection with Copilot checks | PR to main |
| `behavioral-compliance.yml` | Agent behavior compliance checking | Scheduled |
| `agent-principle-compliance-check.yml` | Principle compliance validation | PR changes |
| `tool-manifest.yml` | Validate tools-manifest.yaml and TOOLS_MANIFEST.md sync | tool-manifest changes |
| `document-control.yml` | Document control gate: validate frontmatter, registry sync | Document changes |
| `no-op-pr-guard.yml` | Reject no-op PRs (safety gate, prevents empty merges) | PR to main |
| `pages.yml` | GitHub Pages deployment (docs site) | Push to main |
| `priority-queue-triage.yml` | Priority queue triage automation | Scheduled |
| `haios-harmonizer-pulse.yml` | System pulse monitoring | Every 8 hours |
| `intent-os-refresh.yml` | INTENT-OS state refresh | Scheduled + dispatch |
| `industry-telemetry.yml` | Industry telemetry capture (Q4 2026 forecasts) | Mon 09:30 UTC |

---

## Consolidation History

### Phase 1: Redundancy Elimination (PR #422)

**Completed:**
- ✅ `findings-registry-gate.yml` → Merged into `findings-registry.yml`
  - Consolidated artifact capture logic from separate gate workflow
  - Non-strict validation (tolerates REG_UNCOMMITTED_CANDIDATE warnings; blocks hard failures)
  - Audit S-070726: governance records retention via artifact upload
  
- ✅ `sonarqube.yml` (dormant) → Consolidated into `sonarcloud-baseline-auto.yml`
  - Added PR trigger support (pull_request: [opened, synchronize, reopened])
  - Unified workflow now handles both PR advisory scans and main baseline capture
  - Metrics fetch, BLOCKER issue creation, baseline updates all in one workflow

**Result:** Reduced active workflows from 44 to 42.

### Intentional Non-Consolidations

**Why these remain separate:**

1. **ci-predict-*.yml (3 workflows)**
   - Real-time pins and resolves operate at PR boundary; consolidation would couple boundary logic with batch aggregation
   - Hourly consolidation is independent timing requirement
   - Stage 2 calibration framework requires architectural separation

2. **smag-capture.yml + smag-consolidate.yml (2 workflows)**
   - Real-time capture (on PR close) + weekly consolidation form a closed-loop learning pipeline
   - Separation enables independent retries and failure isolation
   - By design: mechanical capture → human review window → scheduled consolidation

3. **temporal-dissolution-gate.yml**
   - Critical audit gate for deadline policy enforcement (S-070726)
   - Must run on every PR to main; cannot be merged with other gates
   - Policy isolation: separate status report for policy violations

4. **Scheduled audits (21 workflows)**
   - Different schedules (daily, weekly, biweekly, hourly) prevent bundling without losing precision
   - Different scopes (governance, infrastructure, research, monitoring) prevent coupling
   - Fault isolation: a failure in one audit scope does not halt others

---

## Monitoring & Future Optimizations

### Phase 2 Candidates (Not Recommended Now)

1. **Alert infrastructure sharing** (future consideration)
   - `daily-deadline-alerts.yml` + `priority-queue-triage.yml` could potentially share a consolidated alert delivery system
   - Status: Monitor for growth; only consolidate if both workflows grow significantly

2. **Mesh workflow framework** (future consideration)
   - `mesh-standard-files.yml` + `mesh-sync-batch.yml` might benefit from a shared mesh orchestration layer
   - Status: Defer until mesh ecosystem grows beyond current 31 repos

### Non-Candidates (Will Not Consolidate)

1. **Research workflows**
   - Zone status: Read-only per CLAUDE.md; no changes to consolidation policy
   - Status: Frozen unless research zone reactivates

2. **Audit workflows**
   - Intentional separation by schedule and scope
   - Status: Each audit serves a distinct governance or monitoring function; separation prevents fault cascades

---

## Verification & Health Checks

### Current Metrics

```bash
# Total workflows
$ ls .github/workflows/*.yml | wc -l
42

# By trigger type
$ grep -l "schedule:" .github/workflows/*.yml | wc -l
21

$ grep -l "pull_request:" .github/workflows/*.yml | wc -l
28

$ grep -l "push:" .github/workflows/*.yml | wc -l
12
```

### Recommended Ongoing Checks

1. **Watch for new workflows**
   - Every new workflow should be classified and added to this audit
   - Pattern: 4 categories (critical gates, audits, frameworks, maintenance)

2. **Monitor consolidation opportunities**
   - If two workflows run at the same time and same scope → consider future consolidation
   - If a workflow's purpose overlaps >80% with another → flag for review

3. **Audit for timeout/resource issues**
   - Track total CI/CD runtime per day
   - Watch for workflows exceeding 30-minute timeout (may need splitting)

---

## Quick Reference

**Emergency: Need to disable a workflow temporarily?**
1. Rename `.github/workflows/name.yml` to `.github/workflows/name.yml.disabled`
2. Create a PR explaining temporary disable reason
3. Remove `.disabled` suffix when re-enabling

**Adding a new workflow?**
1. Classify as one of: critical gate, scheduled audit, framework, maintenance
2. Document schedule/trigger in `.github/WORKFLOWS.md` (this file)
3. Ensure no duplicate scope with existing workflows
4. Run `workflow-lint.yml` validation before merge

**Want to consolidate workflows?**
1. Verify both workflows serve the same scope (not just same schedule)
2. Ensure consolidation does not break fault isolation (audit workflows)
3. Test consolidated workflow passes all checks
4. Document consolidation in `.github/WORKFLOWS.md`
5. Open PR with justification; await Z2 review

---

**Governance:** This audit is informational (Z1 documentation). Changes to workflow structure require Z2 ratification via PR review.
