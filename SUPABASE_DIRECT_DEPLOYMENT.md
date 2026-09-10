# Supabase Autonomy Metrics Deployment — Direct API Method

**Project ID:** `ksinisdzgtnqzsymhfya`  
**Project URL:** https://ksinisdzgtnqzsymhfya.supabase.co

---

## Method 1: Deploy via Supabase Dashboard (Fastest)

### Step 1: Open SQL Editor

1. Go to https://app.supabase.com
2. Select project `ksinisdzgtnqzsymhfya`
3. Click **SQL Editor** (left sidebar)
4. Click **New Query**

### Step 2: Paste Schema Migration

Copy the entire contents of `supabase/migrations/20260910_autonomy_metrics_schema.sql` and paste into the SQL editor.

Click **Run** (or Cmd+Enter).

**Expected output:**
```
Query executed successfully
Affected rows: 0
```

### Step 3: Verify Schema

In SQL Editor, run:

```sql
SELECT table_name FROM information_schema.tables WHERE table_schema = 'autonomy';
```

You should see:
- autonomy_events
- autonomy_decisions
- autonomy_escalations
- autonomy_metrics
- autonomy_decision_audit

### Step 4: Deploy Edge Functions

1. Click **Edge Functions** (left sidebar)
2. Click **Create a new function**

**Function 1: autonomy-metrics-ingest**
- Name: `autonomy-metrics-ingest`
- Copy code from `supabase/functions/autonomy-metrics/ingest.ts`
- Click **Deploy**

**Function 2: autonomy-metrics-metrics**
- Name: `autonomy-metrics-metrics`
- Copy code from `supabase/functions/autonomy-metrics/metrics.ts`
- Click **Deploy**

### Step 5: Get API Keys

1. Click **Settings** → **API**
2. Copy:
   - **Project URL:** https://ksinisdzgtnqzsymhfya.supabase.co
   - **anon public key** (for frontend/SDK use)
   - **service_role secret** (for backend)

---

## Method 2: Deploy via Supabase API (Programmatic)

### Prerequisites

```bash
export SUPABASE_URL="https://ksinisdzgtnqzsymhfya.supabase.co"
export SUPABASE_API_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtzaW5pc2R6Z3RucXpzeW1oZnlhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQzMDEzMzEsImV4cCI6MjA4OTg3NzMzMX0.2M9uE_JQOeDPy8obGweyNlPNMiJoISSf3xx4qeYbUU8"
export SUPABASE_SERVICE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtzaW5pc2R6Z3RucXpzeW1oZnlhIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NDMwMTMzMSwiZXhwIjoyMDg5ODc3MzMxfQ.24f2g9ZPHZCL2McBRepnDQZounv7JUxYDKanr0BmScg"
```

### Deploy Schema via RPC

Execute the SQL migration directly:

```bash
curl -X POST "$SUPABASE_URL/rest/v1/rpc/exec_sql" \
  -H "Authorization: Bearer $SUPABASE_SERVICE_KEY" \
  -H "apikey: $SUPABASE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"sql": "'"$(cat supabase/migrations/20260910_autonomy_metrics_schema.sql | sed "s/\"/\\\\\"/")"'"}'
```

### Deploy Edge Functions via API

**Function 1: ingest**

```bash
curl -X POST "$SUPABASE_URL/functions/v1/autonomy-metrics-ingest" \
  -H "Authorization: Bearer $SUPABASE_SERVICE_KEY" \
  -H "Content-Type: text/plain" \
  --data-binary @supabase/functions/autonomy-metrics/ingest.ts
```

**Function 2: metrics**

```bash
curl -X POST "$SUPABASE_URL/functions/v1/autonomy-metrics-metrics" \
  -H "Authorization: Bearer $SUPABASE_SERVICE_KEY" \
  -H "Content-Type: text/plain" \
  --data-binary @supabase/functions/autonomy-metrics/metrics.ts
```

---

## Method 3: Python Script Deployment

