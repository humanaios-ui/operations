# NF_LEDGER Event Schema v0.1

**Purpose:** Canonical schema for Brier calibration ledger across nf_ledger_v0_1, molt_cycle, and specimen_intake_evaluator.

**Format:** Append-only JSONL (one JSON object per line); hash-chained via `hash` and `prev_hash` fields.

---

## Event Types

### OPEN (ledger initialization)
Emitted once at ledger creation. Establishes window, resolver, and registered state.

```json
{
  "seq": 1,
  "type": "OPEN",
  "at": "2026-09-05T12:00:00+00:00",
  "by": "Z1",
  "ledger": "NF_LEDGER",
  "version": "v0.1",
  "window": "2026-08-01 to 2026-09-05",
  "source_plan": "...",
  "registered_sha": "42c345bb...",
  "main_sha": "09e1750...",
  "resolver": "molt_cycle",
  "hash": "<SHA256>",
  "prev_hash": "<SHA256>"
}
```

### PIN (forecast issuance)
Emitted when a practice or meta-predictor (Z1, Z2) issues a forecast `p ∈ [0,1]`.

```json
{
  "seq": 2,
  "type": "PIN",
  "at": "2026-09-05T12:00:00+00:00",
  "by": "Z1",
  "pin_id": "T-empirica-outreach-01:Z1",
  "token_id": "T-empirica-outreach-01",
  "target": "T-empirica-outreach-01",
  "predictor": "Z1",
  "p": 0.75,
  "scoreable": false,
  "hash": "<SHA256>",
  "prev_hash": "<SHA256>"
}
```

**Fields:**
- `pin_id`: unique identifier for this forecast (format: `{token_id}:{predictor}`)
- `token_id`: which outcome token this is a forecast for
- `target`: what the forecast is about (usually same as token_id; may differ for aggregates)
- `predictor`: who issued this forecast (Z1, Z2, practice name, or "meta")
- `p`: forecast probability ∈ [0,1]
- `scoreable`: boolean; false until a DATE event by Z2 lands (Z1 pins are never scoreable; Z2 pins become scoreable after DATE)

**Constraints:**
- p must be numeric, ∈ [0,1]; rejected at write-time if not
- scoreable: Z1-pinned forecasts stay false; Z2-pinned forecasts require DATE event to become true

### DATE (Z2 timestamp authorization)
Emitted by Z2 to authorize a forecast's timestamp. Until this event exists, forecasts are VOID for Brier calculation.

```json
{
  "seq": 5,
  "type": "DATE",
  "at": "2026-09-06T10:30:00+00:00",
  "by": "Z2",
  "token_id": "T-empirica-outreach-01",
  "issued_date": "2026-09-05",
  "hash": "<SHA256>",
  "prev_hash": "<SHA256>"
}
```

**Semantics:** Z2 attests that the forecast was genuinely issued on `issued_date`, not backdated.

### RESOLVE (outcome observation)
Emitted when the outcome becomes known. Format: `YES` or `NO` (strings), normalized to `1.0` / `0.0` for Brier.

```json
{
  "seq": 15,
  "type": "RESOLVE",
  "at": "2026-09-10T14:00:00+00:00",
  "by": "Z2",
  "token_id": "T-empirica-outreach-01",
  "outcome": "YES",
  "source": "abc123def... (tree read SHA or file path)",
  "hash": "<SHA256>",
  "prev_hash": "<SHA256>"
}
```

**Fields:**
- `outcome`: "YES" or "NO"; anything else is rejected
- `source`: proof of outcome (tree-read SHA or path); required; no source → refused

**Semantics:** Once a RESOLVE is written, that token is RESOLVED and cannot be resolved again (new DISPUTE event required for corrections).

### STRIKE (dispute / correction)
Emitted to dispute or correct a prior RESOLVE. Creates a new path forward without editing history.

```json
{
  "seq": 16,
  "type": "STRIKE",
  "at": "2026-09-10T15:00:00+00:00",
  "by": "Z2",
  "token_id": "T-empirica-outreach-01",
  "prior_seq": 15,
  "reason": "...",
  "new_outcome": "NO",
  "source": "abc123def...",
  "hash": "<SHA256>",
  "prev_hash": "<SHA256>"
}
```

**Semantics:** Appended as a new event. Ledger readers apply STRIKE to retract the prior RESOLVE and install `new_outcome`.

---

## JOIN: PIN + RESOLVE → Resolved Forecast

**For Brier calculation:**

1. Read all PIN events; group by `token_id`
2. For each token_id, find the latest RESOLVE (by seq)
3. If STRIKE exists for that RESOLVE, apply the correction (use `new_outcome`)
4. If a DATE event exists and `scoreable=true`, pair PIN with RESOLVE:
   - Brier component: `(p - outcome_as_float)²`
   - outcome_as_float: "YES" → 1.0, "NO" → 0.0
5. If no DATE or `scoreable=false`, skip (VOID for scoring)

**SQL-like pseudocode:**

```sql
SELECT 
  p.pin_id,
  p.predictor,
  p.p,
  COALESCE(s.new_outcome, r.outcome) as outcome,
  CAST(CASE COALESCE(s.new_outcome, r.outcome) WHEN 'YES' THEN 1.0 WHEN 'NO' THEN 0.0 END AS FLOAT) as outcome_float,
  POWER(p.p - outcome_float, 2) as brier_component
FROM pin p
LEFT JOIN resolve r ON p.token_id = r.token_id
LEFT JOIN strike s ON r.seq = s.prior_seq
WHERE EXISTS (
  SELECT 1 FROM date d WHERE d.token_id = p.token_id
)
AND p.scoreable = true
```

---

## State Transitions

```
TOKEN issued
  ↓
PIN (by Z1 or Z2)  [scoreable=false if Z1; needs DATE if Z2]
  ↓
DATE (by Z2)       [makes scoreable=true if it was false]
  ↓
RESOLVE (by Z2)    [outcome observed]
  ↓
STRIKE (by Z2)     [optional; corrects prior RESOLVE]
```

---

## Validation Rules

| Rule | Enforced Where |
|------|---|
| Every forecast p ∈ [0,1] | nf_ledger_v0_1.py cmd_build, cmd_resolve (RT-01) |
| outcome ∈ {YES, NO} | nf_ledger_v0_1.py cmd_resolve |
| RESOLVE requires source | nf_ledger_v0_1.py cmd_resolve |
| No double-RESOLVE (append STRIKE instead) | nf_ledger_v0_1.py cmd_resolve |
| Hash chain intact (no edits) | nf_ledger_v0_1.py cmd_verify |
| Scoreable pin requires DATE event | molt_cycle.py JOIN logic |

---

## Ledger Readers

- **molt_cycle.py:** reads PIN + RESOLVE + DATE to compute Brier, detect triggers
- **specimen_intake_evaluator.py:** reads its own PINs and appends RESOLVE events
- **nf_ledger_v0_1.py status:** counts events by type and state
- **nf_ledger_v0_1.py score:** Brier per predictor over resolved, scoreable forecasts

