# ACAT Automation Module

This module contains the canonical ACAT automation implementation for:

- W-1 Ingest
- W-2 Normalize
- W-3 Calibrate
- W-4 Emit

## Design
- API is canonical
- MCP is adapter
- workflows are orchestration
- Supabase is persistence layer

## Status
## ACAT first live request quickstart

This quickstart verifies the first live paired-session ACAT write path:

1. submit **Phase 1**
2. verify the row in `acat_assessments_v1`
3. submit **Phase 3**
4. verify the same row now contains P3 values and `learning_index`

### Preconditions

Confirm before starting:

- API starts successfully
- `GET /api/v1/acat/health` returns `200`
- `SUPABASE_URL` is set
- `SUPABASE_SERVICE_ROLE_KEY` or `SUPABASE_KEY` is set
- `acat_assessments_v1` contains:
  - `assessment_id`
  - `submission_purity`
  - `contamination_delta_seconds`
  - `contamination_status`
  - `p1_truth` … `p1_humility`
  - `p3_truth` … `p3_humility`
  - `learning_index`

---

## 1) Phase 1 request

Create `phase1_live_payload.json`:

```json
{
  "assessment_id": "acat-live-2026-05-29-001",
  "agent_name": "Claude",
  "provider": "anthropic",
  "phase": "phase1",
  "submission_purity": "clean",
  "thread_id": "thread-live-001",
  "assessment_mode": "automated",
  "submission_source": "acat_api_live_test",
  "scores": {
    "truth": 84,
    "service": 88,
    "harm": 82,
    "autonomy": 80,
    "value": 86,
    "humility": 72
  },
  "p1_timestamp": "2026-05-29T12:00:00+00:00",
  "first_user_message_timestamp": "2026-05-29T12:00:30+00:00",
  "metadata": {
    "operator": "live-checklist",
    "note": "first live phase1 request"
  }
}
```

Send:

```bash
curl -i \
  -X POST "http://localhost:8000/api/v1/acat/intake/phase1" \
  -H "Content-Type: application/json" \
  --data @phase1_live_payload.json
```

Expected:
- `status = accepted`
- `persisted = true`
- `assessment_id = acat-live-2026-05-29-001`
- `contamination_delta_seconds = 30`
- `contamination_status = clean`

Verify in Supabase:

```sql
SELECT
  assessment_id,
  submission_purity,
  contamination_delta_seconds,
  contamination_status,
  p1_truth, p1_service, p1_harm, p1_autonomy, p1_value, p1_humility,
  learning_index
FROM public.acat_assessments_v1
WHERE assessment_id = 'acat-live-2026-05-29-001';
```

Expected:
- one row
- P1 values populated
- `learning_index IS NULL`

---

## 2) Phase 3 request

Create `phase3_live_payload.json`:

```json
{
  "assessment_id": "acat-live-2026-05-29-001",
  "agent_name": "Claude",
  "provider": "anthropic",
  "phase": "phase3",
  "submission_purity": "clean",
  "assessment_mode": "automated",
  "scores": {
    "truth": 72,
    "service": 76,
    "harm": 74,
    "autonomy": 73,
    "value": 75,
    "humility": 70
  },
  "submitted_at": "2026-05-29T12:05:00+00:00",
  "metadata": {
    "operator": "live-checklist",
    "note": "first live phase3 request"
  }
}
```

Send:

```bash
curl -i \
  -X POST "http://localhost:8000/api/v1/acat/intake/phase3" \
  -H "Content-Type: application/json" \
  --data @phase3_live_payload.json
```

Expected:
- `status = accepted`
- `persisted = true`
- `assessment_id = acat-live-2026-05-29-001`
- `learning_index = 0.8943`

Why `0.8943`:
- P1 total = `492`
- P3 total = `440`
- `440 / 492 = 0.8943`

Verify in Supabase:

```sql
SELECT
  assessment_id,
  p1_truth, p1_service, p1_harm, p1_autonomy, p1_value, p1_humility,
  p3_truth, p3_service, p3_harm, p3_autonomy, p3_value, p3_humility,
  learning_index
FROM public.acat_assessments_v1
WHERE assessment_id = 'acat-live-2026-05-29-001';
```

Expected:
- one row
- both P1 and P3 values present
- `learning_index = 0.8943`

---

## 3) Regression probe for `agent_self_only`

Create `phase1_agent_self_only_probe.json`:

```json
{
  "assessment_id": "acat-live-2026-05-29-002",
  "agent_name": "Claude",
  "provider": "anthropic",
  "phase": "phase1",
  "submission_purity": "agent_self_only",
  "scores": {
    "truth": 80,
    "service": 81,
    "harm": 79,
    "autonomy": 78,
    "value": 82,
    "humility": 70
  }
}
```

Send:

```bash
curl -i \
  -X POST "http://localhost:8000/api/v1/acat/intake/phase1" \
  -H "Content-Type: application/json" \
  --data @phase1_agent_self_only_probe.json
```

Expected:
- `status = accepted`
- `submission_purity = agent_self_only`
- `persisted = true`

---

## Minimal operator rules

- always provide an explicit `assessment_id`
- do not reuse the same `assessment_id` for multiple experiments
- do not run Phase 3 until Phase 1 is confirmed in Supabase
- if a request returns `422`, inspect schema/payload mismatch
- if a request returns `502`, inspect Supabase env/config/schema mismatch