```python
import os
import requests
from pathlib import Path

SUPABASE_URL = "https://ksinisdzgtnqzsymhfya.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
SUPABASE_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

headers = {
    "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
    "apikey": SUPABASE_API_KEY,
    "Content-Type": "application/json"
}

# Deploy schema
with open("supabase/migrations/20260910_autonomy_metrics_schema.sql") as f:
    schema_sql = f.read()

response = requests.post(
    f"{SUPABASE_URL}/rest/v1/rpc/exec_sql",
    headers=headers,
    json={"sql": schema_sql}
)
print(f"Schema deploy: {response.status_code}")
print(response.text)

# Deploy functions
for func_name in ["ingest", "metrics"]:
    func_path = f"supabase/functions/autonomy-metrics/{func_name}.ts"
    with open(func_path) as f:
        func_code = f.read()
    
    response = requests.post(
        f"{SUPABASE_URL}/functions/v1/autonomy-metrics-{func_name}",
        headers=headers,
        data=func_code,
        headers={**headers, "Content-Type": "text/plain"}
    )
    print(f"Deploy {func_name}: {response.status_code}")
```

---

## Verify Deployment

### Test Schema

```bash
# Query via REST API
curl "$SUPABASE_URL/rest/v1/autonomy.events?select=*" \
  -H "Authorization: Bearer $SUPABASE_API_KEY" \
  -H "apikey: $SUPABASE_API_KEY"
```

**Expected:** Empty array `[]` (no events yet)

### Test Event Ingestion

```bash
curl -X POST "$SUPABASE_URL/functions/v1/autonomy-metrics/ingest" \
  -H "Authorization: Bearer $SUPABASE_API_KEY" \
  -H "apikey: $SUPABASE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "evt-test-001",
    "practice_id": "test-practice",
    "event_type": "decision",
    "channel": "decision_proposal",
    "payload": {"proposal_title": "Test"}
  }'
```

**Expected response:**
```json
{"ok": true, "event_id": "evt-test-001"}
```

### Test Metrics Query

```bash
curl "$SUPABASE_URL/functions/v1/autonomy-metrics/metrics" \
  -H "Authorization: Bearer $SUPABASE_API_KEY" \
  -H "apikey: $SUPABASE_API_KEY"
```

**Expected response:**
```json
{"ok": true, "metrics": [...]}
```

---

## SDK Usage

With credentials configured:

### Python

```python
from supabase.clients.autonomy_metrics_client import AutonomyMetricsClient

client = AutonomyMetricsClient(
    supabase_url="https://ksinisdzgtnqzsymhfya.supabase.co",
    anon_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
)

# Send decision event
await client.send_decision_event(
    practice_id="empirica-autonomy",
    title="Enable safety gate",
    confidence=0.85
)

# Fetch metrics
metrics = await client.get_metrics(practice_id="empirica-autonomy")
```

### TypeScript

```typescript
import { AutonomyMetricsClient } from "./supabase/clients/autonomy_metrics_client";

const client = new AutonomyMetricsClient(
  "https://ksinisdzgtnqzsymhfya.supabase.co",
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
);

await client.sendDecisionEvent({
  practiceId: "empirica-autonomy",
  title: "Enable safety gate"
});

const metrics = await client.getMetrics({
  practiceId: "empirica-autonomy"
});
```

---

## Credentials

These are from `~/.empirica/credentials.yaml`:

| Key | Value |
|-----|-------|
| **Project URL** | https://ksinisdzgtnqzsymhfya.supabase.co |
| **Project ID** | ksinisdzgtnqzsymhfya |
| **Anon Key** | eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtzaW5pc2R6Z3RucXpzeW1oZnlhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQzMDEzMzEsImV4cCI6MjA4OTg3NzMzMX0.2M9uE_JQOeDPy8obGweyNlPNMiJoISSf3xx4qeYbUU8 |
| **Service Role** | eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtzaW5pc2R6Z3RucXpzeW1oZnlhIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NDMwMTMzMSwiZXhwIjoyMDg5ODc3MzMxfQ.24f2g9ZPHZCL2McBRepnDQZounv7JUxYDKanr0BmScg |

---

## Next Steps

1. **Dashboard deployment** (fastest): SQL Editor → paste schema → run
2. **Add secrets** to environment or CI/CD pipeline
3. **Test endpoints** with curl or SDK
4. **Integrate with practices** to start sending metrics
5. **Monitor dashboard** for incoming events

---

**Status:** Ready for deployment  
**Last updated:** 2026-09-10
