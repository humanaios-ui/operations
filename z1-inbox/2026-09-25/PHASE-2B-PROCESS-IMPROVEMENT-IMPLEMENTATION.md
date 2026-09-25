# Phase 2B: Process Improvement & Behavioral Data Capture — Implementation Plan

**Status:** IN PROGRESS  
**Start Date:** 2026-09-25  
**Duration:** 1 week (MVP) + ongoing refinement  
**molt_tier Operational:** 1 (tooling & documentation)  
**molt_tier Control Surface:** 2 (governance workflow changes)  
**Strategy:** Run BOTH operational + control surface simultaneously

---

## Objective

1. **Operational (Tier 1):** Implement automated path filter validator to prevent IC-032 recurrence
2. **Control Surface (Tier 2):** Integrate behavioral data capture into governance workflow itself
3. **Data Integration:** Capture workflow trigger patterns for evidence-based Phase 2C decisions

---

## Part 1: Path Filter Validator (Operational, Tier 1)

### 1.1 Validator Implementation

**File:** `tools/workflow_path_validator.py`

**Purpose:** Verify all paths in workflow path filters actually exist in repository

**Functionality:**
```python
#!/usr/bin/env python3
# workflow_path_validator.py
# Validates that all paths referenced in workflow path filters exist in repo

import yaml
import sys
from pathlib import Path

def validate_workflow_paths(workflow_file):
    """
    Check if all paths in a workflow's path filter exist in repo.
    Returns: (is_valid, errors, warnings)
    """
    with open(workflow_file) as f:
        workflow = yaml.safe_load(f)
    
    errors = []
    warnings = []
    repo_root = Path('.')
    
    # Extract all path filters from workflow triggers
    for trigger_name, trigger_config in workflow.get('on', {}).items():
        if isinstance(trigger_config, dict) and 'paths' in trigger_config:
            paths = trigger_config['paths']
            for path_pattern in paths:
                # Check if path exists (handle globs)
                if path_pattern.endswith('/**'):
                    base_path = path_pattern[:-3]
                else:
                    base_path = path_pattern
                
                if not (repo_root / base_path).exists():
                    errors.append(f"Path '{path_pattern}' not found in repo")
    
    return len(errors) == 0, errors, warnings
```

**Usage:**
```bash
python3 tools/workflow_path_validator.py .github/workflows/quality-baseline.yml
# Output: ✅ All paths valid (8/8 files exist)

python3 tools/workflow_path_validator.py .github/workflows/governance-files.yml
# Output: ✅ All paths valid (3/3 files exist)
```

**Testing:**
- Test on Phase 1 workflows (should pass)
- Test on hypothetical broken workflow (should catch non-existent paths)
- Integration test: Run as pre-commit hook

---

### 1.2 Pre-Merge Validation

**Integration:** Add to PR workflow or pre-commit hook

**Option A: GitHub Actions Check (Recommended)**
```yaml
# .github/workflows/workflow-validation.yml
name: Workflow Path Validation

on:
  pull_request:
    paths:
      - '.github/workflows/*.yml'
      - 'tools/workflow_path_validator.py'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v7
      - run: python3 tools/workflow_path_validator.py .github/workflows/*.yml
```

**Option B: Pre-commit Hook**
```bash
# .git/hooks/pre-commit
for workflow in .github/workflows/*.yml; do
  python3 tools/workflow_path_validator.py "$workflow" || exit 1
done
```

**Recommendation:** Both — GitHub Actions (catches in PR), plus pre-commit (catches locally).

---

### 1.3 Documentation Update

**Add to:** `CLAUDE.md` (Z2 governance file)

**Section:** "Pre-Merge Checklist for Workflow Changes"

