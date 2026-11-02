# Workflow Telemetry Guide

**Phase 2B: Behavioral Data Capture for CI/CD Process Improvement**

This guide documents the workflow telemetry system deployed in Phase 2B, including data schema, collection mechanics, aggregation queries, and analysis patterns.

---

## Overview

### What Is Workflow Telemetry?

Telemetry is structured behavioral data emitted by GitHub Actions workflows to understand:
- **When workflows trigger or skip** (path filter effectiveness)
- **PR intent vs. actual workflow execution** (code vs. governance vs. docs changes)
- **Deployment frequency patterns** (baseline vs. optimized; Phase 1 CI consolidation impact)
- **Edge cases and unexpected behavior** (failures, retries, rate limit pressure)

### Why Telemetry Matters

**IC-032 Prevention (Claim-vs-Tree Mismatch):**
- Phase 1 had a gap: handoff claimed fix was applied, but merged code still had non-existent file references
- Telemetry provides proof that workflows are running correctly and path filters work as designed
- Tier 1 (path validator) + Tier 2 (telemetry) = end-to-end confidence

**Deployment Frequency Optimization (Phase 1 Verification):**
- Phase 1 claimed 60-70% reduction in deployment frequency
- Phase 2A monitoring (14-day window) uses telemetry to verify actual reduction
- Telemetry data enables per-workflow analysis to identify remaining optimization opportunities

### Data Collection Lifecycle

```
Workflow runs (pull_request, push, workflow_dispatch)
    ↓
Telemetry emission step ("Emit Workflow Telemetry")
    ↓
Structured JSON written to telemetry.json
    ↓
GitHub Actions artifact storage ("Upload Telemetry Artifact")
    ↓
Retained for 30 days (configurable)
    ↓
Daily download & aggregation (tools/workflow_telemetry_collector.py)
    ↓
Human-readable report + JSON analysis file
    ↓
Phase 2A monitoring report (final verdict on Phase 1 claims)
```

---

## Data Schema

### Telemetry Record Structure

Each workflow run emits a JSON record with the following fields:

```json
{
  "timestamp": "2026-09-25T14:30:00.123456Z",
  "workflow": "quality-baseline",
  "trigger_reason": "pull_request",
  "path_filter_active": true,
  "path_filter_hit": true,
  "validation_result": "success",
  "pr_number": 543,
  "pr_title": "docs: update README"
}
```

### Field Definitions

| Field | Type | Description | Example |
|:------|:-----|:-----------|:--------|
| `timestamp` | ISO8601 | When the workflow completed (UTC) | `"2026-09-25T14:30:00.123456Z"` |
| `workflow` | string | Workflow name (from workflow definition) | `"quality-baseline"` |
| `trigger_reason` | enum | What triggered the workflow | `"pull_request"` \| `"push"` \| `"workflow_dispatch"` |
| `path_filter_active` | bool | Whether path filters are configured on this workflow | `true` |
| `path_filter_hit` | bool | Whether the PR/push matched the path filter (should run) | `true` |
| `validation_result` | enum | Workflow job status | `"success"` \| `"failure"` |
| `pr_number` | int (optional) | GitHub PR number (only for pull_request trigger) | `543` |
| `pr_title` | string (optional) | GitHub PR title (only for pull_request trigger) | `"docs: update README"` |

### Data Quality Notes

**Guaranteed fields:** `timestamp`, `workflow`, `trigger_reason`, `path_filter_active`, `path_filter_hit`, `validation_result`

**Optional fields:** `pr_number`, `pr_title` (only present for `pull_request` trigger)

**Always collected:** Telemetry step runs with `if: always()` condition, so data is captured even when workflow jobs fail

**Retention:** GitHub Actions artifacts retained for 30 days by default (can be configured per workflow)

---

## Workflow-Specific Telemetry

### quality-baseline.yml

**Purpose:** Validates code quality (lint, type check, pytest suite)

