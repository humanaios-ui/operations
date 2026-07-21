# 🚀 SonarCloud Baseline Scan — Quick Start

**Status:** Ready to execute  
**Duration:** ~60 minutes total  
**Difficulty:** Easy (mostly automated)

---

## BEFORE YOU START (1 minute)

✅ Verify prerequisites:
```bash
# 1. Check GitHub secrets are configured
# Go to: https://github.com/humanaios-ui/operations/settings/secrets/actions
# Should see: SONAR_TOKEN and SONAR_HOST_URL (both must be present)

# 2. Confirm SonarCloud project exists
# Go to: https://sonarcloud.io/organizations/humanaios-ui/projects
# Should see: "operations" project listed
```

**If either is missing:** Stop and configure before proceeding (see troubleshooting in SCAN_EXECUTION_GUIDE.md).

---

## EXECUTE: Run Initial Scan (5 minutes)

### Method 1: GitHub Actions Web UI (Easiest)

```
1. Go to: https://github.com/humanaios-ui/operations/actions
2. Find workflow: "sonarqube-quality"
3. Click on it
4. Click orange "Run workflow" button
5. Branch: main (default)
6. Click "Run workflow" button
7. Workflow will start (~2-4 minutes to complete)
```

### Method 2: Git Push (Alternative)

```bash
cd /Users/andersonfamily/practices/humanaios/operations
git pull origin main
git commit --allow-empty -m "chore: trigger SonarCloud baseline scan"
git push origin main

# Workflow will automatically trigger
# Go to Actions tab to monitor
```

---

## MONITOR: Watch Scan Progress (3 minutes)

```
GitHub Actions tab → sonarqube-quality workflow

Expect to see:
  ✓ Guard — is SonarQube configured? (30 sec)
  ✓ Checkout (10 sec)
  ✓ SonarQube scan (2-4 min)

Look for: Green checkmark ✓ (success) or red X (failure)
```

---

## CAPTURE: Fill Baseline Document (15 minutes)

Once scan completes, open SonarCloud dashboard:

```
https://sonarcloud.io/project/overview?id=humanaios-ui_operations
```

**Copy these numbers into METRICS_BASELINE.md:**

| Section | Where to Find | What to Record |
|---------|---|---|
| **Quality Grades** | Overview page, top section | Reliability, Security, Maintainability grades |
| **Coverage** | Quality profiles or coverage card | XX% (e.g., 45%) |
| **Duplication** | Metrics card | XX% (e.g., 2.5%) |
| **Issues by Severity** | Issues filter or dashboard card | BLOCKER count, CRITICAL count, MAJOR count, etc. |
| **Top Files** | Issues list, sorted by severity | Top 3-5 files with most issues |
| **Language Metrics** | Filter issues by language | Python, JavaScript, etc. metrics |
| **Security** | Security tab | OWASP/CWE findings |

**Command to edit:**
```bash
cd /Users/andersonfamily/practices/humanaios/operations
nano docs/METRICS_BASELINE.md
# Or use your preferred editor
# Replace all [PENDING] with actual values from SonarCloud
```

**Commit the baseline:**
```bash
git add docs/METRICS_BASELINE.md
git commit -m "docs(metrics): capture baseline from initial SonarCloud scan

- BLOCKER issues: [count]
- CRITICAL issues: [count]
- Test coverage: [XX]%
- Duplication: [XX]%

Baseline established 2026-07-21."

git push origin main
```

---

## CREATE: Track BLOCKER Issues (30 minutes)

For each BLOCKER issue found:

```bash
# Create a GitHub issue for each BLOCKER
# Use this template:

gh issue create \
  --title "[Code Quality] BLOCKER: {Rule Name}" \
  --body "## Issue Details
- SonarCloud Rule: {rule name}
- File: {file path}
- Line: {line number}
- Severity: BLOCKER

## Description
{Copy from SonarCloud}

## Remediation Steps
- [ ] Review code
- [ ] Implement fix
- [ ] Run tests
- [ ] Verify in SonarCloud

## SonarCloud Link
https://sonarcloud.io/project/overview?id=humanaios-ui_operations" \
  --label blocker,code-quality \
  --assignee {github-username}
```

