# PR Workflow & Findings Management Guide

**Purpose:** Standardize how we handle PR review findings and maintain quality gates  
**Applies to:** All PRs in humanaios-ui/operations  
**Last Updated:** 2026-09-22  

---

## Quick Start: New PR with Findings

### 1. **Create Task for Each Finding (Session Start)**

When a PR arrives with N findings, immediately create tasks:

```bash
/task create "PR #342: Fix accuracy calculation logic (F-001)" "File: tools/smag_meta_feedback_v1_0.py. Issue: conditional returns same value. Priority: High"
/task create "PR #342: Correct tool ID allocation (F-002)" "File: tools-manifest.yaml. Issue: duplicate HAIOS-TOOL-163. Priority: High"
/task create "PR #342: Update Meta-SMAG documentation (F-003)" "File: audits/*.md. Issue: forecasts inflated. Priority: Medium"
```

This gives visible tracking and prevents losing work to context limits.

### 2. **Open PR Findings Doc** (Optional but Recommended)

Use the template at `.claude/PR_FINDINGS_TEMPLATE.md`:

```
cp .claude/PR_FINDINGS_TEMPLATE.md /tmp/pr-342-findings.md
# Open in your editor or publish as a Claude Doc for live tracking
```

Update as you fix each finding:
- Mark status: In Progress → Fixed
- Add CI validation notes
- Track blockers

### 3. **Fix Findings Systematically**

For each task:

```
1. Read the finding carefully (line numbers, context)
2. Reproduce the issue locally
3. Apply the fix (code or docs)
4. Run: ./scripts/verify_pr_readiness.sh
5. If green: /task update [task_id] --status in_progress → completed
6. If red: Debug, fix root cause, re-run verify script
7. Commit with clear message naming the finding
```

**Example flow:**
```bash
# F-001: Fix accuracy calculation
cd /home/user/operations
python3 tools/smag_meta_feedback_v1_0.py --dry-run  # Reproduce
# ... edit tools/smag_meta_feedback_v1_0.py
./scripts/verify_pr_readiness.sh  # Validate
git add tools/smag_meta_feedback_v1_0.py
git commit -m "fix(meta-smag): correct accuracy calculation logic"
/task update task_xyz --status completed
```

### 4. **Verify Before Each Push**

```bash
# Automated check of all gates
./scripts/verify_pr_readiness.sh

# If green:
git push -u origin branch-name

# If red:
# ... fix issues shown, re-run verify, re-commit
```

### 5. **Handoff: Summary for Z2**

Before merging, capture findings in the PR description or a Doc comment:

```markdown
## Findings Summary

| Finding | File | Status | Fix |
|---------|------|--------|-----|
| Accuracy calc logic | smag_meta_feedback_v1_0.py | ✓ Fixed | Rewrote conditional |
| Tool ID collision | tools-manifest.yaml | ✓ Fixed | Moved to 161 |
| Doc forecasts | audits/*.md | ✓ Fixed | Updated to ~4–5 |

**CI Status:** All 13 checks passing ✓  
**Ready for merge:** Yes ✓
```

---

## Verification Script

**Location:** `./scripts/verify_pr_readiness.sh`

**What it checks:**
- Tool manifest integrity (scan, validate, render)
- Document control integrity (scan, validate)
- Python linting (errors only)

**Usage:**
```bash
./scripts/verify_pr_readiness.sh          # Run all checks
./scripts/verify_pr_readiness.sh --verbose  # Show details
```

**Exit codes:**
- `0` = All checks passed, PR is ready
- `1` = A check failed, fix and retry

---

## Task Tracking Best Practices

### Create Upfront (Session Start)
- One task per finding
- Include file, line number, priority
- Group by category if helpful

### Update as You Go
- Mark as `in_progress` when starting
- Add notes for blockers or dependencies
- Mark as `completed` when fix is validated

### Merge Cleanup
- All tasks should be `completed` before merging
- If any remain open, that's a blocker signal

**Example Task Lifecycle:**
```
Created:     "PR #342: Fix accuracy calc"
In Progress: (after first commit)
Completed:   (after CI validates)
```

---

## Parallel Tracks (Future: Agent-Based)

For large PRs with independent fixes, consider parallel agents:

```
# Logic fixes (agent-1)
→ Fix accuracy calculation
→ Resolve tool ID collision

# Docs fixes (agent-2)
→ Update forecasts
→ Sync documentation

# Both run in parallel, merge results
```

When ready to implement, use `.claude/agents/` workflow or Workflow MCP tool.

---

## CI Validation Checkpoints

**Before each commit:**
```bash
./scripts/verify_pr_readiness.sh
```

**Before each push:**
```bash
git status                          # Verify clean
./scripts/verify_pr_readiness.sh    # Re-check
git push -u origin branch-name
```

**After push (automated):**
- GitHub Actions runs full CI suite
- Manifest integrity, quality, sonar, semgrep, Builder v1.7, etc.
- All must pass before merge

---

## Merge Strategy

**Default:** Merge commit (preserves history and authorship)

```bash
# Done automatically by GitHub or Claude tools
# Commit message format:
# "Merge pull request #XXX: [title]"
# 
# Includes summary of findings fixed and CI status
```

---

## Troubleshooting

### "Manifest is stale"
```bash
python3 .tool-control/scan.py  # Regenerate
git add tools-manifest.yaml TOOLS_MANIFEST.md
git commit -m "chore: regenerate manifest"
```

### "TOOLS_MANIFEST.md is out of sync"
```bash
python3 .tool-control/render.py  # Regenerate
git add TOOLS_MANIFEST.md
git commit -m "chore: regenerate manifest docs"
```

### "Structural rule violations"
```bash
python3 .tool-control/validate.py  # Show all violations
# Fix each violation in tools-manifest.yaml (curated fields, not mechanical)
./scripts/verify_pr_readiness.sh  # Re-check
```

### "CI passed locally but fails on GitHub"
- Check network (proxy, CA bundle)
- Verify all files are committed (`git status`)
- Re-run verify script before pushing
- If GitHub-specific, check runner environment (Python version, dependencies)

---

## Related Files

- **Verification Script:** `scripts/verify_pr_readiness.sh`
- **Findings Template:** `.claude/PR_FINDINGS_TEMPLATE.md`
- **This Guide:** `.claude/PR_WORKFLOW_GUIDE.md`
- **Project Authority:** `CLAUDE.md` (Z-roles, governance)
- **Tool Manifest:** `tools-manifest.yaml` (canonical tool registry)
- **CI Workflows:** `.github/workflows/tool-manifest.yml`, etc.

---

## Contact & Escalation

**Questions about PR workflow?** → This guide  
**Questions about Z2 governance?** → `CLAUDE.md`  
**CI gate failures?** → Check `verify_pr_readiness.sh` output, then debug  
**Merge-blocking issues?** → Contact Z2 (Night)
