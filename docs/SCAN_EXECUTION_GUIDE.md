# SonarCloud Baseline Scan Execution Guide

This guide walks through running the initial SonarCloud scan and capturing baseline metrics.

## Prerequisites

- ✅ GitHub repository access (humanaios-ui/operations)
- ✅ GitHub Actions enabled
- ✅ SONAR_TOKEN secret configured in GitHub
- ✅ SONAR_HOST_URL secret configured in GitHub
- ⏳ SonarCloud project created for humanaios-ui_operations

## Step-by-Step: Running the Initial Scan

### Step 1: Verify Secrets Are Configured (2 minutes)

**Location:** GitHub → Settings → Secrets and variables → Actions

**Check for:**
```
✓ SONAR_TOKEN      (should be present)
✓ SONAR_HOST_URL   (should be present, typically https://sonarcloud.io)
```

**If secrets are missing:**
1. Go to SonarCloud → Security → Tokens
2. Generate new token (if needed)
3. Copy token value
4. Go to GitHub repo → Settings → Secrets → New repository secret
5. Add `SONAR_TOKEN` with the token value
6. Add `SONAR_HOST_URL` with `https://sonarcloud.io`

### Step 2: Trigger Initial Scan (Automated via GitHub Actions)

**Option A: Trigger via Web UI (Recommended)**

1. Go to GitHub repo → Actions
2. Find workflow: "sonarqube-quality"
3. Click on it
4. Click "Run workflow"
5. Select branch: `main`
6. Click "Run workflow" button
7. Wait for workflow to complete (~3-5 minutes)

**Option B: Trigger via Git Push**

```bash
# Make a small change to trigger the workflow
cd /Users/andersonfamily/practices/humanaios/operations
git pull origin main
echo "# Baseline scan trigger" >> README.md
git add README.md
git commit -m "chore: trigger SonarCloud baseline scan"
git push origin main
```

The workflow will automatically trigger on push to main.

### Step 3: Monitor Scan Progress (5 minutes)

**In GitHub:**
1. Go to Actions tab
2. Click on the running "sonarqube-quality" workflow
3. Watch "sonar" job progress
4. Wait for green checkmark (✓ passed) or red X (✗ failed)

**What to expect:**
```
✓ Guard — is SonarQube configured?     (30 seconds)
✓ Checkout                              (10 seconds)
✓ SonarQube scan                         (2-4 minutes)
```

**If scan fails:**
- Check workflow logs for error messages
- Verify SONAR_TOKEN and SONAR_HOST_URL are correct
- Confirm SonarCloud project key matches `sonar.projectKey` in `sonar-project.properties`

### Step 4: View Scan Results (2 minutes)

**In SonarCloud Dashboard:**

1. Go to https://sonarcloud.io/organizations/humanaios-ui/projects
2. Click on "operations" project
3. View overview page showing:
   - Quality grade (A/B/C/D/E)
   - Issue counts by severity
   - Coverage percentage
   - Duplication percentage

**Bookmark this URL:**
```
https://sonarcloud.io/project/overview?id=humanaios-ui_operations
```

You'll reference it frequently for metrics.

### Step 5: Capture Baseline Metrics (15 minutes)

**From SonarCloud Dashboard, fill in METRICS_BASELINE.md:**

#### 5a. Overall Quality Grades
```
Look at: Project Overview → Quality Profiles section

Record in METRICS_BASELINE.md:
- Reliability: A/B/C/D/E
- Security: A/B/C/D/E  
- Maintainability: A/B/C/D/E
- Coverage: XX%
- Duplicates: XX%
```

#### 5b. Issue Counts by Severity
```
Look at: Issues filter → Issues list (or dashboard card)

Count by severity and record:
- BLOCKER: [count]
- CRITICAL: [count]
- MAJOR: [count]
- MINOR: [count]
- INFO: [count]
```

#### 5c. Top Issues by File
```
Look at: Issues filter → Order by "Most issues" or "Severity"

Record top 3-5 files:
File name | Issue count | Top rule
─────────────────────────────────
[file]    | [count]     | [rule]
```

#### 5d. Language-Specific Metrics
```
Look at: Issues filter → Filter by language (Python, JavaScript, etc.)

For each language, record:
- Lines of Code
- Issue count (and breakdown by severity)
- Coverage %
- Duplication %
```

#### 5e. Security Assessment
```
Look at: Security Hotspots and Security tab

Record:
- OWASP Top 10 issues found
- CWE vulnerabilities
- Hotspots (review priority items)
```

### Step 6: Document the Baseline

**Edit METRICS_BASELINE.md:**

```bash
cd /Users/andersonfamily/practices/humanaios/operations

# Open in editor and replace all [PENDING] with actual values
# Key sections to update:
# - Overall Quality Metrics (section 2)
# - Issue Summary by Severity (section 3)
# - Top Issues by File (section 4)
# - Language-Specific Metrics (section 5)
# - Security Assessment (section 7)
```

**Commit the baseline:**

```bash
git add docs/METRICS_BASELINE.md
git commit -m "docs(metrics): capture baseline from initial SonarCloud scan

- Total issues: [count]
- BLOCKER issues: [count]
- CRITICAL issues: [count]
- Test coverage: [XX]%
- Duplication: [XX]%
- Top issue areas: [list files]

Baseline established on 2026-07-21 for quarterly tracking.

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"

git push origin main
```

### Step 7: Create Issue Tracking Project (10 minutes)

**Option A: GitHub Project Board**

1. Go to repo → Projects → New project
2. Name: "Code Quality Remediation"
3. Description: "Track SonarCloud findings by severity and sprint"
4. Create 5 columns:
   - BLOCKER (fix immediately)
   - CRITICAL (this sprint)
   - MAJOR (next sprint)
   - MINOR (backlog)
   - DONE
