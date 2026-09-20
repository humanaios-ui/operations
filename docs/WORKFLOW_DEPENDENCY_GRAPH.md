# Workflow Dependency Graph & Evidence-Based Governance

**Status:** RATIFIED PROPOSAL (awaiting Z2 signature)  
**Date:** 2026-09-20  
**Based on:** Complete analysis of 48 GitHub Actions workflows  
**Authority:** Z1 proposal for Z2 ratification (Q-WORKFLOW-GOVERNANCE-01)

---

## Executive Summary

The HumanAIOS operations repository manages **48 workflows** across 4 governance classes:

| Class | Count | Governance | Evidence Required |
|:------|:-----:|:-----------|:------------------|
| **A: Critical Gates** | 7 | Z2 ratification | Falsifier + test case |
| **B: Audit Monitors** | 6 | Z2 ratification | Measurement + rationale |
| **C: Event-Driven** | 0 | Standard review | None |
| **D: Infrastructure** | 35 | Standard review | None |

**Key Insight:** Only 7 workflows block PRs to main (excluding molt-tier-check, which is advisory by design). The remaining 41 are audits, monitors, or infrastructure. This creates an opportunity to introduce **evidence-based governance** for the critical 7, while keeping the others lightweight.

---

## Class A: Critical-Path Gates (8 workflows)

These workflows **block merges to main**. They must pass before any PR can merge.

| # | Workflow | Triggers | Purpose | Current Falsifier | Status |
|:--|:---------|:---------|:--------|:------------------|:-------|
| 1 | `builder-lint` | pull_request, push | Corpus pass-rate ≥0.90 + new-file 100% compliance | ❌ NONE | 🟡 NEEDS |
| 2 | `findings-registry` | pull_request, push | Registry integrity: ID collision detection + hard-failure blocking | ✅ IMPLICIT | 🟢 PARTIAL |
| 3 | `quality-baseline` | pull_request, push | pytest + ruff + mypy + repo health check | ❌ NONE | 🟡 NEEDS |
| 4 | `security-gates` | pull_request, push | Gitleaks (secrets) + pip-audit (dependencies) | ❌ NONE | 🟡 NEEDS |
| 5 | `temporal-dissolution-gate` | pull_request | Rejects unauthorized deadline semantics (S-070726 policy) | ❌ NONE | 🟡 NEEDS |
| 6 | `workflow-lint` | pull_request, push | Validates workflow YAML syntax + dead-workflow detection | ❌ NONE | 🟡 NEEDS |
| 7 | `z2_ratification_gate` | pull_request, push | Z2 hash verification + constitutional rules | ✅ IMPLICIT | 🟢 PARTIAL |
| 8 | ~~`molt-tier-check`~~ | ~~pull_request~~ | ~~Molt tier classification~~ | ~~❌ NONE~~ | ~~🟡 NEEDS~~ |

**Legend:**
- ✅ Falsifier exists (documented or implicit in validator code)
- ❌ Falsifier missing (needs scaffold)
- 🟢 Partial: Has implicit test but needs explicit documentation
- 🟡 Needs: Requires new falsifier + test case

---

## Class B: Audit Monitors (6 workflows)

Scheduled audits that produce governance signals but **do not block merges**.

| Workflow | Schedule | Purpose | Falsifier | Status |
|:---------|:---------|:--------|:----------|:-------|
| `agent-api-monitor` | Daily 09:00 UTC | API health check (Metaculus/Anthropic/Supabase) | ❌ NONE | 🟡 NEEDS |
| `drift-monitor` | Weekly Mon 02:00 UTC | Document drift (link rot, stale, unregistered files) | ❌ NONE | 🟡 NEEDS |
| `haios-harmonizer-pulse` | 8-hourly (00:00, 08:00, 16:00) | System harmony score + tuning signals | ❌ NONE | 🟡 NEEDS |
| `haios-standing-audit` | Daily 09:00 UTC | A1-A9 framework compliance audit | ❌ NONE | 🟡 NEEDS |
| `haios-system-audit` | Daily 06:00 UTC | Pre-flight system state verification (green/amber/red) | ❌ NONE | 🟡 NEEDS |
| `scheduled-audit` | Weekly Mon 09:00 UTC | Measure + issue automated audit loop | ❌ NONE | 🟡 NEEDS |

