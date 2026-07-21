# Deployment & Launch Guide

Complete guide for deploying HumanAIOS Operations Phase 2 to GitHub Actions.

## Pre-Deployment Checklist

### Code & Commits
- ✅ All code committed to `main` branch
- ✅ Integration tests passing
- ✅ No uncommitted changes

### Workflows
- ✅ 3 workflows defined in `.github/workflows/`
  - `weekly-profile-sync.yml` — Monday 09:00 UTC
  - `weekly-funding-rescore.yml` — Monday 09:30 UTC
  - `daily-deadline-alerts.yml` — Daily 08:00 UTC
- ✅ All workflows use `humanaios_operations.cli`
- ✅ PYTHONPATH configured correctly
- ✅ Python 3.11 specified

### Secrets Configuration
- ✅ GitHub Secrets configured (optional for testing)
  - `SMTP_HOST`
  - `SMTP_PORT`
  - `SMTP_USER`
  - `SMTP_PASS`
  - `ALERT_EMAIL`
- ⚠️  Can be skipped initially (workflows gracefully degrade)

### Documentation
- ✅ GitHub Secrets setup guide created
- ✅ Integration tests documented
- ✅ CLI commands tested and verified

## Launch Steps

### Phase 1: Enable Workflows (Immediate)

1. **Verify workflows are committed:**
   ```bash
   git log --oneline | head -5
   ```

2. **Go to GitHub Actions:**
   - Navigate to: `humanaios-ui/operations`
   - Click **Actions** tab
   - Verify 3 workflows appear in the list

3. **Enable Actions (if not already enabled):**
   - Click **Settings** → **Actions** → **General**
   - Ensure "Allow all actions and reusable workflows" is selected

4. **Verify workflow files:**
   - All 3 workflows should show status: Ready (green checkmark)

### Phase 2: Test Run (Before Full Deployment)

1. **Manual trigger of Profile Sync:**
   - Go to **Actions**
   - Click **Weekly Profile Sync**
   - Click **Run workflow** → **Run workflow**
   - Wait for completion (~30 seconds)
   - Check logs for successful output

2. **Verify data files created:**
   - Check that workflow created:
     - `data/research_profile.json` ✅

3. **Repeat for other workflows:**
   - Run **Weekly Funding Rescore** manually
   - Verify `reports/dashboard.html` created
   - Run **Daily Deadline Alerts** manually
   - Verify no errors

### Phase 3: Configure Secrets (Optional for Email)

1. **Go to GitHub Settings:**
   - **Settings** → **Secrets and variables** → **Actions**

2. **Add 5 repository secrets:**
   - See `docs/GITHUB_SECRETS_SETUP.md` for detailed instructions

3. **Test email configuration:**
   - Run **Weekly Funding Rescore** manually
   - Check logs for email send status
   - Should see either:
     - ✅ "Email sent via SMTP: ..."
     - ⚠️  "Email not configured. Skipping email send."

### Phase 4: Automated Schedule Activation

Once you're confident with manual runs, scheduled automation takes over:

- **Monday 09:00 UTC** — Profile syncs automatically
- **Monday 09:30 UTC** — Opportunities rescore + dashboard + email
- **Daily 08:00 UTC** — Deadline alerts check + email

**No additional action needed.** Workflows run on schedule.

## Monitoring & Maintenance

### Check Workflow Status
```
Actions tab → Select workflow → View runs
```

### Troubleshooting Failed Runs

If a workflow fails:

1. **Click the failed run**
2. **Review logs** for specific error
3. **Common issues:**
   - Missing `requests` dependency → Add to pip install
   - ORCID API timeout → Retry automatically handles
   - SMTP error → Check secrets and SMTP server
   - Git commit failure → Check branch protection settings

### Manual Test Commands

Test locally before assuming GitHub Actions failure:

```bash
# Profile sync
PYTHONPATH=./src python3 -m humanaios_operations.cli profile sync --verbose

# Funding rescore
PYTHONPATH=./src python3 -m humanaios_operations.cli funding rank --markdown data/ranked_opportunities.md

# Dashboard generation
PYTHONPATH=./src python3 -m humanaios_operations.cli dashboard generate

# Deadline check
PYTHONPATH=./src python3 -m humanaios_operations.cli deadline_checker check

# Email test
PYTHONPATH=./src python3 -m humanaios_operations.cli email_alerts test

# Send digest (requires SMTP configured)
PYTHONPATH=./src python3 -m humanaios_operations.cli email_alerts digest
```

## Rollback Plan

If issues occur post-deployment:

### Option 1: Disable Workflows (Keep code)
```
Actions → Select workflow → ... menu → Disable workflow
```
Workflows won't run, but code remains in repo.

### Option 2: Disable via GitHub Settings
```
Settings → Actions → General → Disable all workflows
```
All automation paused, can re-enable with one click.

### Option 3: Revert Code Changes
```bash
git revert HEAD~2  # Revert to before Phase 2
git push
```
Removes all workflow changes.

## Success Metrics

After deployment, verify:

### Automated Data Files
- ✅ `data/research_profile.json` updated Monday
- ✅ `data/ranked_opportunities.json` updated Monday
- ✅ `reports/dashboard.html` updated Monday
- ✅ Files are automatically committed

### Email Alerts (if configured)
- ✅ Digest email received Monday 09:30 UTC
- ✅ Deadline alerts received daily 08:00 UTC
- ✅ Emails contain current data

### Git History
- ✅ Automated commits visible in `git log`
- ✅ Commit messages: "chore: auto-update ..."

### No Alert Emails from GitHub
- ✅ No "Action failed" notifications
- ✅ No "Action succeeded but manual review needed" warnings

## Performance Notes

- **Profile sync:** ~5-10 seconds (ORCID API call)
- **Funding rescore:** ~2-5 seconds (JSON processing)
- **Dashboard generation:** ~1-2 seconds (HTML template)
- **Deadline check:** ~1-2 seconds (date parsing)
- **Email send:** ~3-5 seconds (SMTP connection + send)

**Total workflow time:** ~20-30 seconds per run
**GitHub Actions free tier:** Includes 2,000 free minutes/month (sufficient for this usage)

## Phase 2 Complete ✅

Phase 2 deliverables achieved:
- ✅ GitHub Actions workflows configured and tested
- ✅ Email alerts module implemented and verified
- ✅ Visual dashboard created and responsive
- ✅ Integration tests passing
- ✅ Deployment documentation complete
- ✅ GitHub Secrets configuration documented

Ready for production automation.
