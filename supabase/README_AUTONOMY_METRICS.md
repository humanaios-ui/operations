# Autonomy Metrics — Telemetry Pipeline & REST API

**Status:** DEPLOYED  
**Date:** 2026-09-10  
**Schema Version:** 1.0

---

## Overview

The Autonomy Metrics system provides real-time telemetry for HumanAIOS decision-making, escalation tracking, and practice-level aggregation. It captures every autonomy decision event, tracks escalations with SLA monitoring, and exposes aggregated metrics via REST API for dashboards and reporting.

**Key capabilities:**
- Per-event decision telemetry (proposals, approvals, executions)
- Escalation tracking with SLA compliance monitoring
- Aggregated metrics for dashboard queries (hourly/daily)
- REST API for metrics, escalations, decision statistics
- Row-level security (RLS) for data access control
- Audit trail for all decision changes

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Event Ingestion (POST /autonomy-metrics/ingest)       │
│  Accepts: autonomy events (decisions, escalations)      │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│  PostgreSQL Tables (supabase)                          │
│  ├─ autonomy.events (core event log)                   │
│  ├─ autonomy.decisions (proposals & outcomes)          │
│  ├─ autonomy.escalations (escalation log, SLA)         │
│  ├─ autonomy.metrics (aggregated, hourly/daily)        │
│  └─ autonomy.decision_audit (immutable changes)        │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│  Metrics Queries (GET /autonomy-metrics/metrics)       │
│  ├─ Endpoint: metrics → aggregated metrics data        │
│  ├─ Endpoint: escalations → open/resolved              │
│  └─ Endpoint: decisions → approval/execution rates     │
└─────────────────────────────────────────────────────────┘
```

---

## Schema

### 1. autonomy.events (Core Event Log)

Captures every autonomy decision, escalation, or system event.

```sql
CREATE TABLE autonomy.events (
  id BIGSERIAL PRIMARY KEY,
  event_id TEXT NOT NULL UNIQUE,     -- Globally unique (evt-XXX)
  timestamp TIMESTAMPTZ,             -- When event occurred
  practice_id TEXT NOT NULL,         -- Which practice emitted
  event_type TEXT,                   -- 'decision', 'escalation', 'gate_transition'
  dimension TEXT,                    -- Optional: which dimension affected
  channel TEXT,                      -- Event channel (decision_proposal, escalation_alert)
  payload JSONB,                     -- Event-specific data
  metrics JSONB,                     -- Computed metrics
  source_gate TEXT,                  -- Which gate/module emitted
  parent_event_id TEXT,              -- Link to related event
  tags TEXT[],                       -- Event tags
  created_by TEXT,                   -- AI identity or system user
  updated_at TIMESTAMPTZ
);
```

**Indexes:**
- `timestamp DESC` (chronological queries)
- `practice_id` (per-practice rollups)
- `event_type` (filtering by type)
- `dimension` (dimension-specific analysis)
- `parent_event_id` (event chain traversal)

### 2. autonomy.decisions (Decision Metadata & Outcomes)

Tracks decision proposals, approvals, and execution outcomes.

```sql
CREATE TABLE autonomy.decisions (
  id BIGSERIAL PRIMARY KEY,
  decision_id TEXT UNIQUE,           -- Unique ID (dec-XXX)
  event_id TEXT,                     -- Link to event
  timestamp TIMESTAMPTZ,
  practice_id TEXT,                  -- Where decision was made
  proposal_title TEXT,               -- Short description
  proposal_body TEXT,                -- Full justification
  status TEXT,                       -- 'proposed', 'approved', 'rejected', 'executed'
  approved_by TEXT,                  -- Who approved
  executed BOOLEAN,                  -- Was it executed?
  execution_sha TEXT,                -- Git commit SHA if applicable
  outcome_impact NUMERIC(3,2),       -- Impact score (0.0-1.0)
  parent_decision_id TEXT,           -- Related decision
  created_by TEXT,
  updated_at TIMESTAMPTZ
);
```

**Status lifecycle:** `proposed` → `approved` → `executed` (or `rejected`, `escalated`)

### 3. autonomy.escalations (Escalation Tracking)

Records escalations, why they occurred, and resolution.

```sql
CREATE TABLE autonomy.escalations (
  id BIGSERIAL PRIMARY KEY,
  escalation_id TEXT UNIQUE,         -- Unique ID (esc-XXX)
  event_id TEXT,                     -- Link to event
  timestamp TIMESTAMPTZ,
  practice_id TEXT,                  -- Originating practice
  reason TEXT,                       -- Why escalation occurred
  severity TEXT,                     -- 'low', 'medium', 'high', 'critical'
  source_decision_id TEXT,           -- What decision triggered it
  escalated_to TEXT,                 -- Target (mesh-support, admiral, ECO)
  status TEXT,                       -- 'open', 'acknowledged', 'in_review', 'resolved'
  resolved_by TEXT,                  -- Who resolved
  resolution_note TEXT,
  sla_seconds INTEGER,               -- Target resolution time
  actual_seconds INTEGER,            -- Actual resolution time
  sla_met BOOLEAN,                   -- SLA compliance
  created_by TEXT,
  updated_at TIMESTAMPTZ
);
```

**SLA tracking:** `sla_seconds` vs. `actual_seconds` for compliance monitoring.

### 4. autonomy.metrics (Aggregated Metrics)

Materialized summary for fast dashboard queries (updated hourly/daily).

```sql
CREATE TABLE autonomy.metrics (
  id BIGSERIAL PRIMARY KEY,
  metric_date DATE,                  -- Which date
  metric_hour SMALLINT,              -- Which hour (0-23), NULL for daily
  practice_id TEXT,                  -- NULL = system-wide
  dimension TEXT,                    -- NULL = all dimensions
  events_total BIGINT,
  decisions_proposed BIGINT,
  decisions_approved BIGINT,
  decisions_executed BIGINT,
  escalations_open BIGINT,
  escalations_resolved BIGINT,
  escalation_rate_per_1k NUMERIC,    -- Per 1000 decisions
  approval_rate NUMERIC(3,2),        -- 0.0-1.0
  execution_rate NUMERIC(3,2),       -- 0.0-1.0
  escalation_sla_met_count BIGINT,
  escalation_sla_missed_count BIGINT,
  avg_sla_response_seconds NUMERIC,
  created_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ
);
```

**Unique constraint:** `(metric_date, metric_hour, practice_id, dimension)`

### 5. autonomy.decision_audit (Immutable Audit Trail)

Immutable log of every decision change.

```sql
CREATE TABLE autonomy.decision_audit (
  id BIGSERIAL PRIMARY KEY,
  decision_id TEXT,                  -- Which decision
  timestamp TIMESTAMPTZ,
  actor TEXT,                        -- Who made change
  action TEXT,                       -- 'created', 'approved', 'rejected', 'executed'
  old_status TEXT,
  new_status TEXT,
  note TEXT,                         -- Why
  metadata JSONB                     -- Extra context
);
```

---

## API Endpoints

### 1. Event Ingestion

**POST** `/functions/v1/autonomy-metrics/ingest`

Ingest a new autonomy event.

**Request:**
```json
{
  "event_id": "evt-001",
  "practice_id": "empirica-autonomy",
  "event_type": "decision",
  "dimension": "truth",
  "channel": "decision_proposal",
  "payload": {
    "proposal_title": "Enable autonomy gate for Phase 3",
    "decision_scope": "cross-practice",
    "confidence": 0.85
  },
  "metrics": {
    "processing_time_ms": 42
  },
  "source_gate": "autonomy_gate.py",
  "tags": ["phase-3", "high-impact"]
}
```

**Response:**
```json
{
  "ok": true,
  "event_id": "evt-001"
}
```

**Status codes:**
- `201` — Event created
- `400` — Missing required fields (event_id, practice_id, event_type, channel)
- `500` — Internal error

**Required fields:**
- `event_id` — Globally unique identifier
- `practice_id` — Which practice emitted
- `event_type` — one of: decision, escalation, gate_transition, blocker
- `channel` — Event channel (decision_proposal, escalation_alert, etc.)

---

### 2. Metrics Query

**GET** `/functions/v1/autonomy-metrics/metrics`

Fetch aggregated autonomy metrics.

**Query parameters:**
- `endpoint` — Which endpoint (default: `metrics`)
  - `metrics` — Aggregated metrics
  - `escalations` — Escalation list
  - `decisions` — Decision statistics
- `practice_id` (optional) — Filter by practice
- `dimension` (optional) — Filter by dimension
- `start_date` (optional) — Start date (YYYY-MM-DD, default: 7 days ago)
- `end_date` (optional) — End date (YYYY-MM-DD, default: today)
- `granularity` (optional) — `hourly` or `daily` (default: `daily`)
- `limit` (optional) — Max results for escalations endpoint (default: 50)

**Examples:**

```bash
# Get system-wide metrics for the last 7 days
curl "https://your-project.supabase.co/functions/v1/autonomy-metrics/metrics"

