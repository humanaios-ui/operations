# NF_LEDGER Schema — v1.0 (Unified Calibration Ledger)

**Location:** `ledgers/NF_LEDGER.jsonl` (canonical)  
**Status:** SPECIFICATION (Phase 1, Q-NF-SCHEMA-01)  
**Authority:** Z2 (Night) — ratifies schema changes  
**Enforcement:** Planned CI gate will validate hash chain, append-only, and no overwrites once delivered

---

## Overview

**NF_LEDGER** is the authoritative hash-chained calibration ledger for HumanAIOS. It records:
- Every molt (constant change) and its predicted/actual outcome
- Brier scores per predictor and per constant
- Calibration drift signals (triggers for Molt Cycle wakeup)
- Complete audit trail for receipt reconciliation (B.6)

**Purpose:** Enable the recursive learning function (Molt) to measure whether its predictions hold, and freeze learning when revert-rate exceeds thresholds.

---

## Format Resolution (4 Incompatibilities)

### 1. **nf_ledger_v0_1** → Unified

**Prior format:** Score records only (no prediction/outcome tracking)  
**Unified approach:** Extend to include prediction window, ratification hash, measured outcome

**Migration:** All v0.1 entries converted to v1.0 `record_type="HISTORICAL"` records with:
- `prior_hash`: Recomputed chain link
- `predictor_id`: `"historical_backfill"`
- `prediction`: `{metric: "historical_backfill", probability: 0.5, target_threshold: null, target_direction: "equal", window_days: 0, falsifier: "historical_backfill"}`
- `outcome`: `"HISTORICAL"` (backfill, not part of molt cycle)

### 2. **molt_cycle events** → Unified

**Prior format:** molt_events.jsonl with separate schema  
**Unified approach:** Molt events ARE NF_LEDGER entries (same structure)

**Mapping:**
```
MOLT event → molt_id + constant + prior_value + proposed_value
MEASURE event → window_end timestamp, outcome resolved
KEEP/REVERT event → outcome field set, brier_actual populated
```

**Result:** Single append-only ledger, no separate molt_events.jsonl

### 3. **specimen_intake ledger** → Unified

**Prior format:** specimen_intake_v0.2 tracks N_resolved per claim  
**Unified approach:** Specimen outcomes feed NF_LEDGER as Brier input

**Mapping (continuous outcomes preserved):**
```
Specimen claim → predictor_id + variable + prediction_value + scale_max + binary + confidence
Specimen resolved → actual_value + brier_actual=(prediction_value-normalized_actual)^2 + timestamp=<resolution_date>
```

**Result:** Specimen calibration flows into per-predictor Brier tracking

### 4. **breadcrumbs (trace/audit trail)** → Unified

**Prior format:** Separate audit logs in empirica-foundation-evaluator  
**Unified approach:** Breadcrumbs embedded in NF_LEDGER as optional trace

**Fields added:**
- `breadcrumb`: Optional string naming the decision gate (e.g. "Q-IC030-REPIN-01")
- `session_id`: Session that created the molt (for B.6 receipt matching)
- `z2_ratified_at`: When Z2 ratified (not when measured)

**Result:** Full decision → measurement audit trail in single record

---

## Line Format (JSONL)

Each entry is one line, one complete JSON object. No nested arrays.

```json
{
  "record_type": "MOLT",
  "molt_id": "M-20260916-0001",
  "molt_type": "TIER1",
  "predictor_id": "night",
  "constant": "behavior_spec.json:impact_dial",
  "prior_value": 0.5,
  "proposed_value": 0.55,
  "prior_value_type": "float",
  "prediction": {
    "metric": "Brier",
    "probability": 0.55,
    "target_threshold": 0.15,
    "target_direction": "below",
    "window_days": 7,
    "falsifier": "Brier score >= 0.20 at window close"
  },
  "ratification_hash": "4f0af3cf145f80c8f8e74093031fcef58b98beed6bb4ec6e7ea17aa44f0e5385",
  "z2_ratified_at": "2026-09-16T10:00:00Z",
  "window_start": "2026-09-16T10:00:00Z",
  "window_end": "2026-09-23T00:00:00Z",
  "outcome": "KEEP",
  "brier_actual": 0.14,
  "brier_uncertainty": 0.02,
  "n_predictions_in_window": 47,
  "variable": "impact_dial_brier",
  "prediction_value": 0.55,
  "actual_value": 0.14,
  "scale_max": 1.0,
  "binary": false,
  "confidence": 0.82,
  "timestamp": "2026-09-23T00:00:00Z",
  "prior_hash": "abc123def456...",
  "hash": "def456ghi789...",
  "breadcrumb": "Q-MOLT-04 window close",
  "session_id": "S-091626-01",
  "anti_cascade_check": {
    "open_molt_count": 1,
    "reverts_on_constant": 0,
    "rank_in_queue": 4
  },
  "notes": "Impact dial increased to boost blocker removal. Brier held steady; KEEP."
}
```

