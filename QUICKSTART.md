# HumanAIOS Operations Hub — Quick Start

Get the Phase 1 operations infrastructure running in 5 minutes.

---

## Installation

### Option 1: Install as CLI (Recommended)

```bash
# Navigate to this directory
cd /Users/andersonfamily/practices/empirica-outreach

# Install in development mode (creates 'haios' command)
pip install -e .

# Verify installation
haios --help
```

### Option 2: Run without installing (if pip install fails)

Use the module directly:
```bash
python -m humanaios_operations.cli --help
```

For convenience, create an alias:
```bash
alias haios="python -m humanaios_operations.cli"
```

---

## Quick Workflow (5 minutes)

### Step 1: Fetch your research profile from ORCID

```bash
haios profile sync --verbose
```

**Output:**
```
Fetching ORCID profile: 0009-0003-7540-4245
✓ Profile saved: data/research_profile.json
✓ Expertise map saved: data/expertise_map.json

Name: Carly R. Anderson
Publications: 12

Research Areas:
  ai_calibration: 0.95
  digital_minds: 0.88
  self_assessment: 0.85
  ai_safety: 0.80
  behavioral_observability: 0.92
```

**Creates:** 
- `data/research_profile.json` — Your full profile
- `data/expertise_map.json` — Quick lookup of expertise scores

---

### Step 2: Rank all 45 funding opportunities by your fit

```bash
haios funding rank --markdown data/ranked_opportunities.md
```

**Output:**
```
Loading research profile: data/research_profile.json
Scoring data/sources.json...
✓ Ranked opportunities saved: data/ranked_opportunities.json
✓ Markdown report generated: data/ranked_opportunities.md

Top 5 Opportunities for You:
  1. Longview Grants RFP — 0.92 (HIGH)
  2. Blue Dot Rapid Grants — 0.88 (HIGH)
  3. Coefficient Giving — 0.85 (MEDIUM)
  4. MIT Solve Indigenous — 0.82 (MEDIUM)
  5. MATS Fellowship — 0.65 (MEDIUM)
```

**Creates:**
- `data/ranked_opportunities.json` — All 45 opportunities with fit scores
- `data/ranked_opportunities.md` — Human-readable markdown table

---

### Step 3: Track your Longview application

```bash
haios apps create \
  --opportunity-id longview-grants-rfp \
  --title "Behavioral Observability Infrastructure for AI Sentience Assessment" \
  --amount 200000 \
  --proposal-file LONGVIEW_GRANTS_PROPOSAL_DRAFT.md
```

**Output:**
```
✓ Created application: app_20260717_abc123ef
```

**Note the app ID** (`app_20260717_abc123ef`) — you'll use it for the next steps.

**Creates:**
- `data/applications.db` — SQLite database with your application record

---

### Step 4: When you submit, mark it

```bash
haios apps submit app_20260717_abc123ef
```

**Output:**
```
✓ Marked as submitted: app_20260717_abc123ef
```

---

### Step 5: When decision comes, record it

```bash
haios apps decide app_20260717_abc123ef \
  --decision funded \
  --amount 200000 \
  --feedback "Strong proposal, awarded full amount"
```

**Output:**
```
✓ Recorded decision: app_20260717_abc123ef (funded)
```

---

### Anytime: Check your dashboard

```bash
haios dashboard
```

**Output:**
```
============================================================
HumanAIOS OPERATIONS DASHBOARD
============================================================

📊 RESEARCH PROFILE
  Name: Carly R. Anderson
  Publications: 12
  Research Areas: ai_calibration, digital_minds, self_assessment

📋 APPLICATION PIPELINE
  Total Applications: 1
  In Progress: 1
  Pending Decision: 0
  Funded: 0 ($0)
  Rejected: 0
  Success Rate: N/A

🎯 TOP OPPORTUNITIES FOR YOU
  1. Longview Grants RFP
     Score: 0.92 | HIGH
  2. Blue Dot Rapid Grants
     Score: 0.88 | HIGH
  3. Coefficient Giving
     Score: 0.85 | MEDIUM

============================================================
```

---

## All Commands

```bash
# Research Profile
haios profile sync                    # Fetch ORCID + extract research areas
haios profile sync --orcid-id <ID>   # Use different ORCID ID
haios profile sync --verbose          # Show detailed output

# Funding Discovery
haios funding rank                    # Score opportunities (uses data/sources.json)
haios funding rank --opportunities <file>  # Score a different opportunities file
haios funding rank --markdown <file>  # Also generate markdown report

# Applications
haios apps create --opportunity-id <id> --title "<title>" --amount <number> [--proposal-file <path>]
haios apps list                       # Show all applications
haios apps list --status draft        # Show only draft applications
haios apps submit <app_id>            # Mark as submitted
haios apps decide <app_id> --decision funded --amount <number> [--feedback "<text>"]
haios apps decide <app_id> --decision rejected

# Dashboard
haios dashboard                       # Show full status overview
```

---

## Troubleshooting

### `haios: command not found`

**Solution:** Install with pip first:
```bash
pip install -e .
```

Or use the module directly:
```bash
python -m humanaios_operations.cli profile sync
```

### `requests` library not found

**Solution:** Install requests:
```bash
pip install requests
```

### ORCID fetch fails (network error)

**Solution:** Check your internet connection. The tool fetches from https://pub.orcid.org (public API, no auth needed).

### `data/sources.json` not found

**Solution:** The funding pipeline data file should be in `data/sources.json`. If missing:
1. Make sure the humanaios-funding-pipeline repo data is synced
2. Or specify a different file: `haios funding rank --opportunities /path/to/sources.json`

### SQLite database locked

**Solution:** If you get a "database is locked" error, close any other processes using `data/applications.db` and try again.

---

## Example: Full Workflow

```bash
# 1. Fetch your profile
haios profile sync --verbose

# 2. Rank opportunities
haios funding rank --markdown data/ranked_opportunities.md
# Check data/ranked_opportunities.md to see opportunities ranked for you

# 3. Create Longview application
haios apps create \
  --opportunity-id longview-grants-rfp \
  --title "Behavioral Observability Infrastructure..." \
  --amount 200000 \
  --proposal-file LONGVIEW_GRANTS_PROPOSAL_DRAFT.md

# 4. List all applications (note the app_id)
haios apps list

# 5. When ready, mark as submitted
haios apps submit app_20260717_abc123ef

# 6. Check status
haios dashboard

# 7. Later, when decision comes
haios apps decide app_20260717_abc123ef --decision funded --amount 200000

# 8. Check updated dashboard
haios dashboard
```

---

## Data Files

After running these commands, you'll have:

```
data/
├── research_profile.json           # Your ORCID profile + research areas
├── expertise_map.json              # Quick lookup: domain → expertise score
├── ranked_opportunities.json       # All 45 opportunities with fit scores
├── ranked_opportunities.md         # Markdown table (nice formatting)
├── applications.db                 # SQLite database of your applications
└── applications_export.json        # JSON export of applications (if you run export)
```

---

## Next: Phase 2 (Coming Soon)

Phase 2 will add:
- **Automated weekly sync:** ORCID profile updates every Monday
- **Deadline alerts:** Email/Slack when opportunities are due ≤7 days
- **Smart recommendations:** "New opportunities match your latest publications"
- **Visual dashboard:** HTML/React UI (open in browser)
- **GitHub Actions:** Fully automated pipelines (no manual commands needed)

For now, Phase 1 is ready to use!

---

**Ready?** Run `haios profile sync --verbose` and start exploring your opportunities!