# Get metrics for one practice, one dimension
curl "https://your-project.supabase.co/functions/v1/autonomy-metrics/metrics?practice_id=empirica-autonomy&dimension=truth"

# Get open escalations
curl "https://your-project.supabase.co/functions/v1/autonomy-metrics/metrics?endpoint=escalations&limit=20"

# Get decision approval/execution rates
curl "https://your-project.supabase.co/functions/v1/autonomy-metrics/metrics?endpoint=decisions"
```

**Response (metrics endpoint):**
```json
{
  "ok": true,
  "metrics": [
    {
      "metric_date": "2026-09-10",
      "metric_hour": null,
      "practice_id": null,
      "dimension": null,
      "events_total": 147,
      "decisions_proposed": 23,
      "decisions_approved": 19,
      "decisions_executed": 15,
      "escalations_open": 2,
      "escalations_resolved": 3,
      "escalation_rate_per_1k": 217.39,
      "approval_rate": 0.826,
      "execution_rate": 0.789,
      "escalation_sla_met_count": 2,
      "escalation_sla_missed_count": 1,
      "avg_sla_response_seconds": 3600
    }
  ]
}
```

**Response (escalations endpoint):**
```json
{
  "ok": true,
  "escalations": [
    {
      "escalation_id": "esc-001",
      "timestamp": "2026-09-10T14:32:00Z",
      "practice_id": "empirica-autonomy",
      "reason": "cross-practice impact",
      "severity": "high",
      "status": "open",
      "escalated_to": "mesh-support",
      "sla_seconds": 7200,
      "actual_seconds": 1800,
      "sla_met": true
    }
  ]
}
```

**Response (decisions endpoint):**
```json
{
  "ok": true,
  "decision_stats": {
    "total_decisions": 50,
    "proposed": 10,
    "approved": 8,
    "approval_rate": 80.0,
    "executed": 6,
    "execution_rate": 75.0
  }
}
```

---

## Data Access & Security

### Row-Level Security (RLS)

All tables have RLS enabled. Policies:
- **Read policy:** Authenticated users can read data
- **Insert policy:** Service role (backend) can insert events
- **Update policy:** Only the creator or admin can update

### Authentication

- **Ingestion (POST):** Requires `Authorization: Bearer <SUPABASE_ANON_KEY>` or service role
- **Queries (GET):** No auth required for metrics endpoint (read-only, aggregated data)

### API Key Management

Set these environment variables in Supabase Edge Functions:
- `SUPABASE_URL` — Your project URL
- `SUPABASE_SERVICE_ROLE_KEY` — Service role key (for backend writes)

---

## Deployment

### Prerequisites

- Supabase project (free or paid tier)
- Supabase CLI (`supabase` CLI installed)

### 1. Deploy Schema Migration

```bash
supabase migration up
```

Or manually via Supabase dashboard:
1. Go to SQL Editor
2. Paste contents of `migrations/20260910_autonomy_metrics_schema.sql`
3. Run

### 2. Deploy Edge Functions

```bash
supabase functions deploy autonomy-metrics/ingest
supabase functions deploy autonomy-metrics/metrics
```

Or via Supabase dashboard:
1. Functions → Create Function
2. Copy code from `functions/autonomy-metrics/ingest.ts`
3. Deploy

### 3. Set Environment Variables

In Supabase dashboard → Settings → Functions:
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

---

## Usage Examples

### Sending Decision Telemetry

```typescript
// From an AI practice or autonomy gate
const event = {
  event_id: "evt-" + Date.now(),
  practice_id: "empirica-autonomy",
  event_type: "decision",
  dimension: "truth",
  channel: "decision_proposal",
  payload: {
    proposal_title: "Enable new safety gate",
    scope: "system-wide",
  },
  created_by: "empirica-autonomy",
};