---

## Field Definitions

| Field | Type | Required | Description |
|:------|:-----|:---------|:------------|
| `record_type` | string | ✅ | `GENESIS` / `MOLT` / `SPECIMEN` / `HISTORICAL` / `AUDIT` |
| `molt_id` | string | ✅ | Unique identifier: `M-YYYYMMDD-(NNNN\|GENESIS\|SNNN)` |
| `molt_type` | string | ✅ | TIER0 (read-only), TIER1 (constant change), TIER2 (node/edge change) |
| `predictor_id` | string | ✅ | Predictor identity used for per-predictor aggregation |
| `constant` | string | ✅ | What changed: `file:field` path (e.g., `behavior_spec.json:impact_dial`) |
| `prior_value` | any | ✅ | Previous value (before molt) |
| `proposed_value` | any | ✅ | New value (if outcome=KEEP, this becomes prior for next molt) |
| `prior_value_type` | string | ✅ | Type hint: float, int, string, json (for deserial) |
| `prediction` | object | ✅ | {metric, probability, target_threshold, target_direction, window_days, falsifier} |
| `prediction.metric` | string | ✅ | Brier / GAP-closure / catch-rate / drift / custom |
| `prediction.probability` | number | ✅ | Forecast probability `p` used for Brier scoring |
| `prediction.target_threshold` | number/null | ✅ | Numeric threshold for metric success checks |
| `prediction.target_direction` | string | ✅ | below / above / equal |
| `prediction.window_days` | int | ✅ | Measurement window length in days |
| `prediction.falsifier` | string | ✅ | Exact condition that triggers REVERT (one sentence) |
| `ratification_hash` | string | ✅ | Z2 digest: `sha256(<candidate_canonical_json>\|by=Night\|at=<ISO-8601>\|decision=ACCEPT\|signer_role=Z2)` |
| `z2_ratified_at` | string | ✅ | ISO 8601 timestamp when Z2 signed |
| `window_start` | string | ✅ | When measurement window opened |
| `window_end` | string | ✅ | When measurement closes (prediction resolved) |
| `outcome` | string | ✅ | KEEP / REVERT / MEASURING / HISTORICAL |
| `brier_actual` | number | ❌ | Brier score at window close (only if outcome != MEASURING) |
| `brier_uncertainty` | number | ❌ | ±2σ band on brier_actual (calibration confidence) |
| `n_predictions_in_window` | int | ❌ | How many resolution events fed into brier_actual |
| `variable` | string | ❌ | Predicted variable/claim identifier |
| `prediction_value` | number | ❌ | Raw forecast value before normalization |
| `actual_value` | number | ❌ | Observed value used for outcome scoring |
| `scale_max` | number | ❌ | Normalization divisor for continuous outcomes |
| `binary` | bool | ❌ | Whether `actual_value` is binary |
| `confidence` | number | ❌ | Predictor confidence (0..1) |
| `timestamp` | string | ✅ | ISO 8601 when this record was written |
| `prior_hash` | string | ✅ | Hash of previous record (chain anchor) |
| `hash` | string | ✅ | `sha256(canonical_json(record_without_hash))` (sorted keys, UTF-8, no whitespace variance) |
| `breadcrumb` | string | ❌ | Human-readable name for this molt (e.g., "Q-MOLT-04 day 3") |
| `session_id` | string | ❌ | Session that created molt (for B.6 receipt matching) |
| `anti_cascade_check` | object | ✅ | {open_molt_count, reverts_on_constant, rank_in_queue} |
| `notes` | string | ❌ | Optional analyst comment (included in hash once written) |

---

## Anti-Cascade Enforcement (Embedded)

Each NF_LEDGER entry carries `anti_cascade_check`:

```json
{
  "open_molt_count": 1,
  "reverts_on_constant": 0,
  "rank_in_queue": 4
}
```

**CI gate enforcement (planned in gate deliverable):**
- `open_molt_count` ≤ 3 (K=3 rule)
- `reverts_on_constant` ≤ 2 (second revert records terminal freeze trigger)
- Entry REJECT if either violated, and REJECT all subsequent proposals for frozen constants

---

## Brier Skill Score Calculation

For each molt prediction at window close:

```
Brier Skill Score (BSS) = 1 - (BS / BS_baseline)

where:
  BS = (1/N) * Σ(prediction.probability - normalized_actual_outcome)²
  BS_baseline = p_base * (1 - p_base)  [climatological skill]
  p_base = base rate of positive outcome in population
```

**Example:**
- Predicted: 0.55 (impact dial will improve Brier by 5%)
- Actual: 0.14 (Brier improved by 14%)
- Base rate: 0.30 (historical Brier at this constant)
- BS = (0.55 - 1)² = 0.2025
- BS_baseline = 0.30 × 0.70 = 0.21
- BSS = 1 - (0.2025 / 0.21) = 0.035 (slight positive skill)