**Check dashboard for BLOCKER count:**
```bash
# Quick count
gh issue list --label blocker --label code-quality --state open
```

---

## VERIFY: CI/CD Integration (5 minutes)

**Test that SonarCloud checks work on PRs:**

```bash
# Create test branch
git checkout -b test/sonar-check
git commit --allow-empty -m "test: verify SonarCloud checks"
git push origin test/sonar-check

# Create PR
gh pr create --title "Test: SonarCloud CI Check" \
             --body "Verify SonarCloud status check appears"

# Wait 2-3 minutes, then check PR
# Should see "sonarqube-quality" status check with link to SonarCloud analysis

# Cleanup (after verifying)
gh pr close $(gh pr list --head test/sonar-check --json number -q '.[0].number')
git push origin --delete test/sonar-check
```

---

## SUMMARIZE: Create Remediation Tracking Issue (5 minutes)

```bash
gh issue create \
  --title "Code Quality: Baseline Remediation Sprint 1" \
  --body "## SonarCloud Baseline Established: 2026-07-21

Initial scan complete. See docs/METRICS_BASELINE.md for full metrics.

### BLOCKER Issues: {count}
- [ ] Fix all by 2026-07-28
- GitHub issues created for each

### CRITICAL Issues: {count}
- [ ] Fix 50% by 2026-08-20
- Schedule for sprint planning

### Quality Metrics
- Coverage: {XX}% (target: 70%)
- Duplication: {XX}% (target: <3%)
- Technical Debt: {time}

### Docs
- Baseline: docs/METRICS_BASELINE.md
- Remediation: docs/CODE_QUALITY_REMEDIATION.md
- Scan Guide: docs/SCAN_EXECUTION_GUIDE.md

### Next Steps
1. Review BLOCKER issues (GitHub labels: blocker, code-quality)
2. Assign to developers
3. Target: fix all BLOCKER issues by end of week" \
  --label code-quality \
  --milestone "Sprint 1"
```

---

## Timeline

| Step | Time | Command/Link |
|------|------|---|
| **1. Verify secrets** | 1 min | https://github.com/humanaios-ui/operations/settings/secrets/actions |
| **2. Run scan** | 5 min | GitHub Actions → sonarqube-quality → Run workflow |
| **3. Capture metrics** | 15 min | Edit docs/METRICS_BASELINE.md |
| **4. Commit baseline** | 2 min | `git commit && git push` |
| **5. Create BLOCKER issues** | 20 min | `gh issue create` × {blocker count} |
| **6. Verify CI/CD** | 5 min | Create test PR |
| **7. Summary issue** | 5 min | `gh issue create` for tracking |
| **TOTAL** | ~60 min | ✅ Baseline complete |

---

## ✅ DONE!

After completing all steps above, you'll have:

✅ Initial SonarCloud scan completed  
✅ Baseline metrics captured in docs/METRICS_BASELINE.md  
✅ GitHub issues created for all BLOCKER violations  
✅ CI/CD integration verified (SonarCloud checks appear in PRs)  
✅ Remediation tracking set up  
✅ Team ready to begin fix sprint  

### Next Phase: Remediation
See `docs/CODE_QUALITY_REMEDIATION.md` for how to systematically fix issues by severity.

### Quick Links
- **SonarCloud Dashboard:** https://sonarcloud.io/project/overview?id=humanaios-ui_operations
- **GitHub Repo:** https://github.com/humanaios-ui/operations
- **Baseline Metrics:** docs/METRICS_BASELINE.md (after scan)
- **Remediation Guide:** docs/CODE_QUALITY_REMEDIATION.md
- **Scan Guide:** docs/SCAN_EXECUTION_GUIDE.md

---

**Ready?** Start with Step 1 above! ⬆️
