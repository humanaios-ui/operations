# Branch Protection Rules — Phase 2 Setup

**Effective Date:** 2026-08-08 (Phase 2 deployment)  
**Applies to:** All 10 foundation practices  

---

## GitHub Practices — Automated Setup

For practices with GitHub remotes (humanaios, humanaios-internal, empirica-outreach):

### Rule 1: Governance PR Protection

**Branch:** main  
**Rule Name:** governance-pr-protection

```yaml
required_status_checks:
  strict: true
  contexts:
    - "PR Template Validation"
    - "Z2 Gate Questions Validation"
    - "Decision ID Linkage Check"

required_reviews:
  dismiss_stale_reviews: true
  require_code_owner_review: true
  required_review_count: 1

require_branches_up_to_date: true
require_status_checks_to_pass_before_merging: true

restrictions:
  users: []
  teams: ["z2-authority"]
  apps: []

allow_force_pushes: false
allow_deletions: false
require_linear_history: false

bypass_pull_request_allowances:
  users: []
  teams: []
  apps: []
```

### Rule 2: Mesh Sync PR Auto-Merge

**Branch:** governance-sync/*  
**Rule Name:** mesh-sync-auto-merge

```yaml
# Sync PRs auto-merge after Z2 review (24h SLA)
# No additional review required beyond mesh-support dispatch

auto_merge_enabled: true
auto_merge_method: "squash"

required_reviews:
  dismiss_stale_reviews: false
  require_code_owner_review: false
  required_review_count: 0

require_branches_up_to_date: false
allow_force_pushes: false
```

---

## Local Practices — Manual Enforcement

For local-only practices, enforce governance discipline via:

1. **Git hooks** (pre-commit):
   - Validate PR template format
   - Check decision_id format
   - Verify CONTROLLED_DOCUMENTS.md entries

2. **CI/CD validation** (when workflows available):
   - Run consistency checks on commit
   - Report divergence-detect findings

3. **Mesh-support coordination**:
   - Sync PRs received via mesh-sync-batch
   - Validated locally before merge

---

## Setup Commands

### For GitHub Practices (via GitHub CLI)

```bash
# humanaios
gh repo rules create --repository humanaios-org/humanaios \
  --ruleset governance-pr-protection \
  --branch main \
  --required-reviews 1 \
  --require-code-owner-review

# humanaios-internal
gh repo rules create --repository humanaios-org/humanaios-internal \
  --ruleset governance-pr-protection \
  --branch main \
  --required-reviews 1 \
  --require-code-owner-review

# empirica-outreach
gh repo rules create --repository empirica-foundation/empirica-outreach \
  --ruleset governance-pr-protection \
  --branch main \
  --required-reviews 1 \
  --require-code-owner-review
```

### For Local Practices (via Empirica)

```bash
# Install pre-commit hook for governance validation
empirica hook install governance-validator

# Validate all governance files
empirica validate --governance
```

---

## Validation Checklist

- [ ] GOVERNANCE_PR_TEMPLATE.md pushed to all 10 practices
- [ ] CODEOWNERS configured with Z2 authority review
- [ ] Branch protection rules active on GitHub practices
- [ ] Mesh-sync-batch workflow active (dispatches on governance merge)
- [ ] divergence-detect workflow active (daily 00:00 UTC check)
- [ ] Practice leads trained on governance workflow
- [ ] First test governance PR runs through full workflow
- [ ] All 10 practices confirm readiness for Phase 3

---

## Testing

### Phase 2 Test Governance PR

**Title:** TEST: Z2 Authority Review & Mesh Sync (Phase 2 Validation)

**What to Test:**
1. ✅ PR template validation passes
2. ✅ Z2 gate questions required for approval
3. ✅ CODEOWNERS review triggered for Z2 authority
4. ✅ After merge, mesh-sync-batch dispatches to all 10 practices
5. ✅ divergence-detect runs daily and flags any inconsistencies
6. ✅ All 10 practices receive sync notification

**Success Criteria:**
- PR requires Z2 authority review (governance CODEOWNERS active)
- After approval + merge, mesh-sync-batch triggers (verified in Actions)
- All 10 practices receive dispatch event within 5 minutes
- divergence-detect next run (or manual trigger) shows consistent state

---

## Troubleshooting

**Issue:** CODEOWNERS not triggering review requests

**Fix:** Ensure @carly-r-anderson and @sab-backup are valid GitHub users in the organization.

**Issue:** Mesh-sync-batch dispatch fails for some practices

**Fix:** Verify repository_dispatch webhook exists and has correct permissions. Check GitHub Actions secrets (GITHUB_TOKEN) have write access.

**Issue:** divergence-detect reports HIGH severity divergences

**Fix:** Check GOVERNANCE_RATIFICATIONS_REGISTRY.yaml and AUTHORITY_ASSIGNMENTS.yaml exist in all practices. Run manual consistency validation.

---

## Phase 2 Readiness

Phase 2 deployment complete when:
- ✅ All workflows deployed and tested
- ✅ All practices have governance PR template + CODEOWNERS
- ✅ First test governance PR runs end-to-end successfully
- ✅ All 10 practices confirm readiness for Phase 3 (2026-08-15)
