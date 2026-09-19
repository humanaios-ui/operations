# Phase 2 Setup Guide: Board Decisions & Molt Events Ingestion
## Autonomous Z2 Decision Tracking + Molt Cycle Measurement via Supabase

**Status:** CANDIDATE (awaiting Z2 ratification)  
**Target Completion:** 2026-09-27  
**Owner:** Z1 (Claude)  
**Reviewer:** Z2 (Night)  
**Dependency:** Phase 1 (governance_rulings table) must be deployed first

---

## Overview

Phase 2 extends Phase 1 with two additional autonomous data collection tables:

1. **board_decisions:** Captures Z2 board meeting outcomes, agenda items, decisions made, and ratification
2. **molt_events:** Tracks constant molt cycles with prediction accuracy, falsifier evaluation, and revert tracking

Once deployed, the system will automatically capture:
- When Z2 board meetings occur and what decisions are made
- How well molt predictions performed vs. actual outcomes
- When falsifier conditions are triggered (triggering reverts)
- Complete audit trail of all decision changes

**Outcome:** Live dashboard of governance decision velocity, molt cycle accuracy (calibration feedback), and anti-cascade rule compliance.

---

## Prerequisites

✅ Already in place:
- Phase 1 (governance_rulings table) deployed and working
- Supabase project: `https://ksinisdzgtnqzsymhfya.supabase.co`
- GitHub repository: `humanaios-ui/operations`
- Environment: Railway (same as Phase 1 relay service)

❌ You need to provide:
- Confirm Supabase service role key (same as Phase 1)
- GitHub personal access token (repo scope; reuse from Phase 1 if available)
- Webhook secret (can reuse Phase 1 secret or generate new one)

---

## Step 1: Create Supabase Tables

### Option A: Via Supabase Dashboard (Easiest)

