# Phase 1 Setup Guide: Governance Rulings Ingestion
## Autonomous Z2 Decision Tracking via Supabase

**Status:** CANDIDATE (awaiting Z2 ratification)  
**Target Completion:** 2026-09-20  
**Owner:** Z1 (Claude)  
**Reviewer:** Z2 (Night)

---

## Overview

This guide walks you (Night/Z2) through setting up autonomous ingestion of governance rulings into Supabase. Once deployed, all Z2 board decisions will be automatically captured in real-time with zero manual intervention.

**Outcome:** Live dashboard of all Z2 rulings, decisions, and state transitions.

---

## Prerequisites

✅ Already in place:
- Supabase project: `https://ksinisdzgtnqzsymhfya.supabase.co`
- GitHub repository: `humanaios-ui/operations`
- Environment: Railway (same as relay service)

❌ You need to provide:
- Supabase service role key (from project settings)
- GitHub personal access token (repo scope)
- Webhook secret (random string for HMAC verification)

---

## Step 1: Create Supabase Table

### Option A: Via Supabase Dashboard (Easiest)

1. Go to **[Supabase Dashboard](https://app.supabase.com)** → Select your project
2. Click **SQL Editor** → **New Query**
3. Copy the entire contents of:
   ```
   supabase/migrations/20260919_create_governance_rulings.sql
   ```
4. Paste into the editor
5. Click **Run**

**Expected output:** ✓ Success. Query executed successfully.

### Option B: Via Supabase CLI (If you have local setup)

```bash
# Install CLI if needed
npm install -g supabase

# Navigate to repo
cd /home/user/operations

# Apply migration
supabase migration up

# Verify table exists
supabase db list-tables | grep governance_rulings
```

### Verification

After migration, run this query to confirm:

```sql
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' AND table_name = 'governance_rulings';
```

**Expected:** One row showing `governance_rulings`

---

## Step 2: Gather Credentials

### Supabase Service Role Key

1. Go to **[Supabase Dashboard](https://app.supabase.com)** → Project settings
2. Click **API** (left sidebar)
3. Under **Project API keys**, copy `service_role` key (⚠️ **Keep this private!**)

### GitHub Personal Access Token

1. Go to **[GitHub Settings](https://github.com/settings/tokens)** → **Personal access tokens** (classic)
2. Click **Generate new token**
3. Name: `HumanAIOS Governance Rulings`
4. Scopes: Check only `repo` (full control of private repositories)
5. Click **Generate token**
6. Copy the token (you won't see it again)

### Webhook Secret

Generate a random secret:
```bash
# macOS/Linux
openssl rand -hex 32

# Output example: a3f7b8d2e1c4g9h6i2j5k8l1m4n7o0p3q6r9s2t5u8v1w4x7y0z3

# On Windows (PowerShell)
[System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes([guid]::NewGuid().ToString() + [guid]::NewGuid().ToString()))
```

Save this secret securely (you'll need it in the next step).

---

## Step 3: Deploy Ingestion Service to Railway

The ingestion service runs alongside your relay service.

### Option A: Add to Existing Railway Service (Recommended)

If your relay service is already on Railway:

1. Go to **[Railway Dashboard](https://railway.app)**
2. Select your project → Select the relay service
3. Go to **Deploy** tab
4. Update `Dockerfile` or `railway.json` to include the ingestion service

**Example railway.json:**
```json
{
  "build": {
    "builder": "nixpacks"
  },
  "deploy": {
    "numReplicas": 1,
    "restartPolicyMaxRetries": 3,
    "restartPolicyWindowMs": 60000
  },
  "plugins": [
    {
      "source": "https://github.com/railwayapp/nixpacks/releases/download/v0.18.4/npm-service.tar.gz"
    }
  ]
}
```

### Option B: Create New Railway Service

1. Go to **[Railway Dashboard](https://railway.app)**
2. Click **+ New Project** or add to existing project
3. Select **GitHub repo** → `humanaios-ui/operations`
4. Railway will auto-detect and deploy

### Environment Variables

Once deployed, set these in Railway:

**Railway Dashboard** → Select service → **Variables**

```
SUPABASE_URL=https://ksinisdzgtnqzsymhfya.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<paste service role key from Step 2>
GITHUB_TOKEN=<paste GitHub token from Step 2>
GITHUB_WEBHOOK_SECRET=<paste webhook secret from Step 2>
PORT=3000
NODE_ENV=production
```

**Save & deploy** (Railway will auto-redeploy)

---

## Step 4: Configure GitHub Webhook

Once your ingestion service is deployed, GitHub needs to know where to send events.

### Get Your Webhook URL

From Railway dashboard:
1. Select your service → **Deployments** → Latest
2. Copy the **URL** (e.g., `https://governance-rulings-ingestion-prod.railway.app`)

### Register Webhook in GitHub

1. Go to **[GitHub Repo Settings](https://github.com/humanaios-ui/operations/settings)**
2. Click **Webhooks** (left sidebar)
3. Click **Add webhook**
4. Fill in:
   ```
   Payload URL:      https://your-railway-url/webhooks/github
   Content type:     application/json
   Secret:           <paste webhook secret from Step 2>
   SSL verification: Enable (default)
   ```
5. Check these events:
   ```
   ✓ Pull requests
   ✓ Pushes
   (Pushes will catch immediate commit activity)
   (Pull requests will catch merged PRs with commit details)
   ```
6. Check **Active** (enabled)
7. Click **Add webhook**

### Test Webhook

1. GitHub will show **Recent Deliveries** at the bottom
2. Click the most recent one
3. You should see:
   ```
   ✓ Delivery successful (200 OK)
   ```

If you see a failure:
- Check that your Railway service is running
- Verify the URL is correct
- Check Railway logs: **Logs** tab in your service

---

## Step 5: Backfill Historical Rulings (Optional)

To populate the table with recent rulings from git history:

### Run Backfill Script

```bash
cd /home/user/operations

# Option 1: Run the ingestion script directly
node tools/governance-rulings-backfill.js

# Option 2: Parse git log and insert manually
git log --all --grep="Z2 ruling\|z2 d" --format="%H|%ai|%s|%b" --reverse > /tmp/rulings.txt

# Then use the SQL script to insert from /tmp/rulings.txt
```

**Expected output:**
```
Starting backfill...
✓ Processing d15 (Q-BOARD-RULING-15): rule now
✓ Processing d16 (Q-BOARD-RULING-16): archive as listed
...
✓ Backfill complete: inserted 16 rulings
```

### Manual Verification

Query your table in Supabase:

```sql
SELECT 
  ruling_id,
  decision,
  question,
  ratified_at,
  state
FROM governance_rulings
ORDER BY ratified_at DESC
LIMIT 10;
```

**Expected:** Your recent Z2 rulings appear

---

## Step 6: Verify End-to-End

### Test 1: Real-Time Ingestion

1. Create a test commit locally:
   ```bash
   git commit --allow-empty -m "Z2 ruling d99 (TEST-VERIFICATION): accept (#999)"
   git push origin main
   ```

2. Check Railway logs for ingestion:
   ```
   [Railway Logs] → See "Processing merged PR #999"
   ```

3. Query Supabase to confirm:
   ```sql
   SELECT * FROM governance_rulings WHERE ruling_id = 'd99';
   ```

4. Clean up:
   ```bash
   git reset --soft HEAD~1
   git reset HEAD
   # The commit is undone, but you've verified the system works
   ```

### Test 2: Query Examples

Run these in Supabase SQL Editor to verify the table is working:

```sql
-- All rulings this week
SELECT ruling_id, decision, question, ratified_at
FROM governance_rulings
WHERE ratified_at >= NOW() - INTERVAL '7 days'
ORDER BY ratified_at DESC;

-- Group by decision type
SELECT decision, COUNT(*) as count
FROM governance_rulings
GROUP BY decision
ORDER BY count DESC;

-- Audit trail
SELECT ruling_id, operation, changed_at
FROM governance_rulings_audit
ORDER BY changed_at DESC
LIMIT 10;
```

---

## Step 7: Integrate with Your Workflow

### Manual Trigger (For Testing)

If you want to manually insert a ruling without waiting for GitHub:

```sql
INSERT INTO governance_rulings (
  ruling_id,
  decision,
  question,
  ratified_by,
  ratified_at,
  state,
  category,
  ingestion_source
) VALUES (
  'd99',
  'RULE_NOW',
  'TEST: Verify end-to-end ingestion',
  'Night',
  NOW(),
  'PENDING',
  'board',
  'manual'
);
```

### Scheduled Backfill (Optional)

To run backfill every 12 hours (catch any missed commits):

1. Go to Railway → Select service → **Deployments**
2. Add a cron job:
   ```
   0 */12 * * * node tools/governance-rulings-ingestion.js --backfill
   ```

Or use GitHub Actions:

```yaml
name: Governance Rulings Backfill

on:
  schedule:
    - cron: '0 */12 * * *'  # Every 12 hours
  workflow_dispatch:        # Manual trigger

jobs:
  backfill:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Backfill governance rulings
        run: |
          node tools/governance-rulings-backfill.js
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## Troubleshooting

### Issue: Webhook not triggering

**Check:**
1. Railway service is running: `Railway → Logs tab`
2. Webhook registered: `GitHub → Settings → Webhooks → Recent Deliveries`
3. Secret matches: Compare `GITHUB_WEBHOOK_SECRET` on Railway vs. GitHub webhook config

**Fix:**
```bash
# Restart Railway service
railway up --name governance-rulings-ingestion

# Test webhook delivery manually
curl -X POST https://your-railway-url/webhooks/github \
  -H "X-GitHub-Event: push" \
  -H "X-Hub-Signature-256: sha256=..." \
  -d '{"repository": {"full_name": "humanaios-ui/operations"}, "commits": [...]}'
```

### Issue: Table doesn't exist

**Check:**
1. Go to Supabase SQL Editor → Run: `SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';`
2. Confirm `governance_rulings` appears

**Fix:**
- Re-run the migration SQL from Step 1
- Verify there were no SQL syntax errors

### Issue: Can't insert records

**Check:**
1. Verify service role key is correct
2. Check RLS policies: `ALTER TABLE governance_rulings DISABLE ROW LEVEL SECURITY;` (temporary for testing)
3. Check audit trigger logs

**Fix:**
```sql
-- Debug: Check RLS
SELECT schemaname, tablename, policyname, qual 
FROM pg_policies 
WHERE tablename = 'governance_rulings';

-- Debug: Check recent inserts
SELECT * FROM governance_rulings_audit ORDER BY changed_at DESC LIMIT 5;
```

---

## Next Steps

After Phase 1 is complete and verified:

1. **Phase 2 (Week 2):** Add `board_decisions` table + relay integration
2. **Phase 3 (Week 2–3):** Add `molt_events` table for calibration tracking
3. **Phase 4 (Week 3):** Add `findings_registry` table
4. **Phase 5 (Week 4+):** Build dashboard in Metabase or Superset

---

## Rollback Plan

If something goes wrong:

```sql
-- Drop the ingestion service (on Railway)
-- This stops all writes and deletes the webhook

-- In Supabase, to reset the table:
DROP TABLE IF EXISTS governance_rulings_audit CASCADE;
DROP TABLE IF EXISTS governance_rulings CASCADE;

-- Re-run the migration SQL to recreate clean
```

---

## Contact & Questions

- **For technical issues:** Check Railway logs + Supabase SQL Editor
- **For governance questions:** Reference CLAUDE.md authority matrix
- **For modifications:** File a Q-* candidate in REGISTERED.md for Z2 review

---

**Created:** 2026-09-19  
**Status:** Ready for Z2 ratification  
**Expected volume:** 1–3 new rulings/day