**Telemetry Emitted:**
```json
{
  "timestamp": "2026-09-25T14:30:00Z",
  "workflow": "quality-baseline",
  "trigger_reason": "pull_request",
  "path_filter_active": true,
  "path_filter_hit": true,
  "validation_result": "success",
  "pr_number": 543,
  "pr_title": "feat: add telemetry to workflows"
}
```

**Path Filter Configuration:**
- Triggers when: `src/`, `tools/`, `acat/`, `tests/`, `calibration_profiles/`, `audits/`, `requirements.txt`, `setup.py` change
- Skips when: documentation, governance config, metadata-only changes

**Analytics:** Track code PR frequency, quality failure rate, average runtime

---

### governance-files.yml

**Purpose:** Validates governance file registry consistency

**Telemetry Emitted:**
```json
{
  "timestamp": "2026-09-25T14:35:00Z",
  "workflow": "governance-files",
  "trigger_reason": "pull_request",
  "path_filter_active": true,
  "path_filter_hit": false,
  "validation_result": "skipped",
  "pr_number": 544,
  "pr_title": "docs: fix typo"
}
```

**Path Filter Configuration:**
- Triggers when: `.gov-control/`, `GOVERNANCE_FILES.md` change
- Skips when: code, documentation, other governance files change

**Analytics:** Track governance change frequency, validation pass rate, false positive rate

---

### workflow-path-validation.yml (Phase 2B)

**Purpose:** Validates all workflow path filter references exist in repository (Tier 1 IC-032 prevention)

**Telemetry Emitted:**
```json
{
  "timestamp": "2026-09-25T14:40:00Z",
  "workflow": "workflow-path-validation",
  "trigger_reason": "pull_request",
  "validation_target": "workflow_files",
  "validation_result": "success",
  "pr_number": 545,
  "pr_title": "ci: add path filter to new workflow"
}
```

**Analytics:** Track workflow file changes, path validation pass rate, common path mistakes

---

## Collection & Aggregation

### Manual Telemetry Download

```bash
# Download all telemetry artifacts from a GitHub Actions run
gh run artifacts <run_id> --pattern "workflow-telemetry-*"

# Or download from a specific PR
gh pr view <pr_number> --json status,number
```

### Automated Aggregation

Use `tools/workflow_telemetry_collector.py` to aggregate multiple telemetry files:

```bash
# Download artifacts directory from Actions (via GitHub CLI or UI)
mkdir -p workflow_telemetry
cd workflow_telemetry

# Run collector on downloaded artifacts
python3 ../tools/workflow_telemetry_collector.py . telemetry_report.json

# View human-readable report
cat telemetry_report.txt  # printed by collector

# Programmatic analysis
python3 << 'EOF'
import json
with open("telemetry_report.json") as f:
    data = json.load(f)
    
print(f"Quality-baseline: {data['workflows']['quality-baseline']['runs']} runs")
print(f"Success rate: {data['workflows']['quality-baseline']['successful']} / {data['workflows']['quality-baseline']['runs']}")
print(f"Path filter hits: {data['workflows']['quality-baseline']['path_filter_hits']}")
EOF
```

### Telemetry Report Schema

The `telemetry_report.json` output from the collector has this structure:

```json
{
  "collection_period": {
    "start": "2026-09-25T00:00:00Z",
    "end": "2026-10-02T23:59:59Z",
    "file_count": 42
  },
  "workflows": {
    "quality-baseline": {
      "runs": 28,
      "successful": 26,
      "failed": 2,
      "path_filter_hits": 18,
      "trigger_reasons": {
        "pull_request": 20,
        "push": 8
      },
      "avg_duration_seconds": null
    },
    "governance-files": {
      "runs": 8,
      "successful": 8,
      "failed": 0,
      "path_filter_hits": 5,
      "trigger_reasons": {
        "pull_request": 3,
        "push": 5
      },
      "avg_duration_seconds": null
    }
  },
  "pr_patterns": {
    "code_only": 12,
    "governance_only": 2,
    "mixed": 4,
    "docs_only": 6,
    "dependency_only": 1,
    "other": 0
  },
  "per_workflow_details": [
    { /* individual telemetry record 1 */ },
    { /* individual telemetry record 2 */ },
    // ... 40 more records
  ]
}
```