const response = await fetch("/.netlify/functions/autonomy-metrics/ingest", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(event),
});
```

### Fetching Dashboard Metrics

```typescript
// Get system-wide metrics
const res = await fetch("/.netlify/functions/autonomy-metrics/metrics?granularity=daily");
const { metrics } = await res.json();

// Plot approval/execution rates over time
console.log(
  metrics.map((m) => ({
    date: m.metric_date,
    approval_rate: m.approval_rate,
    execution_rate: m.execution_rate,
  }))
);
```

### Monitoring Escalations

```typescript
// Get open escalations
const res = await fetch("/.netlify/functions/autonomy-metrics/metrics?endpoint=escalations&limit=10");
const { escalations } = await res.json();

// Alert if critical
escalations
  .filter((e) => e.severity === "critical" && e.status === "open")
  .forEach((e) => console.warn("CRITICAL:", e.escalation_id, e.reason));
```

---

## Metrics Definition

### Event Types

| Type | Purpose | Example |
|------|---------|---------|
| `decision` | Decision proposal/approval/execution | Enabling a new safety gate |
| `escalation` | Escalation triggered | Cross-practice impact detected |
| `gate_transition` | State change in a gate/checker | Gate moved from PROPOSED to APPROVED |
| `blocker` | System blocker detected | Dependency not available |

### Dimensions

Mapped from ACAT 6-dimension behavioral instrument:
- `truth` — Accuracy, grounding
- `service` — Alignment with user needs
- `harm` — Safety considerations
- `autonomy` — Decision-making authority
- `value` — Alignment with values
- `humility` — Uncertainty/confidence calibration

### Channels

| Channel | Triggered by | Context |
|---------|--------------|---------|
| `decision_proposal` | New decision proposed | Autonomy gate evaluation |
| `decision_approved` | Decision approved | ECO acceptance |
| `decision_executed` | Decision implemented | Code committed, deployed |
| `escalation_alert` | Decision escalated | Cross-practice impact |
| `gate_transition` | Gate state change | mason_gate.py transitions |

---

## Monitoring & Alerts

### Key Metrics to Monitor

1. **Approval rate** (`approval_rate`) — Should be stable, 70-90%
2. **Execution rate** (`execution_rate`) — Should increase over time as decisions land
3. **Escalation rate** (`escalation_rate_per_1k`) — Should decrease as protocols mature
4. **SLA compliance** (`escalation_sla_met_count` / total) — Should be >95%

### SLA Thresholds

| Severity | Target SLA | Response time |
|----------|-----------|---|
| Critical | 1 hour | < 3600s |
| High | 4 hours | < 14400s |
| Medium | 24 hours | < 86400s |
| Low | 48 hours | < 172800s |

---

## Troubleshooting

### Events not appearing

1. Check function logs: Supabase dashboard → Functions → View logs
2. Verify auth: Ensure `SUPABASE_SERVICE_ROLE_KEY` is set
3. Validate schema: Confirm tables exist in SQL Editor

### Metrics not aggregating

1. Check that events are being inserted (query `autonomy.events`)
2. Verify materialized view trigger exists
3. Manually run aggregation: `SELECT * FROM autonomy.metrics`

### Access denied errors

1. Enable RLS in Supabase dashboard
2. Check policies on each table
3. Ensure caller has correct role (anon vs. service)

---

## Future Enhancements

- [ ] Materialized view auto-refresh (scheduled job for metrics aggregation)
- [ ] Prometheus metrics export for monitoring dashboards
- [ ] Webhook notifications for critical escalations
- [ ] Decision impact analysis (correlate outcome_impact with business metrics)
- [ ] Anomaly detection (ML model for escalation rate prediction)

---

## References

- Supabase Docs: https://supabase.com/docs
- PostgreSQL JSON: https://www.postgresql.org/docs/current/datatype-json.html
- Row-Level Security: https://supabase.com/docs/guides/auth/row-level-security
- Edge Functions: https://supabase.com/docs/guides/functions

---

**Last updated:** 2026-09-10  
**Maintained by:** empirica-outreach (via mesh-support)  
**Schema version:** 1.0
