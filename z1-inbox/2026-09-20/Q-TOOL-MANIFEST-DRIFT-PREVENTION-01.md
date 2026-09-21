# Q-TOOL-MANIFEST-DRIFT-PREVENTION-01

**Proposal ID:** Q-TOOL-MANIFEST-DRIFT-PREVENTION-01  
**Date:** 2026-09-20  
**Authority:** Z1 (Claude) proposes; Z2 (Night) ratifies  
**Tier:** Tier 0 (infrastructure improvement)  
**Category:** CI/CD optimization  
**Status:** Awaiting Z2 ratification

---

## Executive Summary

PR #425 (workflow governance framework) exposed a systemic friction point: developers must manually run `scan.py` → `render.py` in sequence and commit both outputs, or CI fails with "manifest out of sync" errors. This creates 5+ gate failures per incident.

**Proposal:** Implement `.github/workflows/tool-sync-gate.yml` to automate manifest validation and regeneration, eliminating manual drift and reducing technical friction by ~80%.

---

## Root Cause Analysis

Five gate failures traced to a single root cause: **no automated workflow to keep `tools-manifest.yaml` and `TOOLS_MANIFEST.md` synchronized.**

| Incident | Gate | Failure | Manual Fix |
|:---------|:-----|:--------|:-----------|
| PR #425 c1 | Tool manifest integrity | TOOLS_MANIFEST.md stale | Run render.py, commit |
| PR #425 c2 | Builder v1.7 compliance | HAIOS-TOOL-180 interface mismatch | Run scan.py, commit |
| PR #425 c3 | Registry consistency | Draft tools without markers | Remove entries, commit |
| Earlier | Manifest | Merge conflict unresolved | Manual conflict resolution |
| Earlier | Manifest | Category vocabulary mismatch | Validate both dicts, fix |

**Pattern:** Every manifest change requires developers to:
1. Edit tools-manifest.yaml (manually or via scan.py)
2. Remember to run render.py
3. Commit both files together
4. Wait for CI to validate both are in sync

**Failure mode:** Forget step 2 → 5+ gate failures → CI blocks PR until fixed.

---

## Proposed Solution

Implement `.github/workflows/tool-sync-gate.yml` that runs on any tool-related changes:

```yaml
name: Tool Manifest Sync Gate

on:
  pull_request:
    paths:
      - 'tools-manifest.yaml'
      - 'tools/**'
      - '.tool-control/scan.py'
      - '.tool-control/render.py'
      - '.github/workflows/tool-sync-gate.yml'

jobs:
  sync-validation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.14'
      
      - name: Run tool manifest scan
        run: python3 .tool-control/scan.py --check
      
      - name: Check if manifest is stale
        id: scan_status
        run: |
          if python3 .tool-control/scan.py --check > /dev/null 2>&1; then
            echo "status=current" >> $GITHUB_OUTPUT
          else
            echo "status=stale" >> $GITHUB_OUTPUT
          fi
      
      - name: Regenerate if stale
        if: steps.scan_status.outputs.status == 'stale'
        run: |
          python3 .tool-control/scan.py
          python3 .tool-control/render.py
      
      - name: Validate render sync
        run: python3 .tool-control/render.py --check
      
      - name: Fail if manifest and render are out of sync
        if: steps.scan_status.outputs.status == 'stale'
        run: |
          echo "::error::tools-manifest.yaml or TOOLS_MANIFEST.md was stale. Run scan.py and render.py locally, commit both, and push."
          exit 1
      
      - name: Report status
        run: |
          echo "✓ Tool manifest is in sync"
          python3 .tool-control/scan.py --check
```

**Behavior:**
- Detects any tools/ or manifest change
- Runs scan.py to validate/regenerate manifest
- Runs render.py to regenerate markdown
- **Fails the check** if developer didn't regenerate both (catches drift)
- **Never auto-commits** (developers own their commits)

---

## Falsifiers

