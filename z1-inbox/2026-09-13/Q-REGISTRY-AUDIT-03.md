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
- # ZONE_REGISTRY — unified authority map for all 31 HumanAIOS repositories
+ # ZONE_REGISTRY — unified authority map for 12 active HumanAIOS repositories
```

**Apply Q-REGISTRY-AUDIT-02 changes:**
- Remove 13 non-existent planned repos (clean up table)
- Add 7 new repos from GitHub (acat-x, acat-dashboard, acat-observatory, docs, empirica-practice-mesh, research, findlocaltattooartists)
- Final count: 12 repos (matching GitHub truth)

**If Q-REGISTRY-AUDIT-01 chooses Option B (Track Planned Separately):**

- Keep ZONE_REGISTRY.md with 12 active repos
- Create PLANNED_REPOS.md with 13 planned + roadmap
- Add cross-references in authority index (CLAUDE.md)

**If Option C (Hybrid):**

- Update header: "Currently 12 repos (31 planned)"
- Create ROADMAP_REPOS.md with status tracking for each planned repo
- Link from ZONE_REGISTRY

---

### Task 2: Update CI Gate (registry_consistency.yml)

**Current gate (implied):**
```yaml
# Check that repos in ZONE_REGISTRY exist on GitHub
falsifier:
  - name: "registry_consistency"
    rule: |
      For each repo in ZONE_REGISTRY.md:
        - EXISTS on humanaios-ui org? YES
        - Claims in header match table row count? YES
```

**New gate (post-reconciliation):**

```yaml
registry_consistency:
  rules:
    - name: "header_vs_table_match"
      assert: |
        ZONE_REGISTRY.md header count ==
        count(active repos in table)
      failure: |
        "Header claims N repos but table lists M"
        
    - name: "all_table_repos_exist_on_github"
      assert: |
        For each repo in ZONE_REGISTRY table:
          gh repo view humanaios-ui/{repo} --json isArchived
          must return isArchived=false
      failure: |
        "Repo {repo} in ZONE_REGISTRY but missing/archived on GitHub"
        
    - name: "no_unregistered_active_repos"
      assert: |
        gh repo list humanaios-ui --json nameWithOwner | count
        <= count(active repos in ZONE_REGISTRY table)
      failure: |
        "GitHub has active repos not in ZONE_REGISTRY"
        
    - name: "planned_repos_tracked"
      if: "PLANNED_REPOS.md or ROADMAP_REPOS.md exists"
      assert: |
        All 13 planned repos from Q-REGISTRY-AUDIT-01
        appear in planned/roadmap file with status
      failure: |
        "Planned repos not tracked in secondary registry"
```

**Deploy gate in:** `.github/workflows/registry_consistency.yml` (runs on PR, gates merge)

---

### Task 3: Update CLAUDE.md Cross-Reference

Add to "Governance Files & CI/CD Integration" table:

```markdown
| ZONE_REGISTRY.md | Z2 ratifies repos | Repo add/remove/claim change | CI: registry_consistency gate |
| PLANNED_REPOS.md (if Option B/C) | Z2 ratifies | Roadmap update | CI: registry_consistency gate |
```

Update "Session Rituals (§A)" to include:

```markdown
3. Read `ZONE_REGISTRY.md` at that SHA (pin repo list)
   - Verify header count matches table rows
   - For active work: confirm your repo is registered
```

---

## Falsifier

**Success Criteria:**
- [ ] Header claim matches GitHub reality (±0 discrepancy)
- [ ] All 12 active repos registered in ZONE_REGISTRY
- [ ] All 13 planned repos tracked (if Option B/C)
- [ ] CI gate registry_consistency passes on main
- [ ] No PR merges without gate passing

**Failure Criteria:**
- [ ] Header still claims 31 (unresolved)
- [ ] Missing repos remain untracked
- [ ] CI gate not deployed
- [ ] Gap persists for next audit

---

## Estimated Effort

- ZONE_REGISTRY.md edit: 10 min
- .github/workflows/registry_consistency.yml: 20 min
- CLAUDE.md update: 5 min
- Testing gate locally: 15 min
- **Total: ~50 min**

---

## Rollout Plan

1. **Phase 1** → Z2 ratifies Q-REGISTRY-AUDIT-01 (Option chosen)
2. **Phase 2** → Z2 ratifies Q-REGISTRY-AUDIT-02 (7 new repos approved)
3. **Phase 3** → Z1 implements Q-REGISTRY-AUDIT-03 (this task):
   - Apply ZONE_REGISTRY edits
   - Deploy CI gate
   - Test locally (all repos resolve, header matches)
   - Push to branch
4. **Phase 4** → Z2 ratifies PR for Q-REGISTRY-AUDIT-03 with Z2 hash
5. **Phase 5** → CI gate passes, PR merges to main
6. **Phase 6** → Future audits run against new gate (preventive)

---

## Handoff Block

Once merged:
- `ZONE_REGISTRY.md` is now SOT for active repos (12)
- Header truthful and CI-enforced
- 13 planned repos tracked separately (if Option B/C)
- Next audit: Re-run registry_consistency on all 31-repo ecosystem (other orgs, etc.)

---

**Proposed Z2 Decision Window:** 48h (sequential after Q-REGISTRY-AUDIT-01 + -02)  
**Associated:** IC-REGISTRY-003 (implementation + gate deployment)
