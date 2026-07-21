# GitHub Secrets Setup Guide

This document explains how to configure GitHub Secrets for the HumanAIOS Operations automation workflows.

## Overview

The workflows use GitHub Secrets to securely store sensitive SMTP credentials. These secrets are accessed by the GitHub Actions workflows to send email notifications.

## Secrets Required

Five repository secrets are required for full email functionality:

| Secret Name | Purpose | Example | Required |
|---|---|---|---|
| `SMTP_HOST` | SMTP server hostname | `smtp.gmail.com` | Yes (if email enabled) |
| `SMTP_PORT` | SMTP server port | `587` | Yes (if email enabled) |
| `SMTP_USER` | SMTP username/email | `notifications@example.com` | Yes (if email enabled) |
| `SMTP_PASS` | SMTP password or app-specific password | `xxxxxxxxxxxx` | Yes (if email enabled) |
| `ALERT_EMAIL` | Recipient email address | `carly@example.com` | Yes (if email enabled) |

## Setup Instructions

### Step 1: Navigate to Repository Settings
1. Go to your GitHub repository: `humanaios-ui/operations`
2. Click **Settings** (in the top navigation)
3. Click **Secrets and variables** (in the left sidebar)
4. Click **Actions** (under "Secrets and variables")

### Step 2: Add Each Secret

For each secret below, click **New repository secret** and add:

#### SMTP_HOST
- **Name:** `SMTP_HOST`
- **Value:** Your SMTP server hostname
  - Gmail: `smtp.gmail.com`
  - Outlook: `smtp-mail.outlook.com`
  - Custom: Your server's SMTP hostname

#### SMTP_PORT
- **Name:** `SMTP_PORT`
- **Value:** SMTP port number
  - Gmail/most services: `587`
  - Some services: `465` (TLS) or `25` (unencrypted, not recommended)

#### SMTP_USER
- **Name:** `SMTP_USER`
- **Value:** Email address or username for SMTP authentication
  - Gmail: Your full Gmail address (`user@gmail.com`)
  - Custom: Your SMTP username
  
  ⚠️ **Gmail users:** Use an [app-specific password](https://support.google.com/accounts/answer/185833), not your main password

#### SMTP_PASS
- **Name:** `SMTP_PASS`
- **Value:** SMTP password or app-specific password
  - Gmail: Use app-specific password from 2-factor authentication settings
  - Custom: Your SMTP password

#### ALERT_EMAIL
- **Name:** `ALERT_EMAIL`
- **Value:** Email address where alerts should be sent
  - Example: `carly@example.com`

### Step 3: Verify Configuration

Run the email configuration test:

```bash
python -m humanaios_operations.cli email_alerts test
```

Expected output when properly configured:
```
✅ SMTP connection successful: smtp.gmail.com:587
```

## Workflow Behavior

### With Secrets Configured
- ✅ Weekly digest emails sent Monday 09:30
- ✅ Deadline alert emails sent daily 08:00
- ✅ Emails include research opportunities ranked by fit

### Without Secrets (Graceful Degradation)
- ✅ All workflows still run
- ⚠️  Email steps skip silently
- ✅ Profile sync completes
- ✅ Dashboard generates
- ✅ No errors or failures

## Configuration Examples

### Gmail Setup (Recommended for Testing)

1. Enable 2-factor authentication on your Google account
2. Generate an app-specific password: https://myaccount.google.com/apppasswords
3. Add secrets:
   - `SMTP_HOST`: `smtp.gmail.com`
   - `SMTP_PORT`: `587`
   - `SMTP_USER`: `your-email@gmail.com`
   - `SMTP_PASS`: `xxxx xxxx xxxx xxxx` (generated app password)
   - `ALERT_EMAIL`: `recipient@example.com`

### Office 365 / Outlook Setup

1. Add secrets:
   - `SMTP_HOST`: `smtp-mail.outlook.com`
   - `SMTP_PORT`: `587`
   - `SMTP_USER`: `your-email@outlook.com`
   - `SMTP_PASS`: `Your Office 365 password`
   - `ALERT_EMAIL`: `recipient@example.com`

### Custom SMTP Server

Contact your email provider for:
- SMTP hostname
- Port (typically 587 or 465)
- Username and password
- TLS/SSL requirements

Then add secrets accordingly.

## Troubleshooting

### "SMTP configuration incomplete"
**Cause:** One or more secrets not set
**Solution:** Verify all 5 secrets are configured in GitHub Settings

### "SMTP connection failed"
**Cause:** Incorrect credentials or server unavailable
**Solution:** 
- Verify credentials are correct
- Check SMTP_HOST and SMTP_PORT are correct
- For Gmail, ensure you're using app-specific password, not main password
- Verify firewall allows outbound SMTP connections

### "Authentication failed"
**Cause:** Invalid username or password
**Solution:**
- Double-check credentials
- For Gmail: verify app-specific password was generated correctly
- Try connecting with a mail client to verify credentials work

### Workflow shows warning but continues
**This is normal.** The workflows are designed to continue even if email fails. Check:
1. Secrets are configured
2. SMTP server is reachable
3. Credentials are correct

To debug, check the workflow run logs in **Actions** tab.

## Security Best Practices

1. **Never commit credentials** to the repository
2. **Use app-specific passwords** for services that support them (Gmail, Office 365)
3. **Rotate passwords** periodically
4. **Limit email access** — use a dedicated service account if possible
5. **Use TLS/STARTTLS** (port 587) instead of unencrypted (port 25)
6. **Restrict permissions** — GitHub secrets are only available to Actions workflows

## Testing Workflow Configuration

After setting up secrets, workflows will run on their schedule:

- **Weekly Profile Sync:** Every Monday at 09:00 UTC
- **Weekly Funding Rescore + Email:** Every Monday at 09:30 UTC
- **Daily Deadline Alerts:** Every day at 08:00 UTC

To test immediately:

1. Go to **Actions** tab
2. Select a workflow (e.g., "Weekly Profile Sync")
3. Click **Run workflow** → **Run workflow**
4. Monitor the logs to verify email is sent

## Disabling Email (Optional)

If you want to disable email alerts:

1. Remove or leave empty the SMTP secrets
2. Workflows will continue to run normally
3. Email steps will be skipped gracefully
4. No errors will occur

To re-enable, reconfigure the secrets.

## Support

For issues:
1. Check workflow logs in **Actions** tab
2. Run `python -m humanaios_operations.cli email_alerts test` locally
3. Verify SMTP server credentials with a mail client
4. Review troubleshooting section above
