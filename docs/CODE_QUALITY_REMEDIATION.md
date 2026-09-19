# Code Quality Remediation Workflow

This document outlines the systematic process for identifying, triaging, and remediating SonarCloud code quality issues in the humanaios-ui/operations repository.

## Overview

SonarCloud scans are triggered on:
- Every push to `main` branch
- Every pull request (opened, synchronized, reopened)
- Manual workflow dispatch

**Configuration:** See `sonar-project.properties` for scan settings, exclusions, and quality gates.

## Issue Severity Levels

| Severity | Definition | SLA | Action |
|----------|-----------|-----|--------|
| **BLOCKER** | Security vulnerability, critical bug | ASAP (same day) | Hotfix; blocks merge |
| **CRITICAL** | Major bug/security issue | 1-2 days | Priority fix; code review required |
| **MAJOR** | Important code smell, reliability issue | 1 week | Scheduled fix; include in sprint |
| **MINOR** | Code smell, maintainability issue | 2 weeks | Backlog item; opportunistic fix |
| **INFO** | Convention, style suggestion | No deadline | Nice-to-have; address in refactors |

## Triage Process

### Step 1: Automated Issue Detection
- SonarCloud scan runs automatically on PR/push
- Results appear in PR checks and SonarCloud dashboard
- GitHub Actions workflow reports scan status

### Step 2: Issue Classification
```
BLOCKER (0-5% of issues)
├─ SQL injection vulnerabilities
├─ Authentication bypass
├─ Hardcoded credentials
└─ Unhandled critical exceptions

CRITICAL (5-10%)
├─ Logic bugs affecting core flow
├─ Missing validation
├─ Unsafe data access
└─ Race conditions

MAJOR (20-30%)
├─ Code duplication
├─ High cyclomatic complexity
├─ Missing error handling
└─ Performance issues

MINOR (40-60%)
├─ Naming conventions
├─ Unused variables
├─ Dead code
└─ Style issues

INFO (5-10%)
└─ Documentation, comments
```

### Step 3: Issue Assignment & Tracking

Create GitHub issues using the **Code Quality** issue template:
1. Copy issue details from SonarCloud
2. Link to affected file(s) and line(s)
3. Assign to responsible developer
4. Add label: `code-quality`
5. Add severity label: `blocker`, `critical`, `major`, `minor`
6. Set milestone for target release

### Step 4: Remediation

#### For BLOCKER/CRITICAL Issues (Same Day)
```bash
# 1. Create hotfix branch
git checkout -b fix/sonar-{rule-id}-{description}

# 2. Fix the issue
# (edit the flagged code)

# 3. Verify fix locally
python -m pytest tests/  # if applicable
sonar-scanner           # if local SonarQube available

# 4. Commit with reference
git commit -m "fix(code-quality): resolve {RULE_ID}

- Fixed {issue description}
- Affected files: {list}
- SonarCloud rule: {rule URL}
- Severity: BLOCKER

Closes #{GitHub issue number}

Co-Authored-By: [Your Name] <your.email@example.com>"

# 5. Push and create PR
git push origin fix/sonar-{rule-id}-{description}
# Create PR with link to issue
```

#### For MAJOR Issues (Weekly Sprint)
- Add to sprint backlog
- Schedule for next sprint planning
- Include in regular code review

#### For MINOR Issues (Opportunistic)
- Batch similar issues together
- Include fixes when modifying related code
- Address during refactoring work

### Step 5: Verification

After fix implementation:

1. **Local Verification**
   ```bash
   # Run tests
   pytest tests/ -v
   
   # Run linters
   ruff check .
   black --check .
   ```

2. **PR Review**
   - Code review for correctness
   - SonarCloud re-scan on PR
   - Verify issue is resolved in PR checks

3. **Merge & Confirm**
   - Merge PR to main
   - Confirm SonarCloud scan on main passes
   - Update GitHub issue: mark as closed

## Quality Gates

### Current Thresholds (Configurable in SonarCloud)

```
✓ Reliability Rating: A (< 5 bugs per 1000 LOC)
✓ Security Rating: A (no vulnerabilities)
✓ Maintainability Rating: A (< 3% technical debt ratio)
✓ Coverage: > 70% (for new code)
✓ Duplicates: < 3% (for new code)
```

### PR Blocking Conditions

PRs are blocked if:
- BLOCKER or CRITICAL issue introduced
- Overall code coverage drops > 5%
- Quality gate fails

## Monthly Review

Every 30 days, the team should:

1. **Generate Metrics Report**
   ```bash
   # Export metrics from SonarCloud dashboard
   - Total issues by severity
   - Trends (improving/degrading)
   - Files with most issues
   - Rules with most violations
   ```

2. **Identify Patterns**
   - Which rules trigger most frequently?
   - Are issues concentrated in certain files?
   - What types of bugs are we missing?

3. **Adjust Quality Gates**
   - Tighten gates for improving areas
   - Add custom rules for common mistakes
   - Disable rules that create false positives

4. **Team Calibration**
   - Review sample issues with team
   - Discuss remediation strategies
   - Update linting/formatting tools

## Automation: SonarCloud → GitHub Issues

To automatically create GitHub issues from SonarCloud findings (requires SonarCloud Enterprise or GitHub Actions custom integration):

1. **Option A: SonarCloud Native Integration**
   - Configure GitHub app in SonarCloud
   - Enable "Create GitHub Issues" on quality gates
   - Issues auto-created when rules violation detected

2. **Option B: Custom GitHub Action**
   ```yaml
   # Add to .github/workflows/code-quality-issues.yml
   - name: Create GitHub issues from SonarCloud findings
     uses: custom-action/sonar-to-github-issues@v1
     with:
       sonar_token: ${{ secrets.SONAR_TOKEN }}
       sonar_host: ${{ secrets.SONAR_HOST_URL }}
   ```

## Tools & Commands

### Local SonarQube Scanning (if available)
```bash
# Install sonar-scanner
# See: https://docs.sonarqube.org/latest/analysis/scan/sonarscanner/

# Run scan
sonar-scanner \
  -Dsonar.projectKey=humanaios-ui_operations \
  -Dsonar.sources=. \
  -Dsonar.host.url=https://your-sonarqube-server \
  -Dsonar.login=$SONAR_TOKEN
```

### Python-Specific Tools
```bash
# Pylint
pylint acat/ tools/ --disable=C0111,C0103

# Black (formatter)
black --line-length=100 .

# Ruff (linter)
ruff check . --fix

# MyPy (type checking)
mypy acat/ tools/ --ignore-missing-imports
```

### Code Coverage
```bash
# Generate coverage report
pytest --cov=acat --cov=tools --cov-report=xml

# Upload to SonarCloud (automatic in CI)
```

## Escalation Path

If an issue can't be resolved:

1. **Decision Needed**
   - Add label: `needs-decision`
   - Comment with: what's blocking, options considered
   - Tag code owner for design review

2. **False Positive**
   - Add label: `false-positive`
   - Comment on SonarCloud with details
   - Request rule exception or disable for that file

3. **Architectural Issue**
   - Add label: `architectural`
   - Schedule design discussion
   - Document decision for future reference

## Resources

- **SonarCloud Docs:** https://docs.sonarcloud.io
- **SonarQube Rules:** https://sonarcloud.io/organizations/humanaios-ui/rules
- **Python Best Practices:** PEP 8, PEP 484 (type hints)
- **Security Guidelines:** OWASP Top 10, CWE Top 25

## Questions?

Contact the code quality lead or post in #code-quality Slack channel.
