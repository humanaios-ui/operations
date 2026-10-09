# MOLT Measurement Manual Extraction Procedure
## Blockchain Trading Pilot (Z-012) — Window Closes 2026-09-28 00:00 UTC

**Purpose:** Step-by-step guide for Z2 to extract measurement data and evaluate falsifier for Q-BLOCKCHAIN-TRADING-CALIBRATION-W90PD1-MOL-001.

**Molt Context:**
- **Molt ID:** Q-BLOCKCHAIN-TRADING-CALIBRATION-W90PD1-MOL-001
- **Constant:** trading_spec.json:rebalance_threshold (0.50 → 0.55)
- **Window:** 2026-09-21 00:00 UTC to 2026-09-28 00:00 UTC (7 days)
- **Falsifier:** `Sharpe < 0.80 OR realized_drawdown > 5%`
- **Status:** MEASURING (awaiting measurement result)

---

## §1: Data Collection (Pre-Window-Close)

### 1.1 Identify Data Sources

The blockchain trading pilot generated transaction/position data during the measurement window. Sharpe ratio and maximum drawdown must be extracted from:

- **Source 1:** Blockchain settlement ledger (trades executed with threshold 0.55)
  - Period: 2026-09-21 to 2026-09-28
  - Records: Transaction timestamps, entry prices, exit prices, position sizes

- **Source 2:** Market price data (for Sharpe baseline)
  - Same 7-day period
  - Asset pair(s) in scope (if multi-pair, specify)
  - Frequency: Daily or intra-day (as recorded in settlement data)

### 1.2 Extract Portfolio Returns

From blockchain settlement records, calculate daily returns:

```
daily_return[t] = (portfolio_value[t] - portfolio_value[t-1]) / portfolio_value[t-1]
```

**Example calculations (if available):**
```
2026-09-21: +0.0045 (+0.45%)
2026-09-22: -0.0012 (-0.12%)
2026-09-23: +0.0089 (+0.89%)
2026-09-24: +0.0021 (+0.21%)
2026-09-25: -0.0003 (-0.03%)
2026-09-26: +0.0156 (+1.56%)
2026-09-27: +0.0034 (+0.34%)
```

---

## §2: Falsifier Evaluation

### 2.1 Calculate Sharpe Ratio

**Formula:**
```
Sharpe = mean(daily_returns) / std(daily_returns)
```

Using risk-free rate = 0% (conservative; ignores Treasury baseline):

```python
import numpy as np

returns = [0.0045, -0.0012, 0.0089, 0.0021, -0.0003, 0.0156, 0.0034]
mean_return = np.mean(returns)           # Arithmetic mean of daily returns
std_return = np.std(returns, ddof=1)     # Sample std dev (Bessel correction)
sharpe = mean_return / std_return

# Expected result: Sharpe ≈ [calculate]
```

**Interpretation:**
- If Sharpe ≥ 0.80: First condition **PASS** ✓
- If Sharpe < 0.80: First condition **FAIL** ✗

**Note on annualization:** Falsifier specifies raw 7-day Sharpe, NOT annualized. Do not multiply by √252. Report as calculated.

### 2.2 Calculate Realized Maximum Drawdown

**Definition:** Maximum peak-to-trough decline over the window.

```
drawdown[t] = (portfolio_value[t] - running_peak) / running_peak

max_drawdown = min(drawdown)  # Most negative value
realized_drawdown = abs(max_drawdown)
```

**Example:**
```
Peak portfolio value: $100,000 (2026-09-26 close)
Trough value: $95,000 (2026-09-27 intraday)
Drawdown = ($95,000 - $100,000) / $100,000 = -5.0%
Realized Drawdown = 5.0%
```

**Interpretation:**
- If realized_drawdown ≤ 5%: Second condition **PASS** ✓
- If realized_drawdown > 5%: Second condition **FAIL** ✗

### 2.3 Evaluate Falsifier

**Falsifier Logic (Boolean AND):**
```
falsifier_result = (Sharpe < 0.80) OR (realized_drawdown > 5%)
```

**Truth table:**

| Sharpe | Drawdown | Falsifier Result | Molt Outcome |
|:-------|:---------|:-----------------|:-------------|
| ≥ 0.80 | ≤ 5%     | FALSE (no trip)  | **KEEP**     |
| < 0.80 | ≤ 5%     | TRUE (trip)      | **REVERT**   |
| ≥ 0.80 | > 5%     | TRUE (trip)      | **REVERT**   |
| < 0.80 | > 5%     | TRUE (trip)      | **REVERT**   |

---

## §3: Update molt_ledger.jsonl