5. Manually create issues for BLOCKER/CRITICAL items

**Option B: Use GitHub Issues Labels + Filter**

Create issue labels:
```bash
gh label create blocker -c FF0000 -d "SonarCloud BLOCKER - fix immediately"
gh label create critical -c FFA500 -d "SonarCloud CRITICAL - high priority"
gh label create code-quality -c 0366D6 -d "Code quality issue from SonarCloud"
```

Filter issues:
```
https://github.com/humanaios-ui/operations/issues?q=label%3Acode-quality%2Cblocker
```

### Step 8: Create Initial Issues for High-Severity Items (30 minutes)

For each BLOCKER issue from the scan:

```bash
gh issue create \
  --title "[Code Quality] BLOCKER: {Rule Name} in {File}" \
  --body "SonarCloud Rule: {rule ID}
Severity: BLOCKER
File: {file path}
Line: {line number}

Issue: {description from SonarCloud}

**SonarCloud Link:** {link to issue}

## Remediation
- [ ] Code review
- [ ] Fix implementation  
- [ ] Tests pass
- [ ] SonarCloud re-scan verification" \
  --label blocker,code-quality \
  --assignee {developer-github-handle}
```

### Step 9: Verify CI/CD Integration (5 minutes)

**Create a test PR to verify SonarCloud checks:**

```bash
# Create test branch
git checkout -b test/sonar-verification
git commit --allow-empty -m "test: verify SonarCloud CI/CD integration"
git push origin test/sonar-verification

# Create PR via GitHub web UI or:
gh pr create --title "Test: SonarCloud CI/CD Integration" \
             --body "Verify SonarCloud status checks appear in PRs"

# Wait 2-3 minutes for scan
# Should see "sonarqube-quality" check in PR
# Can also see link to SonarCloud analysis

# After verification, close PR
gh pr close --comment "SonarCloud CI/CD verified - closing test PR"
git push origin --delete test/sonar-verification
```

### Step 10: Document Next Steps (5 minutes)

**Create a GitHub issue to track baseline remediation:**

```bash
gh issue create \
  --title "Code Quality: SonarCloud Baseline Remediation (Sprint 1)" \
  --body "## Baseline Established: 2026-07-21

Initial SonarCloud scan complete. Baseline metrics captured in docs/METRICS_BASELINE.md

### BLOCKER Issues: {count}
- [ ] Fix all BLOCKER issues (due 2026-07-28)
- [ ] Create GitHub issues for each
- [ ] Assign to developers

### CRITICAL Issues: {count}
- [ ] Fix 50% of CRITICAL issues (due 2026-08-20)
- [ ] Schedule for sprint planning

### MAJOR/MINOR Issues: {count}
- [ ] Categorize by file/rule
- [ ] Add to backlog for future sprints

### Metrics to Track
- Coverage: {XX}% (target: 70%)
- Duplication: {XX}% (target: <3%)
- Technical Debt: {time} (target: <5%)

### References
- Baseline: docs/METRICS_BASELINE.md
- Remediation Guide: docs/CODE_QUALITY_REMEDIATION.md
- SonarCloud: https://sonarcloud.io/project/overview?id=humanaios-ui_operations" \
  --label code-quality \
  --milestone "Sprint 1 (Code Quality)"
```

---

## Troubleshooting

### Scan Doesn't Run

**Error: "SonarQube layer dormant. Add SONAR_TOKEN + SONAR_HOST_URL secrets"**

→ Check GitHub Secrets (Settings → Secrets and variables → Actions)
→ Both secrets must be present

### Scan Fails with Auth Error

**Error: "Unauthorized" or "401"**

→ SONAR_TOKEN may be invalid or expired
→ Generate new token in SonarCloud
→ Update GitHub secret with new token

### Scan Completes but No Results in Dashboard

**Issue: Scan runs but SonarCloud dashboard is empty**

→ Verify project key in `sonar-project.properties` matches SonarCloud
→ Check SonarCloud project settings → Administration → Project key
→ Should be: `humanaios-ui_operations`

### Coverage Shows 0%

**Issue: Coverage percentage not appearing**

→ Coverage reports (pytest/coverage) not being generated
→ Uncomment `sonar.python.coverage.reportPaths` in `sonar-project.properties` if coverage.xml exists
→ Run `pytest --cov=acat --cov=tools --cov-report=xml` locally first

---

## Command Reference

```bash
# View latest scan status
gh workflow view sonarqube-quality --shell

# Run workflow manually
gh workflow run sonarqube-quality --ref main

# View workflow runs
gh run list --workflow=sonarqube-quality.yml --limit 5

# View latest run details
gh run view $(gh run list --workflow=sonarqube-quality.yml --limit 1 --json databaseId -q '.[0].databaseId') --log

# Create code quality issue
gh issue create --template code-quality.md

# View all code quality issues
gh issue list --label code-quality --state open
```

---

## Timeline

| Step | Time | Status |
|------|------|--------|
| Verify secrets | 2 min | [Pending] |
| Run initial scan | 5 min | [Pending] |
| Capture metrics | 15 min | [Pending] |
| Create issues | 30 min | [Pending] |
| Verify CI/CD | 5 min | [Pending] |
| **Total** | **~60 min** | [Pending] |

---

## Next: Remediation

Once baseline is established:

1. ✅ Fix all BLOCKER issues (due: 2026-07-28)
2. ✅ Fix 50% CRITICAL (due: 2026-08-20)
3. ✅ Reduce MAJOR by 25% (due: 2026-09-20)

See `docs/CODE_QUALITY_REMEDIATION.md` for the full remediation workflow.

---

**Questions?** Check the FAQ or contact the code quality lead.
