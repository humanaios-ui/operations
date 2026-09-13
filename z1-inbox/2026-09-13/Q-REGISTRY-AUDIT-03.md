# Q-REGISTRY-AUDIT-03: ZONE_REGISTRY.md Final Reconciliation & CI Integration

**Type:** F (Finding/Implementation)  
**Date:** 2026-09-13  
**Author:** Z1 (Claude)  
**Status:** Awaiting Z2 Ratification (blocked on Q-REGISTRY-AUDIT-01 + Q-REGISTRY-AUDIT-02)  
**Depends On:** Q-REGISTRY-AUDIT-01 decision (Option A/B/C), Q-REGISTRY-AUDIT-02 approval  

---

## Problem Statement

After Q-REGISTRY-AUDIT-01 and Q-REGISTRY-AUDIT-02 are ratified, **implement chosen reconciliation** and update CI gates to prevent future drift.

---

## Implementation Path (3 Sub-Tasks)

### Task 1: Update ZONE_REGISTRY.md

**If Q-REGISTRY-AUDIT-01 chooses Option A (Correct Header):**

```diff
- ## Repository Zone Assignments (31 repos)
+ ## Repository Zone Assignments (12 repos)
```

Then:
- Remove 13 non-existent planned repos from table (empirica-autonomy, empirica-foundation-evaluator, etc.)
- Add 7 new repos from Q-REGISTRY-AUDIT-02 (acat-x, acat-dashboard, acat-observatory, docs, empirica-practice-mesh, research, findlocaltattooartists) using full 7-column schema
- Update Tier organization if needed to accommodate new repos
- Final count: 12 repos (matching GitHub truth)

**If Q-REGISTRY-AUDIT-01 chooses Option B (Track Planned Separately):**

- Keep ZONE_REGISTRY.md section heading as "## Repository Zone Assignments (12 active repos)"
- Remove 13 non-existent repos from ZONE_REGISTRY table
- Add 7 new repos from Q-REGISTRY-AUDIT-02 (same 7-column schema)
- Create PLANNED_REPOS.md with 13 planned repos + 6 unaccounted repos (see Q-REGISTRY-AUDIT-01 "Universe Closure" section) with status column: `| Repo | Status | Note | Z2 Authority |`
  - Status values: PLANNED, ARCHIVED, RETIRED, OTHER_ORG, UNKNOWN
- Add cross-reference in CLAUDE.md: "For roadmap repos, see PLANNED_REPOS.md"
- Update ZONE_REGISTRY.md file listing in CI gates (see Task 2)

**If Option C (Hybrid):**

- Update section heading: `## Repository Zone Assignments (12 active repos, 31 planned)`
- Keep ZONE_REGISTRY.md with 12 active repos only (same as Option B)
- Create ROADMAP_REPOS.md with all 31 planned/aspirational repos (13 missing from audit + 6 unaccounted + 12 active = 31)
  - Schema: `| Repo | Status | Z2 Authority | Notes | Roadmap Phase |`
  - Status values: ACTIVE, PLANNED, ARCHIVED, RETIRED, OTHER_ORG, UNKNOWN
- Link from ZONE_REGISTRY to ROADMAP_REPOS.md
- Update authority index in CLAUDE.md with both ZONE_REGISTRY and ROADMAP_REPOS governance rules

---

### Task 2: Update CI Gate (registry_consistency.yml)

**Specification (pre-implementation):**