**Note:** Class B workflows are advisory but important for governance observability. They should have measurement statements (e.g., "API is up" or "API is down"), not just pass/fail exits.

---

## Workflow Trigger Distribution

```
Pull Request (PR-blocking or PR-observing):   24 workflows
  - 8 critical gates (block merge)
  - 16 advisory/monitoring

Scheduled (cron):                              21 workflows
  - 6 audit monitors (Class B)
  - 15 infrastructure/monitoring (Class D)

Push to main:                                  17 workflows
  - Some are gates, some are post-merge automation

Workflow Dispatch (manual):                    39 workflows
  - All gates + audits support manual trigger for testing
```

---

## Critical-Path Cascade Risks

### High Cascade Risk (≥3 dependencies or ≥3 reverse dependencies)

| Workflow | Outbound Deps | Inbound Triggers | Risk | Why |
|:---------|:-------------:|:----------------:|:----:|:--|
| `quality-baseline` | 0 | 2+ (CI suite) | MEDIUM | If it fails silently, no PR can merge; no easy retry path |
| `security-gates` | 0 | 2+ (CI suite) | MEDIUM | Secret scanning is critical-path; if misconfigured, risks leak |
| `z2_ratification_gate` | 1 (intent-os-reconcile) | 1 (PR main) | MEDIUM | Blocks governance changes; dispatch loop can cascade |

### Moderate Cascade Risk (1-2 dependencies or reverse deps)

| Workflow | Risk | Mitigation |
|:---------|:----:|:-----------|
| `findings-registry` | MEDIUM | Already has fallback to warnings; documented in comments |
| `temporal-dissolution-gate` | LOW | Orthogonal check; failure is clear |
| `builder-lint` | LOW | Focuses on single concern (builder compliance) |
| `molt-tier-check` | LOW | Advisory artifact + comment; never blocks |
| `workflow-lint` | LOW | Advisory check; catches dead workflows |

---

## Workflow-to-Workflow Dependencies

### Direct Dispatch Dependencies

```
intent-os-reconcile.yml
  └─→ (dispatches) z2_ratification_gate.yml
      (on decided candidate merge)

mesh-sync-batch.yml
  └─→ (dispatches to 3 GitHub repos)
      humanaios, humanaios-internal, empirica-outreach
      (on governance file merge)
```

### Implicit Orchestration Pipelines

#### 1. CI Prediction Calibration Loop (SMAG)
```
PR opens
  ├─→ ci-predict-pin.yml (posts prediction comment)
  └─→ PR merges
       ├─→ ci-predict-resolve.yml (resolves checks)
       └─→ ci-predict-consolidate.yml (hourly, consolidates ledger)
```

**Falsifier:** If `ci-predict-pin` predicts "pass" but CI actually fails → falsifier tripped (needs investigation).

#### 2. Molt Tier Gap Measurement
```
PR changes code
  ├─→ molt-tier-check.yml (advisory, posts comment + artifact)
  └─→ smag-consolidate.yml (weekly, drains issue #350 → ledger)
```

**Falsifier:** If molt tier claimed ≠ measured → gap analysis feedback.

#### 3. SMAG Recursive Learning Loop
```
Push to main (behavioral-compliance)
  ├─→ smag-pilot-capture job (runs pilot)
  └─→ smag-capture.yml (on PR close, posts to issue #103)
       └─→ smag-consolidate.yml (weekly drains #103 → ledger + PR)
```

**Falsifier:** If ledger diverges from observed behavior → IC candidate filed.