**Reported in:** NF_LEDGER.brier_actual and in POSTFLIGHT metrics

---

## Append-Only & Hash Chain

**CI validation (planned gate extension):**

```yaml
nf_ledger_hash_chain:
  - Load prior signed commitment (head_hash, line_count) pinned in REGISTERED.md
  - Current ledger tail hash and line count must match that pinned commitment
  - Read ledgers/NF_LEDGER.jsonl up to prior_hash
  - Extract last record: get its hash
  - New entry's prior_hash must == last record's hash
  - Compute hash of canonical new entry (without hash), verify it matches hash field
  - Reject if chain breaks
  - Write next signed commitment with updated (head_hash, line_count)
```

**Result:** Tamper-evident ledger with anchored head/length commitments. Any edit, deletion, or reorder breaks validation.

---

## Molt Cycle Integration

When molt_cycle.py wakes (session open, after VERDICT batch):

```python
# READ phase
nf_ledger = read_append_only("ledgers/NF_LEDGER.jsonl")
brier_per_predictor = aggregate_brier(nf_ledger)
revert_rate = count_reverts(nf_ledger) / count_molts(nf_ledger)

# PROPOSE phase
for constant in CONSTANTS:
  if should_propose_molt(constant, brier_per_predictor, revert_rate):
    emit molt_id, constant, prior, proposed, prediction, falsifier
    # Entry goes to Priority Queue, not NF_LEDGER yet

# RATIFY phase (Z2)
z2_signs_molt_candidate(molt_id, ratification_hash)

# APPLY phase
write_to_nf_ledger(molt_id, ..., outcome="MEASURING")
set_constant(constant, proposed_value, molt_id)
emit MOLT event

# MEASURE phase (at window_end)
measure_outcome = test_falsifier(prediction.falsifier)
append_to_nf_ledger(molt_id, record_type="AUDIT", outcome=measure_outcome, brier_actual=..., timestamp=now, prior_hash=last_hash)

# KEEP/REVERT phase
if outcome == "KEEP":
  emit KEEP event
elif outcome == "REVERT":
  revert_constant(constant, prior_value)
  emit REVERT event
  file F/IC candidate
  check anti_cascade freeze rule
```

---

## Initial Seeding (Sep 16)

When Phase 1 launches, initialize ledgers/NF_LEDGER.jsonl:

1. **Create genesis record** (entry 0):
   ```json
   {
     "record_type": "GENESIS",
     "molt_id": "M-20260916-GENESIS",
     "molt_type": "TIER0",
     "predictor_id": "system",
     "constant": "system:initialized",
     "prior_value": null,
     "proposed_value": "NF_LEDGER v1.0",
     "prior_value_type": "string",
     "prediction": {
       "metric": "genesis_bootstrap",
       "probability": 1.0,
       "target_threshold": null,
       "target_direction": "equal",
       "window_days": 0,
       "falsifier": "genesis_bootstrap"
     },
     "ratification_hash": "<z2_digest>",
     "z2_ratified_at": "2026-09-16T00:00:00Z",
     "window_start": "2026-09-16T00:00:00Z",
     "window_end": "2026-09-16T00:00:00Z",
     "outcome": "KEEP",
     "timestamp": "2026-09-16T00:00:00Z",
     "prior_hash": "0000000000000000000000000000000000000000000000000000000000000000",
     "hash": "<computed>",
     "anti_cascade_check": {"open_molt_count": 0, "reverts_on_constant": 0, "rank_in_queue": 0},
     "notes": "NF_LEDGER schema v1.0 initialized per Phase 1 Q-NF-SCHEMA-01"
   }
   ```

2. **Backfill v0.1 entries** (if any exist):
   - Convert to v1.0 format
   - Set record_type="HISTORICAL", predictor_id="historical_backfill", outcome="HISTORICAL"
   - Populate historical prediction object (metric/probability/threshold/window/falsifier) per migration rules above
   - Compute prior_hash chain

3. **Zero the chain**: prior_hash of genesis = "0" × 64 (no prior)

---

## Success Criteria (Q-NF-SCHEMA-01 DONE)

- ✅ NF_LEDGER_SCHEMA_v1.md published in operations/
- ✅ Unified schema resolves all 4 format incompatibilities at spec level
- ⏳ CI gate update (`z2_ratification_gate.yml`) implemented and merged
- ⏳ `tools/molt_cycle.py` updated to read/write unified records
- ⏳ Brier calculation implementation/tests merged
- ⏳ Genesis record committed to main

**Then:** Q-MOLT-04 unblocks (molt_cycle.py implementation)

---

## Migration Path (Not in scope for Q-NF-SCHEMA-01)

For existing ledgers (specimen_intake, resource_miner, etc.):
- Extract records
- Convert to v1.0 format
- Append to NF_LEDGER with outcome="HISTORICAL"
- Validate chain
- Timestamp: Sep 23 (end of Phase 1)