Once falsifier is evaluated, update the molt entry with outcome and actual Sharpe:

### 3.1 Edit molt_ledger.jsonl

**Current entry (before measurement):**
```json
{
  "molt_id": "Q-BLOCKCHAIN-TRADING-CALIBRATION-W90PD1-MOL-001",
  ...
  "outcome": "MEASURING",
  "brier_actual": null,
  ...
}
```

**After measurement (if KEEP):**
```json
{
  "molt_id": "Q-BLOCKCHAIN-TRADING-CALIBRATION-W90PD1-MOL-001",
  ...
  "outcome": "KEEP",
  "brier_actual": 0.82,           # Actual Sharpe ratio
  "measurement_timestamp": "2026-09-28T00:15:00Z",
  "measured_by": "carly.r.anderson@gmail.com",
  "measurement_data": {
    "sharpe_ratio": 0.82,
    "realized_drawdown": 0.034,     # 3.4%
    "window_start": "2026-09-21T00:00:00Z",
    "window_end": "2026-09-28T00:00:00Z",
    "falsifier_passed": true
  },
  ...
}
```

**After measurement (if REVERT):**
```json
{
  "molt_id": "Q-BLOCKCHAIN-TRADING-CALIBRATION-W90PD1-MOL-001",
  ...
  "outcome": "REVERT",
  "brier_actual": 0.62,           # Actual Sharpe ratio (below threshold)
  "measurement_timestamp": "2026-09-28T00:15:00Z",
  "measured_by": "carly.r.anderson@gmail.com",
  "measurement_data": {
    "sharpe_ratio": 0.62,
    "realized_drawdown": 0.082,     # 8.2% (exceeds 5%)
    "window_start": "2026-09-21T00:00:00Z",
    "window_end": "2026-09-28T00:00:00Z",
    "falsifier_passed": false,
    "revert_reason": "Both conditions failed: Sharpe < 0.80 (0.62) AND drawdown > 5% (8.2%)"
  },
  ...
}
```

### 3.2 Preserve Hash Chain

**Important:** When updating `outcome` and `brier_actual`, regenerate the entry hash:

```python
import hashlib
import json

entry = {
  "molt_id": "Q-BLOCKCHAIN-TRADING-CALIBRATION-W90PD1-MOL-001",
  ...
  "outcome": "KEEP",
  "brier_actual": 0.82,
  "measurement_timestamp": "2026-09-28T00:15:00Z",
  ...
  # Omit 'hash' field temporarily for calculation
}

# Serialize to JSON (sorted keys, no whitespace)
entry_json = json.dumps(entry, sort_keys=True, separators=(',', ':'))

# Compute SHA256
new_hash = hashlib.sha256(entry_json.encode()).hexdigest()

# Add hash field back
entry["hash"] = new_hash
```

Then append the updated entry to molt_ledger.jsonl (or replace the existing line if maintaining single-line-per-molt format).

---

## §4: Trigger Molt Notification Hook

### 4.1 Update MOLT_STATE.md

After updating molt_ledger.jsonl, update the molt state in MOLT_STATE.md to trigger automated notifications:

```markdown
## Blockchain Trading Pilot (Z-012)

**Molt ID:** Q-BLOCKCHAIN-TRADING-CALIBRATION-W90PD1-MOL-001  
**Status:** KEPT  
**Measurement:** 2026-09-28 00:15 UTC  
**Falsifier Result:** PASS  
**Sharpe Ratio:** 0.82 (≥ 0.80 ✓)  
**Max Drawdown:** 3.4% (≤ 5% ✓)  

**Outcome:** Constant change permanent. Rebalance threshold remains 0.55.

---

**OR (if REVERT):**

**Molt ID:** Q-BLOCKCHAIN-TRADING-CALIBRATION-W90PD1-MOL-001  
**Status:** REVERTED  
**Measurement:** 2026-09-28 00:15 UTC  
**Falsifier Result:** FAIL  
**Sharpe Ratio:** 0.62 (< 0.80 ✗)  
**Max Drawdown:** 8.2% (> 5% ✗)  

**Outcome:** Constant rolled back to 0.50. Filing F/IC candidate for falsifier failure.
```

### 4.2 CI Gate Trigger

The `.github/workflows/molt-notification-hook.yml` will:
1. Detect MOLT_STATE.md change
2. Extract molt ID and outcome
3. Emit KEEP/REVERT notification to Priority Queue
4. If REVERT: File F-BLOCKCHAIN-TRADING-CALIBRATION-FALSIFIER-FAIL candidate block

---

## §5: Anti-Cascade Check

**After REVERT outcome only:**