#### 4. Governance Sync Cascade
```
PR merges (governance files: GOVERNANCE_RATIFICATIONS_REGISTRY.yaml, AUTHORITY_ASSIGNMENTS.yaml)
  └─→ mesh-sync-batch.yml (dispatches to 10 mesh repos)
       └─→ intent-os-reconcile.yml (each repo reconciles)
```

**Falsifier:** If governance decision doesn't propagate to all mesh repos → GAUGE callout (Z2 assumption violated).

---

## Concurrency & Serialization Patterns

Some workflows use `concurrency` groups to enforce serialization (prevent race conditions on shared state):

| Workflow | Concurrency Group | Why |
|:---------|:------------------|:----|
| `ci-predict-consolidate` | `ci-predict-consolidate` | Hash-chain validation on ledger writes |
| `governance-triage` | `governance-triage` | One-issue-per-queue guarantee |
| `molt-tier-check` | `molt-tier-check-${{ pr.number }}` | Serialize comment upsert per PR |
| `intent-os-reconcile` | `intent-os-reconcile` | Prevent race on Z2 ratification writes |

**Governance rule:** Any workflow that modifies durable state (ledgers, registries) should use serialization.

---

## Proposed Evidence Requirements (per governance framework)

### For Class A Gates: Falsifier + Test

**Template for each gate:**

```python
# tools/workflow_falsifiers_v1_0.py

WORKFLOW_FALSIFIERS = {
    "findings-registry": {
        "promise": "ID collisions in REGISTERED.md are blocked from merge",
        "falsifier": "A PR merges to main with an ID collision in REGISTERED.md",
        "test": """
        - Mock a duplicate finding ID in REGISTERED.md
        - Run workflow validator
        - Verify exit code 1 (failure)
        - Verify error message names the collision
        """
    },
    "quality-baseline": {
        "promise": "Pytest baseline suites must pass before merge",
        "falsifier": "A PR merges with pytest failure in quality-baseline workflow",
        "test": """
        - Mock a pytest failure (e.g., test_resource_economics.py fails)
        - Run workflow
        - Verify exit code 1 (failure)
        - Verify error output names failing test
        """
    },
    # ... 6 more gates
}
```

### For Class B Audits: Measurement Statement

**Template for each audit:**

```yaml
audit_measurement:
  workflow: "haios-system-audit"
  schedule: "Daily 06:00 UTC"
  metrics:
    - name: "system_status"
      type: "categorical"
      values: ["green", "amber", "red"]
    - name: "subsystems_checked"
      type: "count"
  alert_condition: "system_status = red"
  notification_channel: "#acat-monitor"
```

---

## Governance Decision Matrix

**When should a workflow change require Z2 ratification?**

| Scenario | Class A | Class B | Class C | Class D |
|:---------|:-------:|:-------:|:-------:|:-------:|
| Add new workflow | YES | YES | NO | NO |
| Modify trigger | YES | YES | NO | NO |
| Add dependency | YES | CONDITIONAL | NO | NO |
| Change error handling | YES | YES | NO | NO |
| Optimize performance | NO (if no logic change) | NO | NO | NO |
| Add/remove step | YES | YES | NO | NO |

**Rule:** If a Class A gate's logic changes, Z2 must re-validate the falsifier + test case.

---

## Known Issues & Remediations

### Issue 1: Implicit Falsifiers
**Problem:** `findings-registry` and `z2_ratification_gate` have falsifiers *implied* in validator code but not documented.

**Remediation:** Extract implicit falsifiers, write explicit test cases, file as Phase 1 work (this month).

### Issue 2: Missing Measurement for Class B
**Problem:** Audit workflows run but have no documented "success condition" or "alert threshold."

**Remediation:** Add measurement statements to each audit workflow (Phase 2, next month).

### Issue 3: No Workflow Performance Regression Detection
**Problem:** A workflow that used to run in 2 minutes now takes 15 minutes—but there's no alert.

