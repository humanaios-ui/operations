# HumanAIOS Operations Hub

Orchestration layer for research profile management, funding discovery, and application tracking automation.

## Overview

The Operations Hub automates:

- **Profile Sync** — Fetches ORCID profile (research areas, publications)
- **Funding Discovery** — Ranks opportunities by research fit
- **Deadline Tracking** — Monitors and alerts on approaching deadlines
- **Dashboard** — Generates HTML dashboard of research & opportunities
- **Email Alerts** — Sends digests and deadline notifications

## Installation

```bash
pip install -e .
```

Or use directly:
```bash
PYTHONPATH=./src python -m humanaios_operations.cli --help
```

## Quick Start

### 1. Sync Your Research Profile
```bash
python -m humanaios_operations.cli profile sync --verbose
```
Fetches your ORCID profile and saves to `data/research_profile.json`

### 2. Rank Funding Opportunities
```bash
python -m humanaios_operations.cli funding rank --markdown data/ranked_opportunities.md
```
Ranks opportunities by research fit, outputs markdown report

### 3. Check Deadlines
```bash
python -m humanaios_operations.cli deadline_checker check
```
Categorizes opportunities by deadline urgency

### 4. Generate Dashboard
```bash
python -m humanaios_operations.cli dashboard generate
```
Creates responsive HTML dashboard at `reports/dashboard.html`

### 5. Send Email Alerts
```bash
# Test SMTP configuration
python -m humanaios_operations.cli email_alerts test

# Send weekly digest
python -m humanaios_operations.cli email_alerts digest

# Send deadline alert
python -m humanaios_operations.cli email_alerts alert
```

## Configuration

### Environment Variables
```bash
export ORCID_ID="0009-0003-7540-4245"           # Your ORCID ID
export SMTP_HOST="smtp.gmail.com"                # SMTP server
export SMTP_PORT="587"                           # SMTP port
export SMTP_USER="notifications@example.com"     # SMTP username
export SMTP_PASS="your-app-password"            # SMTP password
export ALERT_EMAIL="recipient@example.com"       # Alert recipient
```

### GitHub Actions (Workflow Integration)
Secrets are configured via GitHub Settings:
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USER`
- `SMTP_PASS`
- `ALERT_EMAIL`

See `docs/GITHUB_SECRETS_SETUP.md` for setup instructions.

## Module Reference

### profile.py
```python
from humanaios_operations import profile

# Fetch and save ORCID profile
data = profile.sync_profile(orcid_id="0009-0003-7540-4245", verbose=True)

# Extract research areas
areas = profile.extract_research_areas(profile_data)

# Extract publications
pubs = profile.extract_publications(profile_data)
```

### deadline_checker.py
```python
from humanaios_operations import deadline_checker

# Check for upcoming deadlines
result = deadline_checker.check_deadlines(
    opportunities_file="data/opportunities.json",
    days_ahead=30,
    dry_run=False
)
# Returns: {urgent: [...], soon: [...], upcoming: [...], rolling: [...]}
```

### email_alerts.py
```python
from humanaios_operations import email_alerts

# Test SMTP connection
email_alerts.test_smtp_connection()

# Send digest report
email_alerts.digest_report(opportunities_file="data/ranked_opportunities.json")

# Send deadline alert
email_alerts.deadline_alert(
    opportunities_file="data/ranked_opportunities.json",
    days_ahead=7
)

# Send custom email (raw)
email_alerts.send_email(
    subject="Custom Subject",
    body_html="<p>Your content</p>"
)
```

### dashboard.py
```python
from humanaios_operations import dashboard

# Generate HTML dashboard
dashboard.generate_dashboard(
    opportunities_file="data/ranked_opportunities.json",
    profile_file="data/research_profile.json",
    output_file="reports/dashboard.html"
)
```

## Workflows

Three GitHub Actions workflows orchestrate the operations:

### 1. Weekly Profile Sync (Monday 09:00 UTC)
- Fetches ORCID profile
- Extracts research areas and publications
- Commits updated profile data

### 2. Weekly Funding Rescore (Monday 09:30 UTC)
- Ranks opportunities by research fit
- Generates HTML dashboard
- Sends weekly digest email
- Commits updated rankings and dashboard

### 3. Daily Deadline Alerts (Daily 08:00 UTC)
- Checks for upcoming deadlines
- Sends deadline alert emails
- Categorizes by urgency

## Data Files

### Input
- `data/opportunities.json` — Funding opportunities (from humanaios-funding-pipeline)
- `data/research_profile.json` — Research profile (auto-generated)

### Output
- `data/research_profile.json` — ORCID profile, research areas, publications
- `data/ranked_opportunities.json` — Opportunities ranked by research fit
- `data/ranked_opportunities.md` — Markdown report of rankings
- `reports/dashboard.html` — Interactive HTML dashboard

## Email Templates

### Weekly Digest
- Subject: 📊 HumanAIOS Weekly Digest
- Shows: Top 5 opportunities by fit score
- Includes: Sponsor, award size, deadline
- Sent: Monday 09:30 UTC

### Deadline Alert
- Subject: ⏰ URGENT: N funding deadlines within N days
- Shows: Urgent deadlines with days remaining
- Sorted: By urgency (nearest first)
- Sent: Daily 08:00 UTC

## Integration Tests

Run end-to-end tests:
```bash
python tests/integration_test.py
```

Tests verify:
- Profile sync works
- Opportunities ranking works
- Dashboard generation works
- Deadline detection works
- Email alerts (with SMTP check)

## Troubleshooting

### ORCID Profile Won't Fetch
```bash
# Verify ORCID API is reachable
curl https://pub.orcid.org/v3.0/0009-0003-7540-4245

# Check if ORCID ID is correct
python -m humanaios_operations.cli profile sync --verbose
```

### Email Not Sending
```bash
# Test SMTP configuration
python -m humanaios_operations.cli email_alerts test

# Verify secrets are set (GitHub Actions)
# Check workflow logs: Actions → workflow run → logs
```

### Workflows Not Running
```bash
# Check Actions are enabled
# Settings → Actions → General → Enable

# Verify workflow files exist
ls -la .github/workflows/

# Check workflow syntax
# Actions tab → select workflow → should show green checkmark
```

## Development

### Adding New Operations
1. Create new module in `src/humanaios_operations/`
2. Implement main functions
3. Add CLI command in `cli.py`
4. Add integration test in `tests/`
5. Commit and document

### Testing Locally
```bash
export PYTHONPATH=./src

# Test individual commands
python -m humanaios_operations.cli profile sync --verbose
python -m humanaios_operations.cli deadline_checker check --dry-run

# Run integration suite
python tests/integration_test.py
```

## License

Part of HumanAIOS project.

## Support

See:
- `docs/GITHUB_SECRETS_SETUP.md` — Email configuration
- `docs/DEPLOYMENT_GUIDE.md` — Launch & monitoring
- `tests/integration_test.py` — End-to-end testing