```yaml
registry_consistency:
  # This gate ensures ZONE_REGISTRY.md header count matches table reality
  # and that GitHub has no unregistered active repos.
  
  rules:
    - id: "header_vs_table_match"
      name: "ZONE_REGISTRY section heading count matches table rows"
      implementation: |
        REGEX: Extract N from `## Repository Zone Assignments (N repos|N active repos.*)`
        PARSE: Read ZONE_REGISTRY.md table (exclude placeholder rows like "[Other archived repos]")
        COUNT: Sum non-placeholder rows in all tiers
        ASSERT: N == COUNT
        
    - id: "all_table_repos_exist_on_github"
      name: "All ZONE_REGISTRY repos exist and are not archived on GitHub"
      scope: "humanaios-ui org only"
      implementation: |
        For each repo row in ZONE_REGISTRY table (skip "[Other archived repos]" placeholder):
          IF repo contains "archive" in name:
            SKIP (archives are expected to be present or archived)
          ELSE:
            CALL: gh repo view humanaios-ui/{repo} --json isArchived,isPrivate
            ASSERT: isArchived=false OR (isPrivate=true AND has_credentials)
        NOTE: acat-observatory is private. Verify via GitHub API with org credentials (GitHub Actions secret).
        
    - id: "no_unregistered_active_repos"
      name: "GitHub has no active repos outside ZONE_REGISTRY"
      scope: "humanaios-ui org"
      implementation: |
        CALL: gh repo list humanaios-ui --json nameWithOwner,isArchived
        FILTER: WHERE isArchived=false (active repos only)
        PARSE: Extract repo names; compare against ZONE_REGISTRY table
        FOR each GitHub active repo:
          IF NOT in ZONE_REGISTRY table:
            FAIL with list of unregistered repos
            
    - id: "planned_repos_tracked" 
      name: "All planned/roadmap repos tracked in secondary file"
      condition: "IF PLANNED_REPOS.md OR ROADMAP_REPOS.md exists"
      implementation: |
        GET: List of 13 planned repos from Q-REGISTRY-AUDIT-01 classification
        GET: List of 6 unaccounted repos from Q-REGISTRY-AUDIT-01 "Universe Closure"
        PARSE: Secondary file (PLANNED_REPOS.md or ROADMAP_REPOS.md)
        FOR each of 13 planned + 6 unaccounted = 19 repos:
          ASSERT: repo appears in secondary file with status column
          ASSERT: status in [PLANNED, ARCHIVED, RETIRED, OTHER_ORG, UNKNOWN]
```

**Deploy gate in:** `.github/workflows/registry_consistency.yml`
- Trigger: on push to main, on every PR to main (blocking merge)
- Requires: GitHub Actions secrets for private repo access (GITHUB_TOKEN with org read access)
- Branch protection rule: Add `registry_consistency` as required check

**Post-deployment checklist:**
- [ ] Test locally with `gh workflow run registry_consistency.yml --ref main`
- [ ] Verify gate passes on current main branch
- [ ] Add `registry_consistency` to branch protection rules for main
- [ ] Document gate in `.github/GOVERNANCE.md` or similar CI documentation

---

### Task 3: Update CLAUDE.md Cross-Reference

**A. Add new row to "Governance Files & CI/CD Integration" table:**

If Option A (header correction only):
```markdown
| ZONE_REGISTRY.md | Z2 ratifies repos | Repo add/remove/count change | CI: registry_consistency gate |
```

If Option B (separate PLANNED_REPOS.md):
```markdown
| ZONE_REGISTRY.md | Z2 ratifies active repos | Repo add/remove/count change | CI: registry_consistency gate |
| PLANNED_REPOS.md | Z2 ratifies roadmap | Planned repo add/status change | CI: registry_consistency gate |
```

If Option C (hybrid ROADMAP_REPOS.md):
```markdown
| ZONE_REGISTRY.md | Z2 ratifies active repos | Active repo add/remove/count change | CI: registry_consistency gate |
| ROADMAP_REPOS.md | Z2 ratifies roadmap | Planned/archived repo status change | CI: registry_consistency gate |
```

**B. Update "Session Rituals (§A)" — ADD as new numbered item (not replacing existing item 3):**

```markdown
4. Read `ZONE_REGISTRY.md` at that SHA (pin repo list)
   - Verify section heading count matches active repo rows
   - Confirm your repo is registered if this is active work
   - If Option B/C: Check PLANNED_REPOS.md or ROADMAP_REPOS.md for roadmap context