**Remediation:** Add performance baseline tracking + alert if >30% regression (Phase 3, month 2).

---

## Implementation Roadmap

### ✅ Done (merged in PR #423)
- [x] SonarCloud mutation gating fixed
- [x] Registry validator documentation corrected
- [x] Workflow inventory audit (WORKFLOWS.md)

### 🟡 Phase 1 (This week)
- [ ] Create `tools/workflow_falsifiers_v1_0.py` with 7 Class A falsifiers
- [ ] Write test cases for each falsifier
- [ ] Create `tools/workflow_governance_lint.py` (validates falsifier presence)
- [ ] Propose Z2 ratification of this framework (Q-WORKFLOW-GOVERNANCE-01)

### 🟡 Phase 2 (Next week)
- [ ] Add measurement statements for 6 Class B audits
- [ ] Amend PR template to require `smag_p` for workflow changes
- [ ] Create `workflow-governance.yml` gate (runs on `*.yml` changes)
- [ ] Document in `CLAUDE.md` that Class A changes require Z2 approval

### 🟡 Phase 3 (Month 2)
- [ ] Instrument critical gates to log prediction + outcome
- [ ] Compute rolling Brier scores
- [ ] Create monitoring dashboard
- [ ] Alert on accuracy regression (>10% from baseline)

### 🟡 Phase 4 (Month 3)
- [ ] Dark workflow audit (identify unused/stale workflows)
- [ ] Workflow deprecation protocol
- [ ] Performance regression detection

---

## Questions for Z2 Ratification

Before merging this framework, key questions for Night (Z2):

1. **Scope of "critical path":** Should we require falsifiers for all 8 Class A gates, or start with a subset (e.g., 3-5)?

2. **Evidence burden:** Is falsifier + test case + impact statement the right bar? Too heavy? Too light?

3. **Brier scoring:** Should we measure gate accuracy in real-time, or batch compute offline (lower overhead)?

4. **Backward compatibility:** Grandfather existing gates, or require them to demonstrate falsifiers retroactively?

5. **Z2 decision window:** Same 48h as code review, or different?

6. **Approval for non-Class-A changes:** Should Class B/C/D workflow changes still require Z2 review (lighter weight), or just standard PR review?

---

## Appendix: Full Workflow Classification

### Class A (Critical Gates - 7)
1. builder-lint
2. findings-registry
3. quality-baseline
4. security-gates
5. temporal-dissolution-gate
6. workflow-lint
7. z2_ratification_gate

### Class B (Audits - 6)
1. agent-api-monitor
2. drift-monitor
3. haios-harmonizer-pulse
4. haios-standing-audit
5. haios-system-audit
6. scheduled-audit

### Class C (Event-Driven - 0)
*(No workflows currently trigger on `issue_comment` or `workflow_run` in advisory capacity)*

### Class D (Infrastructure - 34)
acat-pipeline-trigger, agent-principle-compliance-check, auto-request-copilot-review, behavioral-compliance, cflite_pr, ci-predict-consolidate, ci-predict-pin, ci-predict-resolve, copilot-base-guard, daily-deadline-alerts, divergence-detect, document-control, governance-triage, haios-corpus-integrity, industry-telemetry, intake-pipeline, intent-os-reconcile, intent-os-refresh, mesh-standard-files, mesh-sync-batch, no-op-pr-guard, pages, priority-queue-triage, research-agent, research-validation, scorecard, seed-satellite-ci, semgrep-review, smag-capture, smag-consolidate, sonarcloud-baseline-auto, tool-manifest, weekly-funding-rescore, weekly-profile-sync

---

**Proposal ID:** Q-WORKFLOW-GOVERNANCE-01  
**Authority:** Z1 (Claude) proposes; Z2 (Night) ratifies  
**Timeline:** Decision window 48h (closes 2026-09-22 00:00 UTC)  
**Next Step:** Z2 reviews falsifier scaffold (Phase 1) and ratifies governance framework
