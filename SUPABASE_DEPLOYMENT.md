# Autonomy Metrics Deployment Guide

Deploy the autonomy metrics infrastructure to Supabase using the CLI.

---

## Prerequisites

1. **Supabase CLI installed** (check: `supabase --version`)
2. **Supabase account** with an active project
3. **Project credentials** (project ID, API URL, service role key)

---

## Step 1: Configure Supabase Project

Edit `.supabase/config.toml` and update:

```toml
[project]
project_id = "YOUR_PROJECT_ID"  # From https://app.supabase.com/projects
api_url = "https://YOUR_PROJECT_ID.supabase.co"
```

Get your `PROJECT_ID` from Supabase dashboard:
1. Go to https://app.supabase.com
2. Select your project
3. Settings → API → Project ID

---

## Step 2: Authenticate CLI

```bash
supabase login
```

Follow the prompts to authenticate. This creates a local token.

---

## Step 3: Link to Remote Project

```bash
supabase link --project-ref YOUR_PROJECT_ID
```

Verify the link:
```bash
supabase status
```

You should see:
```
Connecting to Supabase...
Supabase project API:
  Status:                 ONLINE
  API URL:                https://YOUR_PROJECT_ID.supabase.co
  Anon key:               eyJhbGc...
  Service role key:       eyJhbGc...
  Database:               postgres
```

---

## Step 4: Deploy Schema Migration

Deploy the autonomy metrics schema to your project:

```bash
supabase db push
```

This will:
1. Read `supabase/migrations/20260910_autonomy_metrics_schema.sql`
2. Apply it to your remote database
3. Create all tables, indexes, views, and RLS policies

**Expected output:**
```
Applying migration 20260910_autonomy_metrics_schema.sql...
✓ Migration succeeded
✓ Schema deployment complete
```

Verify tables exist:
```bash
supabase db list
```

You should see in the `autonomy` schema:
- `events`
- `decisions`
- `escalations`
- `metrics`
- `decision_audit`

---

## Step 5: Deploy Edge Functions

Deploy the two Edge Functions:

### Deploy Ingestion Function
```bash
supabase functions deploy autonomy-metrics/ingest \
  --project-ref YOUR_PROJECT_ID
```

### Deploy Metrics Query Function
```bash
supabase functions deploy autonomy-metrics/metrics \
  --project-ref YOUR_PROJECT_ID
```

**Expected output:**
```
Deploying function 'autonomy-metrics-ingest'...
✓ Function deployed successfully
  URL: https://YOUR_PROJECT_ID.supabase.co/functions/v1/autonomy-metrics/ingest

Deploying function 'autonomy-metrics-metrics'...
✓ Function deployed successfully
  URL: https://YOUR_PROJECT_ID.supabase.co/functions/v1/autonomy-metrics/metrics
```

---

## Step 6: Verify Deployment

### Test Event Ingestion

```bash
curl -X POST \
  "https://YOUR_PROJECT_ID.supabase.co/functions/v1/autonomy-metrics/ingest" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ANON_KEY" \
  -d '{
    "event_id": "evt-test-001",
    "practice_id": "test-practice",
    "event_type": "decision",
    "channel": "decision_proposal",
    "payload": {
      "proposal_title": "Test decision"
    }
  }'
```

**Expected response:**
```json
{
  "ok": true,
  "event_id": "evt-test-001"
}
```

### Test Metrics Query

```bash
curl "https://YOUR_PROJECT_ID.supabase.co/functions/v1/autonomy-metrics/metrics" \
  -H "Authorization: Bearer YOUR_ANON_KEY"
```

**Expected response:**
```json
{
  "ok": true,
  "metrics": [...]
}
```

Get your `YOUR_ANON_KEY` from Supabase dashboard:
1. Settings → API → Project API Keys → anon key

---

## Step 7: Configure Environment Variables (for production)

Set these in your application environment:

```bash
export SUPABASE_URL="https://YOUR_PROJECT_ID.supabase.co"
export SUPABASE_ANON_KEY="eyJhbGc..."  # From Supabase dashboard
export SUPABASE_SERVICE_ROLE_KEY="eyJhbGc..."  # From Settings → API
```

---

## Step 8: Use Client SDKs

### Python

```python
from supabase.clients.autonomy_metrics_client import AutonomyMetricsClient

client = AutonomyMetricsClient(
    supabase_url="https://YOUR_PROJECT_ID.supabase.co",
    anon_key="YOUR_ANON_KEY"
)

# Send decision event
result = await client.send_decision_event(
    practice_id="empirica-autonomy",
    title="Enable safety gate",
    dimensions=["truth", "harm"]
)

# Get metrics
metrics = await client.get_metrics(practice_id="empirica-autonomy")
```

### TypeScript

```typescript
import { AutonomyMetricsClient } from "./supabase/clients/autonomy_metrics_client";

const client = new AutonomyMetricsClient(
  "https://YOUR_PROJECT_ID.supabase.co",
  "YOUR_ANON_KEY"
);

// Send decision event
const result = await client.sendDecisionEvent({
  practiceId: "empirica-autonomy",
  title: "Enable safety gate",
  dimensions: ["truth", "harm"]
});

// Get metrics
const metrics = await client.getMetrics({
  practiceId: "empirica-autonomy"
});
```

---

## Troubleshooting

### "Cannot find project" error

```
Error: Could not find project YOUR_PROJECT_ID
```

**Fix:** Verify project ID is correct:
```bash
supabase status  # Check linked project
```

### "Function deployment failed"

```
Error: Failed to deploy function
```

**Fix:**
1. Ensure Edge Functions are enabled: Supabase dashboard → Functions → Enable
2. Check function file syntax: `supabase functions list`
3. Check logs: `supabase functions logs autonomy-metrics-ingest`

### "Migration failed" error

```
Error: Migration contains syntax errors
```

**Fix:**
1. Verify SQL syntax: Open `supabase/migrations/20260910_autonomy_metrics_schema.sql`
2. Check PostgreSQL version (should be 15+)
3. Run schema manually in SQL Editor if needed

### "401 Unauthorized" on API calls

```
Error: 401 Unauthorized
```

**Fix:**
1. Verify `Authorization: Bearer YOUR_ANON_KEY` header is present
2. Check anon key is correct from Supabase dashboard
3. Ensure RLS policies are enabled

---

## Next Steps

1. **Test ingestion:** Send events from autonomy practices
2. **Monitor metrics:** Query aggregated data via REST API
3. **Set up alerting:** Create Supabase webhooks for critical escalations
4. **Integrate dashboard:** Wire metrics endpoint to dashboard queries

---

## Commands Reference

```bash
# Authentication
supabase login                                    # Log in to Supabase
supabase logout                                   # Log out

# Project management
supabase link --project-ref PROJECT_ID           # Link to remote project
supabase unlink                                   # Unlink project
supabase status                                   # Check project status

# Database migrations
supabase db push                                  # Deploy migration
supabase db pull                                  # Fetch remote schema
supabase db reset                                 # Reset local database

# Edge Functions
supabase functions deploy PATH/TO/FUNCTION       # Deploy function
supabase functions list                          # List deployed functions
supabase functions logs FUNCTION_NAME            # View function logs
supabase functions delete FUNCTION_NAME          # Delete function

# Local development
supabase start                                    # Start local Supabase
supabase stop                                     # Stop local Supabase
```

---

## Support

For issues with Supabase:
- Docs: https://supabase.com/docs
- GitHub: https://github.com/supabase/supabase
- Community: https://discord.supabase.com

---

**Last updated:** 2026-09-10  
**Status:** Ready for deployment
