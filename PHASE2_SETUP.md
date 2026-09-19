# Phase 2: GitHub Actions Automation + Email Alerts + Dashboard

**Status:** ✅ Implementation Complete  
**Delivered:** 3 workflows + email module + HTML dashboard

---

## What's Included

### 1. GitHub Actions Workflows

Three automated workflows are now set up in `.github/workflows/`:

#### Weekly Profile Sync (Monday 09:00 UTC)
- **File:** `weekly-profile-sync.yml`
- **Runs:** Every Monday at 09:00 UTC
- **Does:** Fetches your ORCID profile, extracts research areas, commits updates
- **Output:** `data/research_profile.json`, `data/expertise_map.json`

#### Weekly Funding Rescore (Monday 09:30 UTC)
- **File:** `weekly-funding-rescore.yml`
- **Runs:** Every Monday at 09:30 UTC (after profile sync)
- **Does:** Re-scores all 45 opportunities by your research fit, generates dashboard
- **Output:** `data/ranked_opportunities.json`, `reports/dashboard.html`
- **Bonus:** Sends email digest of top opportunities (if email configured)

#### Daily Deadline Alerts (Daily 08:00 UTC)
- **File:** `daily-deadline-alerts.yml`
- **Runs:** Every day at 08:00 UTC
- **Does:** Checks for opportunities with ≤7 days to deadline, sends urgent alerts
- **Output:** Email notifications (if email configured)

---

### 2. Email Alerts Module

**File:** `src/humanaios_operations/email_alerts.py`

Sends three types of notifications:

**a) Opportunity Digest (Weekly)**
- Email with top 10 opportunities ranked by your fit
- Triggered by weekly-funding-rescore workflow
- Example: "Your Top Funding Opportunities (2026-07-21)"

**b) Deadline Alert (Daily)**
- Urgent alert when opportunity deadline is ≤7 days away
- Triggered by daily-deadline-alerts workflow
- Example: "⏰ Urgent: Longview Grants RFP deadline in 3 days"

**c) Funding Decision (Manual)**
- Notification when you record a funding decision
- Sent when you run `haios apps decide`
- Example: "🎉 Funding Decision: Behavioral Observability Infrastructure..."

---

### 3. HTML Dashboard

**File:** `src/humanaios_operations/dashboard.py`

Auto-generates a responsive HTML dashboard showing:
- **Research Profile:** Name, publication count, research areas
- **Application Pipeline:** Total apps, in progress, funded, success rate
- **Quick Stats:** Top expertise score, expertise domains, avg opportunity fit
- **Top Opportunities:** Your 5 best-fitting opportunities with scores

**Features:**
- ✅ Dark mode support (respects system preference)
- ✅ Responsive design (mobile-friendly)
- ✅ Auto-generated every Monday
- ✅ Links to full opportunities report

**Output:** `reports/dashboard.html`

---

## Setup: Enable Email Alerts

Email alerts are **optional** but recommended. To enable:

### Step 1: Choose Your Email Provider

**Option A: Gmail (Free)**
1. Go to https://myaccount.google.com/apppasswords
2. Create an "App Password" for GitHub Actions
3. Copy the 16-character password

**Option B: SendGrid (Free tier available)**
1. Sign up at sendgrid.com
2. Create an API key
3. Use as SMTP password

**Option C: Custom SMTP**
- Use your own email server
- Have: SMTP host, port, username, password

### Step 2: Add GitHub Secrets

Go to your repository settings → Secrets and variables → Actions → New repository secret

Add these secrets:

| Secret Name | Value | Example |
|-------------|-------|---------|
| `SMTP_HOST` | SMTP server address | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP port (usually 587 or 465) | `587` |
| `SMTP_USER` | Your email address | `carly@example.com` |
| `SMTP_PASS` | App password or API key | `abcd efgh ijkl mnop` |
| `ALERT_EMAIL` | Where to send alerts | `carly@example.com` |
| `FROM_EMAIL` | Sender address (optional) | `humanai os@example.com` |

### Step 3: Test the Workflow

Manually trigger the workflows to test:

```bash
# Via GitHub UI: Actions → Select workflow → Run workflow

# Or via CLI:
gh workflow run weekly-profile-sync.yml
gh workflow run weekly-funding-rescore.yml
gh workflow run daily-deadline-alerts.yml
```

---

## Using the Dashboard

The dashboard is generated automatically every Monday at 09:30 UTC.

To view it locally:

```bash
# Generate dashboard
PYTHONPATH=./src python3 -m humanaios_operations.dashboard

# Open in browser
open reports/dashboard.html
```

To view on GitHub:

1. Go to repository → Actions → Weekly Funding Rescore
2. Check for successful runs
3. Dashboard file is committed to `reports/dashboard.html`

---

## Commands for Phase 2

### Generate Dashboard Manually
```bash
haios dashboard generate
```

### Send Opportunity Digest Email
```bash
# Requires SMTP configured
PYTHONPATH=./src python3 -m humanaios_operations.email_alerts digest
```

### Check for Deadline Alerts
```bash
# Dry-run (don't send emails)
PYTHONPATH=./src python3 -m humanaios_operations.deadline_checker check --dry-run

# Actually send alerts
PYTHONPATH=./src python3 -m humanaios_operations.deadline_checker check
```

---

## Automation Timeline

After setup, your HumanAIOS operations hub will automatically:

**Every Monday at 09:00 UTC:**
- Fetch your ORCID profile
- Extract research areas
- Commit updates to repo

**Every Monday at 09:30 UTC:**
- Re-score all 45 opportunities by fit
- Generate HTML dashboard
- Send you an email digest of top opportunities

**Every Day at 08:00 UTC:**
- Check for opportunities with ≤7 days to deadline
- Send urgent deadline alerts if any found

**On Demand:**
- Track applications as you submit them
- Record funding decisions
- Get email notifications

---

## Integration with Phase 1

Phase 2 builds on Phase 1:

| Phase 1 | Phase 2 |
|---------|---------|
| ResearchProfile (manual) | ResearchProfile (auto weekly) |
| FundingFitScorer (manual) | FundingFitScorer (auto weekly) |
| ApplicationTracker (manual) | ApplicationTracker + notifications |
| CLI dashboard (manual) | HTML dashboard (auto weekly) |
| (No email) | Email alerts (optional) |

---

## Troubleshooting

### Workflows aren't running
- Check GitHub Actions is enabled in repo settings
- Verify CRON schedule times (in UTC)
- Check Actions → Workflows for error logs

### Emails not sending
- Verify SMTP secrets are set correctly
- Check email logs in workflow output
- Ensure email provider allows SMTP access
- Gmail: use App Password, not regular password

### Dashboard not generating
- Check workflow logs for errors
- Verify `ranked_opportunities.json` exists
- Run `haios funding rank` manually first

---

## Next: Phase 3 (Future)

Phase 3 will add:
- Publication-to-proposal suggestion automation
- Funding outcome tracking + learning loops
- Cross-practice visibility (if expanding team)
- Advanced analytics + trend reports

---

## Success Criteria

✅ GitHub Actions workflows trigger on schedule  
✅ Email alerts send when configured  
✅ Dashboard generates and auto-updates weekly  
✅ All automation requires zero manual intervention after setup  

**Phase 2 Status: READY FOR DEPLOYMENT**

---

*To get started: configure GitHub Secrets (5 min), then watch the workflows run automatically every Monday & daily.*