---

## Phase 2A Analysis Patterns

### Hypothesis: Path Filters Reduce Deployment Frequency

**Query:** Deployment frequency before/after Phase 1

```python
def analyze_deployment_frequency(report):
    """Calculate deployment frequency from telemetry data."""
    
    quality = report['workflows']['quality-baseline']
    governance = report['workflows']['governance-files']
    
    # Total workflows triggered
    total_runs = quality['runs'] + governance['runs']
    
    # Path filter effectiveness
    quality_skip_rate = 1 - (quality['path_filter_hits'] / quality['runs']) if quality['runs'] > 0 else 0
    governance_skip_rate = 1 - (governance['path_filter_hits'] / governance['runs']) if governance['runs'] > 0 else 0
    
    print(f"Quality-baseline skip rate: {quality_skip_rate:.1%}")
    print(f"Governance-files skip rate: {governance_skip_rate:.1%}")
    print(f"Total workflow runs: {total_runs}")
    
    # Estimate deployment frequency reduction
    # Baseline: quality + governance run on every PR (2 deploys)
    # After Phase 1: only appropriate workflows run (≤1 deploy per PR)
    avg_deploys_per_pr = (quality['path_filter_hits'] + governance['path_filter_hits']) / max(1, total_runs)
    
    print(f"Average deploys per workflow run: {avg_deploys_per_pr:.2f}")
    return {
        'quality_skip_rate': quality_skip_rate,
        'governance_skip_rate': governance_skip_rate,
        'avg_deploys_per_run': avg_deploys_per_pr
    }
```

### Hypothesis: Path Filter Configuration Protects Against IC-032

**Query:** Workflow path validation success rate

```python
def analyze_path_validation(report):
    """Calculate path filter validation robustness."""
    
    if 'workflow-path-validation' not in report['workflows']:
        print("Path validation workflow not deployed yet")
        return None
    
    validation = report['workflows']['workflow-path-validation']
    
    success_rate = validation['successful'] / validation['runs']
    print(f"Path validation success rate: {success_rate:.1%}")
    print(f"Failed validations: {validation['failed']}")
    
    if validation['failed'] > 0:
        print("⚠️  IC-032 risk detected: invalid path filters exist in repository")
    else:
        print("✅ IC-032 protected: all workflow paths valid")
    
    return {
        'success_rate': success_rate,
        'ic032_protected': validation['failed'] == 0
    }
```

### Hypothesis: PR Intent Classification

**Query:** Distribution of PR types (code vs. docs vs. governance)

```python
def analyze_pr_intent(report):
    """Analyze PR intent distribution."""
    
    patterns = report['pr_patterns']
    total = sum(patterns.values())
    
    for intent, count in patterns.items():
        pct = (count / total * 100) if total > 0 else 0
        print(f"{intent:20s}: {count:3d} PRs ({pct:5.1f}%)")
    
    # Estimate Vercel rate limit impact
    # Only code PRs should trigger quality-baseline
    unnecessary_deploys = patterns['docs_only'] + patterns['governance_only']
    print(f"\nUnnecessary deployments prevented: ~{unnecessary_deploys} (by path filters)")
```

---

## Troubleshooting

### Telemetry Not Collected

**Symptom:** No telemetry.json artifact appears after workflow run

**Causes & Fixes:**
1. **Telemetry step not added to workflow**
   - Fix: Add "Emit Workflow Telemetry" and "Upload Telemetry Artifact" steps (see template below)
2. **Artifact retention expired**
   - Fix: Increase `retention-days` in Upload Telemetry Artifact step (default: 30)
