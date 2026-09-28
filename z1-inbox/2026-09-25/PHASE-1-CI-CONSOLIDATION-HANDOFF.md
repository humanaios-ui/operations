# Z1 Handoff: Phase 1 CI/CD Consolidation

**Date:** 2026-09-25  
**Branch:** `claude/phase-1-ci-consolidation`  
**Z1 Proposer:** Claude Haiku 4.5  
**Destination:** Z2 Ratification (Admiral / Night)  
**Session:** https://claude.ai/code/session_01WwqvhW7fxxsz1BVWhfJv4U

---

## Executive Summary

User request: "Reduce deployment frequency. Consolidate our CI and ensure it maps according to requirements and intention."

**Phase 1 Implementation: COMPLETE**

Path filters added to two high-overhead workflows:
- `quality-baseline.yml` — runs only on code changes (src/, tools/, requirements.txt, etc.)
- `governance-files.yml` — runs on governance changes (.gov-control/**, GOVERNANCE_FILES.md)

Result: Reduces every-PR overhead; maintains critical quality gates; respects Vercel rate limits.

---

## Implementation Details

### Workflows Modified

| Workflow | Change | Impact | Trade-off |
|---|---|---|---|
| `quality-baseline.yml` | Added path filter | Runs only on code changes | None (comprehensive filtering) |
| `governance-files.yml` | Added path filter + documented rationale | Reduces Vercel overhead | May miss file deletions unless `.gov-control/**` touched |

### Quality Filter Paths

```yaml
paths:
  - 'src/**'
  - 'tools/**'
  - 'acat/**'
  - 'tests/**'
  - 'calibration_profiles/**'
  - 'audits/**'
  - 'requirements.txt'
  - 'setup.py'
  - '.github/workflows/quality-baseline.yml'
```

### Root Cause & Fix

**Issue found:** Initial path filter referenced non-existent `pyproject.toml`
**Fix applied:** Corrected to actual dependency files (`requirements.txt`, `setup.py`)
**Verification:** All paths in filter correspond to actual repository structure

---

## Governance

**molt_tier_claimed:** 2  
**Rationale:** Path filter changes modify CI/CD workflow behavior (governance control surface)

**Z2 Review Required:** YES

---

## Verification Status

✅ Path filters reference valid paths only  
✅ YAML syntax valid  
✅ All test files exist  
✅ GitHub checks passing (Security Evidence, Config Audit, Harness Audit)  
🔴 External blocker: Vercel rate limits (account-level, not code-fixable)

---

## Next Steps for Z2

1. Review changes: path filters on two workflows
2. Assess: deployment frequency reduction + trade-off (path filter may miss deletions)
3. Ratify: Sign Z2 hash per REGISTERED.md
4. Authorize: Merge to main once ratified

---

## Why This is Separate from PR #538

PR #538 combines RNOLA governance work (with pre-existing test failures) + Phase 1 CI consolidation.

This new branch isolates **Phase 1 only**, allowing it to:
- Move forward cleanly to Z2 ratification
- Merge independently without RNOLA test blockers
- Directly address user's original request (reduce deployment frequency)

RNOLA work proceeds on its own timeline (PR #538).

---

**Status:** Ready for Z2 ratification  
**Awaiting:** Admiral/Night (Carly R. Anderson) Z2 decision signature