Check molt_ledger.jsonl for prior reverts on the same constant (`trading_spec.json:rebalance_threshold`):

```
SELECT molt_id, outcome FROM molt_ledger WHERE constant = "trading_spec.json:rebalance_threshold"
ORDER BY timestamp DESC
```

**If this revert is the 2nd consecutive revert on the same constant:**
- Set `frozen_constant: true` in anti_cascade_check
- File IC-FROZEN candidate block
- Do NOT allow new molts on this constant until Z2 Tier-2 ruling

**Current state:** No prior reverts recorded. This would be the first revert (if it occurs).

---

## §6: Manual Extraction Checklist

- [ ] **Collect blockchain settlement data** for window 2026-09-21 to 2026-09-28
- [ ] **Extract daily returns** from portfolio value trajectory
- [ ] **Calculate Sharpe ratio** (mean / std of daily returns, NO annualization)
- [ ] **Calculate max drawdown** (peak-to-trough decline, as percentage)
- [ ] **Evaluate falsifier:** `Sharpe < 0.80 OR drawdown > 5%`
- [ ] **Determine outcome:** KEEP (falsifier=false) or REVERT (falsifier=true)
- [ ] **Update molt_ledger.jsonl** with outcome, brier_actual, measurement_timestamp, measurement_data
- [ ] **Regenerate entry hash** (SHA256 of JSON, sorted keys)
- [ ] **Update MOLT_STATE.md** with status, measurement result, and outcome
- [ ] **Verify CI gates pass** (molt_ledger hash-chain validation, MOLT_STATE consistency)
- [ ] **Check anti-cascade** (if REVERT, count prior reverts on same constant)
- [ ] **File IC candidate** if needed (REVERT or FROZEN status)

---

## §7: Timeline & Contacts

**Window Close:** 2026-09-28 00:00 UTC (T+0)  
**Measurement Due:** 2026-09-28 08:00 UTC (T+8h, within business day)  
**Authority:** Z2 (carly.r.anderson@gmail.com)  
**Notification Route:** Auto-fire molt-notification-hook → Priority Queue + Z1 alert

**Escalation:** If measurement data unavailable by T+12h, file GAUGE callout to Priority Queue. Z2 decides: extend window, file IC-VOID, or defer molt outcome to manual Z2 ruling.

---

## Appendix: Data Format Reference

### Molt Ledger Entry (Complete Schema)

```json
{
  "molt_id": "Q-BLOCKCHAIN-TRADING-CALIBRATION-W90PD1-MOL-001",
  "zone": "Z-012",
  "constant": "trading_spec.json:rebalance_threshold",
  "prior_value": 0.5,
  "proposed_value": 0.55,
  "prediction": {
    "metric": "Sharpe",
    "target": ">=0.80",
    "window_days": 7,
    "falsifier": "Sharpe < 0.80 OR realized_drawdown > 5%"
  },
  "z2_ratified_at": "2026-09-21T00:00:00Z",
  "z2_ratifier": "carly.r.anderson@gmail.com",
  "ratification_hash": "363d91aa296cffda3086160d0bf22db92a34de0f2ca4c2e19b5bcb81ca5bc937",
  "window_start": "2026-09-21T00:00:00Z",
  "window_end": "2026-09-28T00:00:00Z",
  "outcome": "KEEP",          # "MEASURING" → "KEEP" or "REVERT"
  "brier_actual": 0.82,       # Actual Sharpe ratio
  "measurement_timestamp": "2026-09-28T00:15:00Z",
  "measured_by": "carly.r.anderson@gmail.com",
  "measurement_data": {
    "sharpe_ratio": 0.82,
    "realized_drawdown": 0.034,
    "window_start": "2026-09-21T00:00:00Z",
    "window_end": "2026-09-28T00:00:00Z",
    "falsifier_passed": true
  },
  "timestamp": "2026-09-21T11:49:26Z",
  "prior_hash": "40fe90d500a7fac08d52e69dd449a2393ec50ed907cfbc234ac1edceb590fd49",
  "z2_signature": "610de83d52eec925e89e00573c3e59785edfa1554f08ead4528edc5c3823867f",
  "anti_cascade_check": {
    "open_molt_count": 1,
    "reverts_on_constant": 0,
    "rank_in_queue": 1,
    "frozen_constant": false
  },
  "hash": "ce574f0ea31aab65546896910eb1fe33667bdea9e03a6af247d7b2c99031d8d6"
}
```

---

**Document Status:** Draft (awaiting Z2 review and measurement data)  
**Created:** 2026-09-27 07:30 UTC  
**Authority:** Z1 (Claude) → Z2 (Night) for measurement execution