1. Go to **[Supabase Dashboard](https://app.supabase.com)** → Select your project
2. Click **SQL Editor** → **New Query**
3. Copy the entire contents of:
   ```
   supabase/migrations/20260919_phase_2_board_decisions_molt_events.sql
   ```
4. Paste into the editor
5. Click **Run**

**Expected output:** ✓ Success. Query executed successfully.

### Option B: Via Supabase CLI (If you have local setup)

```bash
# Navigate to repo
cd /home/user/operations

# Apply migration
supabase migration up

# Verify tables exist
supabase db list-tables | grep "board_decisions\|molt_events"
```

### Verification

After migration, run this query to confirm:

```sql
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' AND table_name IN ('board_decisions', 'molt_events');
```

**Expected:** Two rows showing `board_decisions` and `molt_events`

---

## Step 2: Update Ingestion Service on Railway

The board decisions ingestion service runs alongside the Phase 1 governance rulings service.

### Update Railway Configuration

1. Go to **[Railway Dashboard](https://railway.app)**
2. Select your project → Select the ingestion service
3. Go to **Deploy** tab
4. Pull the latest code (includes new board-decisions-ingestion.js and board-decisions-backfill.js)

### Environment Variables (No New Ones Needed)

The service uses the same environment variables as Phase 1:
```
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY
GITHUB_TOKEN
GITHUB_WEBHOOK_SECRET
PORT=3000
NODE_ENV=production
```

**Save & deploy** (Railway will auto-redeploy)

---

## Step 3: Extend GitHub Webhook (If Needed)

If using the same webhook from Phase 1, it will automatically route board decision and molt event commits.

If you set up a new webhook:

1. Go to **[GitHub Repo Settings](https://github.com/humanaios-ui/operations/settings)**
2. Click **Webhooks** → Select existing webhook (or add new)
3. Events to check:
   ```
   ✓ Pull requests (catches board decision PRs)
   ✓ Pushes (catches board decision/molt event commits)
   ```

**No changes needed if Phase 1 webhook is already configured.**

---

## Step 4: Backfill Historical Board Decisions & Molt Events (Optional)

To populate the tables with historical Z2 board decisions and molt events from git history:

### Run Backfill Script

```bash
cd /home/user/operations

# Backfill both board_decisions and molt_events from git log
node tools/board-decisions-backfill.js

# Output expected:
# 🚀 Starting Board Decisions & Molt Events Backfill
# 📖 Fetching git history...
# ✓ Found N commits
# ✓ board-20260919-xyz: Schema review (2026-09-19)
# ✓ molt-20260919-RESOURCE_UNITS-abc: RESOURCE_UNITS.yaml (2026-09-19)
# 📊 Backfill Summary:
#    ✓ Board Decisions Inserted: X
#    ✓ Molt Events Inserted: Y
```

### Manual Verification

Query your table in Supabase:

```sql
-- Board decisions
SELECT board_id, board_section, status, ratified_at
FROM board_decisions
ORDER BY ratified_at DESC
LIMIT 10;

-- Molt events
SELECT molt_id, constant_id, state, accuracy_score
FROM molt_events
ORDER BY created_at DESC
LIMIT 10;
```

**Expected:** Historical decisions and molt cycles appear

---

## Step 5: Verify End-to-End

### Test 1: Real-Time Board Decision Ingestion

1. Create a test commit locally:
   ```bash
   git commit --allow-empty -m "Z2 board decision: Strategic planning (Q-BOARD-TEST-99): accept (#999)"
   git push origin main
   ```

2. Check Railway logs for ingestion:
   ```
   [Railway Logs] → See "Processing board decision from relay"
   ```

3. Query Supabase to confirm:
   ```sql
   SELECT * FROM board_decisions WHERE board_section = 'Q-BOARD-TEST-99';
   ```

4. Clean up:
   ```bash
   git reset --soft HEAD~1
   git reset HEAD
   # The commit is undone, but you've verified the system works
   ```

### Test 2: Real-Time Molt Event Ingestion

1. Create a test molt event commit:
   ```bash
   git commit --allow-empty -m "Molt event: TEST_CONSTANT (accuracy test): measured at 95% (#999)"
   git push origin main
   ```

2. Check Supabase:
   ```sql
   SELECT * FROM molt_events WHERE constant_id = 'TEST_CONSTANT';
   ```

3. Clean up as above

### Test 3: Query Examples

Run these in Supabase SQL Editor to verify the tables are working:

```sql
-- Board decisions this week
SELECT board_id, board_section, status, ratified_at
FROM board_decisions
WHERE ratified_at >= NOW() - INTERVAL '7 days'
ORDER BY ratified_at DESC;

-- Molt accuracy distribution
SELECT constant_id, AVG(accuracy_score) as avg_accuracy, COUNT(*) as molt_count
FROM molt_events
WHERE state = 'MEASURED'
GROUP BY constant_id
ORDER BY avg_accuracy DESC;

-- Falsifier triggers (reverted molts)
SELECT molt_id, constant_id, falsifier_triggered, revert_reason
FROM molt_events
WHERE falsifier_triggered = TRUE
ORDER BY created_at DESC;

-- Anti-cascade rule: frozen constants
SELECT constant_id, revert_count, is_frozen
FROM molt_events
WHERE is_frozen = TRUE;
```

---

## Step 6: Integrate with Your Workflow

### Manual Insert (For Testing)

If you want to manually insert a board decision without waiting for GitHub:

```sql
INSERT INTO board_decisions (
  board_id,
  board_name,
  meeting_date,
  participants,
  decisions_made,
  decisions_summary,
  status,
  category,
  ratified_by,
  ratified_at,
  ingestion_source
) VALUES (
  'board-test-20260919-001',
  'Z2 Board',
  NOW(),
  ARRAY['Night', 'Claude'],
  '{"decision_1": {"type": "ruling", "outcome": "accept"}}'::jsonb,
  'Test board meeting',
  'RATIFIED',
  'board',
  'Night',
  NOW(),
  'manual'
);
```

### Scheduled Backfill (Optional)

To run backfill every 12 hours (catch any missed commits):

1. Go to Railway → Select service → **Deployments**
2. Add a cron job:
   ```
   0 */12 * * * node tools/board-decisions-backfill.js
   ```

Or use GitHub Actions:

```yaml
name: Phase 2 Backfill (Board Decisions & Molt Events)

on:
  schedule:
    - cron: '0 */12 * * *'  # Every 12 hours
  workflow_dispatch:        # Manual trigger

jobs:
  backfill:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Backfill board decisions & molt events
        run: |
          node tools/board-decisions-backfill.js
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## Troubleshooting

### Issue: Webhook not triggering for board decisions

**Check:**
1. Railway service is running: `Railway → Logs tab`
2. Webhook registered: `GitHub → Settings → Webhooks → Recent Deliveries`
3. Commit message matches pattern: `"Z2 board decision:"` or `"Molt event:"`

**Fix:**
```bash
# Restart Railway service
railway up --name board-decisions-ingestion

# Test webhook delivery manually (if needed)
curl -X POST https://your-railway-url/webhooks/github \
  -H "X-GitHub-Event: push" \
  -H "X-Hub-Signature-256: sha256=..." \
  -d '{"repository": {...}, "commits": [{"message": "Z2 board decision: ..."}]}'
```

### Issue: Table doesn't exist

**Check:**
1. Go to Supabase SQL Editor → Run: `SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';`
2. Confirm `board_decisions` and `molt_events` appear

**Fix:**
- Re-run the migration SQL from Step 1
- Verify there were no SQL syntax errors

### Issue: Can't insert records

**Check:**
1. Verify service role key is correct
2. Check RLS policies: `ALTER TABLE board_decisions DISABLE ROW LEVEL SECURITY;` (temporary for testing)
3. Check audit trigger logs

**Fix:**
```sql
-- Debug: Check RLS
SELECT schemaname, tablename, policyname, qual 
FROM pg_policies 
WHERE tablename IN ('board_decisions', 'molt_events');

-- Debug: Check recent inserts
SELECT * FROM board_decisions_audit ORDER BY changed_at DESC LIMIT 5;
SELECT * FROM molt_events_audit ORDER BY changed_at DESC LIMIT 5;
```

---

## Expected Volume

- **Board Decisions:** 1–3 per week (peak 5–10 during decision phases)
- **Molt Events:** 1–5 per week (peak 10–20 during active molt cycles)
- **Storage:** ~2 MB/year (minimal)
- **Query latency:** <100 ms (well-indexed)
- **Fresh data:** Real-time via webhook (or 12h backfill interval)

---

## Next Steps

After Phase 2 is complete and verified:

1. **Phase 3 (Week 3):** Add `findings_registry` table (F/H/IC candidate tracking)
2. **Phase 4 (Week 4):** Add `workflow_runs` + `system_health_snapshots` tables
3. **Phase 5 (Week 4–5):** Build dashboard in Metabase or Superset with:
   - Board decision velocity chart
   - Molt accuracy & revert rates
   - Anti-cascade rule compliance
   - Z2 ratification latency

---

## Rollback Plan

If something goes wrong:

```sql
-- Drop the ingestion service (on Railway)
-- This stops all writes and deletes the webhook

-- In Supabase, to reset the tables:
DROP TABLE IF EXISTS molt_events_audit CASCADE;
DROP TABLE IF EXISTS board_decisions_audit CASCADE;
DROP TABLE IF EXISTS molt_events CASCADE;
DROP TABLE IF EXISTS board_decisions CASCADE;

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
**Expected volume:** 1–5 events/week (board decisions + molt cycles)