3. **Job failed before telemetry step**
   - Fix: Ensure telemetry step has `if: always()` condition (runs even on failure)

### Telemetry JSON Malformed

**Symptom:** `workflow_telemetry_collector.py` fails with JSON parsing error

**Causes & Fixes:**
1. **Missing quotes in JSON**
   - Fix: Use `json.dump()` not f-strings for JSON serialization
2. **Workflow name contains special characters**
   - Fix: Ensure workflow names are alphanumeric + hyphen only
3. **GitHub Actions secret interpolation failed**
   - Fix: Verify `${{ github.event_name }}` syntax is correct

### Path Validation Fails on Valid Paths

**Symptom:** workflow_path_validator.py reports paths not found, but they exist

**Causes & Fixes:**
1. **Path globbing not supported**
   - Issue: `src/**` glob patterns require special handling
   - Fix: Script handles `/**` suffix correctly; ensure glob follows GitHub Actions conventions
2. **YAML "on:" parsing issue**
   - Issue: Python's `yaml.safe_load()` converts `on:` key to boolean `True`
   - Fix: Check for both string key `"on"` and boolean key `True`

---

## Telemetry Emission Template

To add telemetry to a new workflow, include this step at the end (after all jobs):

```yaml
- name: Emit Workflow Telemetry (Phase 2B)
  if: always()
  run: |
    python3 << 'TELEMETRY_EOF'
    import json
    from datetime import datetime

    telemetry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "workflow": "your-workflow-name",
        "trigger_reason": "${{ github.event_name }}",
        "path_filter_active": True,
        "path_filter_hit": True,
        "validation_result": "${{ job.status }}"
    }

    # Add PR context if available
    if "${{ github.event_name }}" == "pull_request":
        telemetry["pr_number"] = "${{ github.event.pull_request.number }}"
        telemetry["pr_title"] = "${{ github.event.pull_request.title }}"

    with open("telemetry.json", "w") as f:
        json.dump(telemetry, f, indent=2)
    TELEMETRY_EOF

- name: Upload Telemetry Artifact
  if: always()
  uses: actions/upload-artifact@v3
  with:
    name: workflow-telemetry-your-workflow-name
    path: telemetry.json
    retention-days: 30
```

---

## Phase 2A Monitoring Checklist

**2026-09-25 to 2026-10-02 (14-day observation window)**

- [ ] Day 1-3: Collect telemetry baseline (20+ artifact collections)
- [ ] Day 4-7: Aggregate data, verify schema, check for collection gaps
- [ ] Day 8-10: Run analysis queries (deployment frequency, path filter effectiveness, PR intent patterns)
- [ ] Day 11-13: Verify Phase 1 claims (60-70% frequency reduction, IC-032 protection)
- [ ] Day 14: Final report, file findings/hypotheses, hand off to Z2

**Success Criteria:**
- ✅ All telemetry records valid JSON
- ✅ Path filter effectiveness ≥60% (docs PRs skip quality checks)
- ✅ Path validation success rate = 100% (no IC-032 incidents)
- ✅ Deployment frequency reduction matches Phase 1 estimate (2-3/day vs. 5-8/day)

---

## References

- **Phase 2B Telemetry Implementation:** PR #538
- **Phase 1 CI Consolidation:** PR #541
- **Path Validator Tool:** `tools/workflow_path_validator.py`
- **Telemetry Collector Tool:** `tools/workflow_telemetry_collector.py`
- **Governance:** `/CLAUDE.md` (Z1/Z2/Z3 authority model, molt tiers)
- **Phase 2A Handoff:** `/z1-inbox/2026-09-25/HANDOFF-PHASE-2B-TELEMETRY.md`

---

**Last Updated:** 2026-09-28  
**Author:** Claude (Z1 Proposer)  
**Status:** Phase 2B Follow-Up PR #2 (Enhanced Documentation)  
**Audience:** Z1 (proposers), Z2 (ratifier), Phase 2A monitoring coordinators