```markdown
### Workflow Path Filter Checklist

Before submitting a PR that modifies any `.github/workflows/*.yml`:

1. Run local validation:
   ```bash
   python3 tools/workflow_path_validator.py .github/workflows/<your-workflow>.yml
   ```
   Expected: ✅ All paths valid

2. Verify manually: Open the workflow file and check that each path filter entry:
   - Points to an actual file or directory in the repository
   - Uses correct glob syntax (`**` for recursive, `/*` for single-level)
   - Is not referring to deprecated or moved files

3. Update PR body: Include output of validator in PR description

4. CI Gate: GitHub Actions will automatically validate all modified workflows
```

---

## Part 2: Control Surface Integration — Behavioral Data Capture (Tier 2)

### 2.1 Governance Workflow Enhancement

**Concept:** Add behavioral telemetry to the governance validation workflow itself.

**File:** `.github/workflows/governance-files.yml` (enhance existing)

**New Feature:** Emit structured behavioral data when workflows run

**Implementation:**
```yaml
# Add to governance-files.yml (after validation step)
- name: Capture Workflow Behavior Data
  if: always()  # Run even if validation fails
  run: |
    cat > /tmp/workflow_behavior.json << 'EOF'
    {
      "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
      "pr_number": "${{ github.event.pull_request.number }}",
      "pr_title": "${{ github.event.pull_request.title }}",
      "workflow": "governance-files",
      "trigger_reason": "${{ github.event_name }}",
      "files_changed": ${{ toJson(github.event.pull_request.modified_files || []) }},
      "validation_result": "${{ job.status }}",
      "path_filter_hit": true
    }
    EOF
    
    # Upload to artifact for collection
    mkdir -p workflow_telemetry
    cp /tmp/workflow_behavior.json workflow_telemetry/$(date +%s).json

- name: Upload Workflow Telemetry
  if: always()
  uses: actions/upload-artifact@v3
  with:
    name: workflow-behavior-telemetry
    path: workflow_telemetry/
    retention-days: 30
```

**Rationale:** Governance workflows emit their own execution data; this is the control surface.

---

### 2.2 Quality-Baseline Behavioral Enhancement

**File:** `.github/workflows/quality-baseline.yml` (enhance existing)

**Same pattern:** Emit structured data when workflow runs

```yaml
# Add to quality-baseline.yml
- name: Emit Workflow Trigger Data
  if: always()
  run: |
    python3 << 'EOF'
    import json
    import os
    from datetime import datetime
    
    telemetry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "workflow": "quality-baseline",
        "trigger_reason": os.getenv("GITHUB_EVENT_NAME"),
        "workflow_status": "${{ job.status }}",
        "path_filter_active": True  # We have path filters
    }
    
    with open("telemetry.json", "w") as f:
        json.dump(telemetry, f)
    EOF
```

---

### 2.3 Centralized Telemetry Collector

**File:** `tools/workflow_telemetry_collector.py`

**Purpose:** Aggregate workflow behavior data across all runs

**Functionality:**
```python
#!/usr/bin/env python3
# workflow_telemetry_collector.py
# Collects and aggregates workflow behavioral data

import json
import sys
from pathlib import Path
from datetime import datetime

def collect_telemetry(artifact_dir):
    """
    Collect all telemetry files from GitHub Actions artifacts.
    Returns: aggregated behavioral data for analysis.
    """
    data = {
        "collection_period": {
            "start": None,
            "end": None
        },
        "workflows": {
            "quality-baseline": {
                "runs": 0,
                "successful": 0,
                "failed": 0,
                "path_filter_hits": 0,
                "avg_duration": None
            },
            "governance-files": {
                "runs": 0,
                "successful": 0,
                "failed": 0,
                "path_filter_hits": 0,
                "avg_duration": None
            }
        },
        "pr_patterns": {
            "code_only": 0,
            "governance_only": 0,
            "mixed": 0,
            "docs_only": 0
        }
    }
    
    # Aggregate telemetry files
    for telemetry_file in Path(artifact_dir).glob("*.json"):
        with open(telemetry_file) as f:
            record = json.load(f)
        
        workflow = record.get("workflow")
        if workflow in data["workflows"]:
            data["workflows"][workflow]["runs"] += 1
            if record.get("validation_result") == "success":
                data["workflows"][workflow]["successful"] += 1
            else:
                data["workflows"][workflow]["failed"] += 1
    
    return data
```

**Output:** Weekly behavioral summary for Z2 review

---

## Part 3: Running Both Tier 1 + Tier 2 Simultaneously

### Strategy: Dual-Track Rollout

**Why both together:** 
- Tier 1 (operational validator) has no governance risk
- Tier 2 (behavioral data capture) only adds telemetry, doesn't change behavior
- Both enhance the same governance workflow, so deploy together is efficient

### Rollout Plan

**Week 1 (Days 1-3): Development**
1. Create `tools/workflow_path_validator.py` (Tier 1)
2. Add telemetry emission to both workflows (Tier 2)
3. Create `tools/workflow_telemetry_collector.py` (Tier 2)
4. Write tests for validator
5. Document in CLAUDE.md (Tier 1) and .github/TELEMETRY.md (Tier 2)

**Week 1 (Days 4-5): Internal Testing**
1. Test validator on existing workflows
2. Test telemetry capture on internal PRs
3. Verify data collection and aggregation
4. No changes to production yet

**Week 1 (Day 6): Z2 Submission**
1. Create PR with:
   - Tier 1 changes (validator, validation doc)
   - Tier 2 changes (telemetry in workflows, collector)
2. Submit to Z2 for single ratification (both tiers together)
3. Mark molt_tier as "1+2 (operational + control surface)"

**Week 2 (after Z2 approval): Merge & Deploy**
1. Z2 ratifies both tiers
2. Merge to main
3. Telemetry collection begins automatically on next PR

### molt_tier Handling

**Question for Z2:** Can we classify this as "Tier 1.5" or do we need dual ratification?

**Proposed approach:**
```
molt_tier_claimed: 1.5  (primary: operational tooling; secondary: control surface telemetry)
molt_tier_rationale: "Validator is operational tool (Tier 1), telemetry collection is control surface instrumentation (Tier 2). Deployed together as single coherent improvement to Phase 1."
```

**Alternative (if Z2 wants strict separation):**
```
Create TWO PRs:
  - PR #X: Validator only (Tier 1)
  - PR #X+1: Telemetry only (Tier 2)
```

---

## Integration with Phase 2A (Monitoring)

**Data Flow:**
```
Phase 2A (Manual Monitoring)
  ↓
  Collects deployment counts, samples PRs manually
  ↓
Phase 2B Telemetry (Automated Behavioral Data)
  ↓
  Collects workflow trigger patterns from GitHub Actions artifacts
  ↓
Combined Analysis Report
  ↓
  → Used by Z2 to decide Phase 2C (expand filters) or 2D (Vercel config)
```

**Synergy:** Phase 2A provides big-picture metrics; Phase 2B provides detailed behavioral patterns.

---

## Deliverables

### Tier 1 (Operational)
- ✅ `tools/workflow_path_validator.py` (linter)
- ✅ `.github/workflows/workflow-validation.yml` (CI gate)
- ✅ CLAUDE.md update (pre-merge checklist)
- ✅ Unit tests for validator
- ✅ Pre-commit hook setup (optional)

### Tier 2 (Control Surface)
- ✅ Enhanced `governance-files.yml` (telemetry emission)
- ✅ Enhanced `quality-baseline.yml` (telemetry emission)
- ✅ `tools/workflow_telemetry_collector.py` (aggregator)
- ✅ `.github/TELEMETRY.md` (data spec + retention policy)
- ✅ Weekly behavioral data export (CSV or JSON)

### Documentation
- ✅ CLAUDE.md section: "Workflow Path Filter Pre-Merge Checklist"
- ✅ .github/TELEMETRY.md: Behavioral data format & governance
- ✅ tools/README.md: Validator & collector usage

---

## Timeline

- **2026-09-25:** Development start (both tiers in parallel)
- **2026-09-28:** Internal testing complete
- **2026-09-29:** Z2 submission (PR with both tiers)
- **2026-09-30:** Z2 review + decision (ratify together or split?)
- **2026-10-01:** Merge to main (both tiers live)
- **2026-10-02:** First behavioral data collection (on PR activity)

**Note:** Phase 2A monitoring runs independently during this time.

---

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Validator has bugs | Unit tests + dry-run on existing workflows |
| Telemetry overhead | Use GitHub Actions artifacts (no API calls) |
| Z2 rejects Tier 2 | Deploy Tier 1 only; revisit Tier 2 later |
| Mixed molt_tier confuses approvals | Clear documentation + single PR ratification |

---

## Success Criteria

✅ **Tier 1:** Validator catches non-existent paths (test with fake workflow)  
✅ **Tier 2:** Telemetry collected on 100% of PR runs (verify artifacts exist)  
✅ **Integration:** Phase 2A + 2B data flows together for combined analysis  
✅ **Documentation:** Pre-merge checklist prevents IC-032 recurrence  
✅ **Governance:** Z2 ratifies both tiers successfully  

---

## Next Steps

1. **Z1 develops** both tiers in parallel (Days 1-3)
2. **Z1 tests** internally (Days 4-5)
3. **Z1 submits** PR with molt_tier decision question for Z2 (Day 6)
4. **Z2 reviews** and decides (Day 7)
5. **Z2 ratifies** and we merge (after approval)

---

**Status:** READY TO START  
**Awaiting:** Permission to begin development immediately  
**molt_tier:** 1 (operational) + 2 (control surface) — running together  
**Question for Z2:** Should both tiers be ratified as single "1.5" or split?