```

**C. Update authority rules section (if Option B/C chosen):**

Add to "Z2 Ratifier (Night) — Serial Gate" subsection:

```markdown
**Registry governance:**
- ZONE_REGISTRY.md is SOT for active repos (required Z2 hash)
- PLANNED_REPOS.md or ROADMAP_REPOS.md tracks planned/aspirational repos (required Z2 hash if edited)
- CI gate `registry_consistency` enforces header count vs table match on both files
```

---

## Implementation Details & Edge Cases

**Private Repo Handling (acat-observatory):**
- acat-observatory is marked PRIVATE on GitHub
- CI gate must use GitHub Actions GITHUB_TOKEN (org-scoped) to verify private repos
- If credentials unavailable: gate should skip private repos with logged warning, not fail
- Z3 executor must verify private repo manually before accepting gate bypass

**Placeholder Row Handling (`[Other archived repos]`):**
- Current ZONE_REGISTRY has placeholder row: `| [Other archived repos] | Z0 | — | None (read-only) | Night | None | N/A |`
- This is not a real repo name; CI gate must parse and skip placeholder rows
- Regex to detect placeholders: rows with square brackets `[...]` or containing `archive` in Primary column
- If placeholders are removed post-implementation, gate must still pass (no hard dependency)

**Option C File Naming:**
- If Option C chosen: create ROADMAP_REPOS.md (not PLANNED_REPOS.md)
- Schema for ROADMAP_REPOS.md: `| Repo | Status | Z2 Authority | Notes | Roadmap Phase |`
- All 31 planned/aspirational repos (12 active + 13 classified + 6 unaccounted) enumerated with status

---

## Falsifier

**Success Criteria (all must pass):**
- [ ] Section heading count matches table row count (no placeholder rows counted)
- [ ] All repos in ZONE_REGISTRY table exist on GitHub (or are expected archives)
- [ ] acat-observatory verified as private (not broken link); CI gate handles credentials
- [ ] No active GitHub repos outside ZONE_REGISTRY table
- [ ] 13 planned repos + 6 unaccounted repos tracked in secondary file (if Option B/C)
- [ ] CI gate registry_consistency passes on main before merge
- [ ] All PRs blocked until gate passes (branch protection rule active)

**Failure Criteria (any one blocks merging):**
- [ ] Header count doesn't match table rows (Section heading claims N, table has M)
- [ ] Repo in ZONE_REGISTRY doesn't exist on GitHub (broken link)
- [ ] GitHub has unregistered active repos (drift detected)
- [ ] Planned/roadmap file missing or incomplete (if Option B/C)
- [ ] CI gate not deployed or not enforced on main
- [ ] Placeholder rows causing gate parse errors

---

## Estimated Effort

- ZONE_REGISTRY.md edit (remove 13 rows, add 7 rows, rename section heading): 15 min
- PLANNED_REPOS.md or ROADMAP_REPOS.md creation (if Option B/C): 10 min
- .github/workflows/registry_consistency.yml workflow implementation: 30 min
  - Header/table parsing logic: 10 min
  - GitHub API integration (with private repo handling): 10 min
  - Placeholder row detection and skipping: 5 min
  - Error reporting and logging: 5 min
- Branch protection rule configuration: 5 min
- CLAUDE.md update: 5 min
- Testing gate locally: 20 min
  - Test with current main branch
  - Test gate failure scenarios (add/remove repos, edit header, etc.)
  - Verify private repo handling
- **Total: ~80–90 min** (increased complexity from placeholder/private repo handling)

---

## Rollout Plan (Sequential Dependency Chain)

1. **Phase 1: Z2 Decision on Option A/B/C**
   - Z2 reads Q-REGISTRY-AUDIT-01 "Universe Closure" section (enumerates 6 unaccounted repos)
   - Z2 selects: Option A (correct header to 12), Option B (separate PLANNED_REPOS.md), or Option C (hybrid ROADMAP_REPOS.md)
   - Z2 signs ratification hash for Q-REGISTRY-AUDIT-01

2. **Phase 2: Z2 Approval of Zone Assignments**
   - Z2 reviews 7 new repo zone assignments in Q-REGISTRY-AUDIT-02
   - Z2 verifies assignments align with FRAMEWORK_MAPPING.md (verify acat-x→empirica-autonomy valid, etc.)
   - Z2 signs ratification hash for Q-REGISTRY-AUDIT-02

3. **Phase 3: Z1 Implements Reconciliation (Q-REGISTRY-AUDIT-03)**
   - Based on Option A/B/C decision from Phase 1:
     - **If Option A:** ZONE_REGISTRY.md section heading "12 repos", remove 13 missing rows, add 7 new rows
     - **If Option B:** ZONE_REGISTRY.md "12 active repos", create PLANNED_REPOS.md with 13+6=19 planned repos
     - **If Option C:** ZONE_REGISTRY.md "12 active repos (31 planned)", create ROADMAP_REPOS.md with all 31
   - Create .github/workflows/registry_consistency.yml with full implementation (header/table parsing, private repo handling, placeholder detection)
   - Update CLAUDE.md governance table and Session Rituals
   - Test locally (gate passes on main, gate fails when header/table mismatch introduced, etc.)
   - Push to branch `claude/funny-bohr-fp0rnl`

4. **Phase 4: Z2 Ratifies Implementation PR**
   - Z2 reviews PR with all changes from Phase 3
   - Z2 verifies gate specifications match Option A/B/C decision
   - Z2 signs ratification hash for Q-REGISTRY-AUDIT-03 PR

5. **Phase 5: CI Gate Passes, PR Merges**
   - CI gate `registry_consistency` passes on PR
   - All other gates pass (falsifier_lint, CODEOWNERS, etc.)
   - PR merges to main

6. **Phase 6: Branch Protection Enforcement**
   - Add `registry_consistency` to main branch protection rules (required check)
   - Future PRs to main blocked until registry gate passes

7. **Phase 7: Audit & Prevention**
   - Confirm gate blocks unregistered repos (test with temporary test-repo)
   - Confirm gate requires header/table match
   - Document in z1-inbox/2026-09-13/Z2_RATIFICATION_SUMMARY.md (Z2 writes this)

---

## Handoff Block

**End State (post-merge to main):**

| State | Value | Authority |
|-------|-------|-----------|
| Active repos on GitHub (truth) | 12 | GitHub reality |
| ZONE_REGISTRY.md active repos | 12 | Z2 ratified |
| Section heading count claim | 12 | ZONE_REGISTRY header |
| Planned repos tracked | 13 or 31 (depending on Option B/C) | PLANNED_REPOS.md or ROADMAP_REPOS.md (if created) |
| CI gate status | Deployed & enforced | registry_consistency.yml on main |
| Header/table match | Guaranteed by gate | CI blocks merge if mismatch |
| Future unregistered repos | Detected immediately | gate blocks merge |
| Private repos (acat-observatory) | Verified via credentials | GitHub Actions GITHUB_TOKEN |

**Success Outcome:**
- ZONE_REGISTRY.md is SOT for active repos (truthful, CI-enforced)
- Planned/aspirational repos tracked separately (if Option B/C chosen)
- CI gate prevents future drift (claim/tree mismatch will be caught)
- All 25+ identified repos accounted for; 6 unaccounted repos explicitly documented

**Next Steps for Governance:**
1. Z2 re-audits other HumanAIOS orgs (not humanaios-ui) to enumerate remaining 6 repos if needed
2. Z2 updates FRAMEWORK_MAPPING.md to reflect new repo zone assignments
3. Z3 executors assigned to new repos (TBD delegation)
4. Quarterly audits scheduled to verify gate effectiveness

---

**Proposed Z2 Decision Window:** 48h sequential (Phase 1: -01 decision, Phase 2: -02 approval, Phase 3+4: -03 implementation+ratification)

**Associated:** Q-REGISTRY-AUDIT-01, Q-REGISTRY-AUDIT-02, Q-REGISTRY-AUDIT-03 (complete trilogy, all must be ratified together)