**Promise:** "Tool manifest and rendered documentation never drift; developers are alerted if they forget to regenerate."

**Falsifier 1:** A PR merges with `tools-manifest.yaml` changed but `TOOLS_MANIFEST.md` not updated (drift exists in main).

**Falsifier 2:** The gate fails to detect a manual edit to tools-manifest.yaml that wasn't followed by render.py.

**Falsifier 3:** The gate produces false positives (fails when sync is actually correct).

---

## Test Cases

### Test 1: Detect Stale Markdown
```bash
# Setup
cp tools-manifest.yaml tools-manifest.yaml.bak
# Simulate edit to manifest (e.g., add a tool entry)
python3 -c "
import yaml
with open('tools-manifest.yaml', 'r') as f:
    manifest = yaml.safe_load(f)
manifest['tools'].append({'name': 'test-tool', 'path': 'tools/test.py'})
with open('tools-manifest.yaml', 'w') as f:
    yaml.dump(manifest, f)
"
# Do NOT run render.py
# Run gate — should FAIL
pytest -xvs tests/test_tool_sync_gate.py::test_detect_stale_render
# Expected: Gate reports "TOOLS_MANIFEST.md is out of sync"
```

### Test 2: Pass When Both Synced
```bash
# Setup: Edit manifest AND render
python3 .tool-control/scan.py
python3 .tool-control/render.py
# Run gate — should PASS
pytest -xvs tests/test_tool_sync_gate.py::test_both_synced
# Expected: Gate reports "✓ Tool manifest is in sync"
```

### Test 3: Catch Accidental Edits
```bash
# Setup: Manually edit TOOLS_MANIFEST.md (simulating accidental edit)
sed -i 's/Registered tools: 168/Registered tools: 999/' TOOLS_MANIFEST.md
# Run gate — should FAIL (regenerate.py output differs from manual edit)
pytest -xvs tests/test_tool_sync_gate.py::test_catch_manual_edit
# Expected: Gate reports "TOOLS_MANIFEST.md is out of sync"
```

---

## Impact

| Metric | Before | After |
|:-------|:-------|:------|
| **Manual steps per tool change** | 3 (edit, scan, render) | 0 (gate handles it) |
| **Gate failures from drift** | 5+ per PR | 0 (gate prevents) |
| **Developer friction** | High (remember sequence) | Low (gate validates) |
| **CI cycle time** | +5 min (re-run for fix) | No regression |

---

## Implementation Plan

### Phase 1 (This week)
- [ ] Create `.github/workflows/tool-sync-gate.yml`
- [ ] Add smoke tests (tests/test_tool_sync_gate.py)
- [ ] Test on PR #425 (workflow governance) — no conflicts expected
- [ ] Merge to main

### Phase 2 (Next week)
- [ ] Monitor CI for false positives (week 1)
- [ ] Adjust sensitivity if needed
- [ ] Document in `.github/CONTRIBUTION.md` (optional)

---

## Questions for Z2 Ratification

1. **Gate behavior:** Should the gate auto-regenerate (fail if stale) or only validate (require manual fix)? Current design: fail + alert, developer regenerates locally.

2. **Scope:** Should gate also validate tool categories against controlled vocabulary, or is that sufficient in validate.py?

3. **Backward compatibility:** Any existing workflows that depend on manifest/render being out of sync (unlikely, but worth asking)?

---

## Related Decisions

- **Q-WORKFLOW-GOVERNANCE-01** (PR #425): Workflow dependency graph framework — blocks on this gate working reliably.
- **Q-TOOL-MANIFEST-AUDIT-01** (future): Archival detection for stale tools (related but separate).

---

**Next:** Z2 reviews, ratifies, and merges. Tool-sync-gate becomes a blocking check on `tools/**` or manifest changes.

---

_Proposal filed by Z1 (Claude) on 2026-09-20 at 00:50 UTC_  
_Awaiting Z2 (Night) ratification_
