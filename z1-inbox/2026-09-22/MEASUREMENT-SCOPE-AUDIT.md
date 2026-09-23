# Measurement Scope Audit — Blockchain Trading Pilot (Z-012)

**Type:** Finding (F)  
**Date:** 2026-09-22  
**Window:** 2026-09-21 to 2026-09-28 (measurement in progress)

---

## The Risk

The blockchain trading pilot has a falsifier (Sharpe >= 0.80 AND realized_drawdown <= 5%) but **no documented baseline for what volumes, market conditions, or trade frequencies are being measured**. This creates two risks:

1. **False positive measurement:** The window might capture atypical market conditions or produce a high Sharpe ratio by chance rather than by calibration effect.
2. **Unmeasured scope:** A "passing" measurement could mean "we got lucky" not "the rebalance threshold of 0.55 is better than 0.50".

---

## What the Pilot Specifies

| Aspect | Documented | Status |
|--------|---|---|
| Strategy | correlation-based-rebalance | ✅ specified |
| Prior constant value | 0.50 | ✅ specified |
| Proposed constant value | 0.55 | ✅ specified |
| Metric | Sharpe ratio | ✅ specified |
| Threshold | >= 0.80 | ✅ specified |
| Drawdown limit | <= 5% | ✅ specified |
| Window duration | 7 calendar days | ✅ specified |
| Window dates | 2026-09-21 to 2026-09-28 UTC | ✅ specified |

---

## What is Unspecified (Measurement Scope Gap)

| Aspect | Why It Matters | Current State |
|--------|---|---|
| **Asset pair(s)** | Sharpe depends on assets. Stable-pair correlation differs from volatile pairs. | ❌ MISSING |
| **Position size** | A $100 trade and a $100M trade have different slippage, execution risk, and market impact. | ❌ MISSING |
| **Trade frequency** | Sharpe requires sufficient data points. 1 trade/week has no statistical power; 100 trades/hour is different. | ❌ MISSING |
| **Baseline measurement** | What was the Sharpe ratio at threshold=0.50 during a comparable period? | ❌ MISSING |
| **Market conditions, 2026-09-21 to 2026-09-28** | Did blockchain markets exhibit normal volatility? Bull/bear/sideways? High/low correlation? | ❌ MISSING |
| **Rebalance frequency** | How often does the threshold trigger a rebalance? 0.55 vs 0.50 may never differ in practice. | ❌ MISSING |
| **Slippage model** | Are on-chain execution costs baked into Sharpe? Or is it idealized? | ❌ MISSING |
| **Liquidity conditions** | Is the market depth (order book) sufficient for the position size? | ❌ MISSING |

---

## What This Means

### Scenario A: Measurement "Passes" (Sharpe >= 0.80)

**Best case:** The rebalance threshold of 0.55 is genuinely better than 0.50 for this strategy.  
**Risk case:** The window captured favorable market conditions (e.g., strong uptrend, low correlation) that made *any* calibration look good.  
**Null hypothesis:** We cannot rule out the null without baseline data.

### Scenario B: Measurement "Fails" (Sharpe < 0.80 OR drawdown > 5%)

**Best case:** The rebalance threshold of 0.55 is worse or no better than 0.50.  
**Risk case:** The window captured unfavorable conditions that depressed Sharpe for reasons unrelated to the threshold change.  
**Null hypothesis:** We cannot distinguish signal from noise without baseline data.

---

## Falsifier Compliance Check

The pilot specifies:  
> "Falsifier: Sharpe < 0.80 OR realized_drawdown > 5%"

This is a **pass/fail gate**, but it lacks **comparative baseline**:

- ✅ **Concrete threshold:** 0.80 is specific, testable
- ❌ **Counterfactual:** What would Sharpe have been at 0.50 over the same window?
- ❌ **Effect size:** Is a Sharpe diff of 0.05–0.20 meaningful for this strategy/market?
- ❌ **Statistical power:** Is 7 days enough sample to detect a real effect?

---

## Required Before "Measurement Complete"

At 2026-09-28 00:00 UTC window close, extract and document:

1. **Asset pair(s)** traded during window
2. **Total position sizes** (notional USD or equivalent)
3. **Trade count** and average trade size
4. **Realized Sharpe ratio** at threshold=0.55
5. **Baseline Sharpe ratio** at threshold=0.50 (simulated on same window if not simultaneously measured)
6. **Realized drawdown** (maximum peak-to-trough)
7. **Market volatility** (benchmark: VIX-equivalent for blockchain assets, or realized vol of underlying pairs)
8. **Rebalance events** (how many times did threshold trigger a trade?)
9. **Slippage/execution cost** (actual vs. idealized)

---

## Verdict

**The pilot is measuring something, but we haven't documented what.**

- Measurement autonomy: ✅ Scheduled
- Falsifier clarity: ✅ Specific threshold
- **Measurement meaning: ❌ Scope undefined**

Without baseline volume and market condition documentation, a "pass" verdict on 2026-09-28 will require Z2 judgment call: "Did this pass because the calibration is better, or because we got lucky?"

---

## Z2 Decision Required

At measurement window close (2026-09-28), after falsifier evaluation:

1. **If Sharpe >= 0.80 AND drawdown <= 5%:** Accept or quarantine pending baseline analysis?
2. **If Sharpe < 0.80 OR drawdown > 5%:** Revert or extend window pending baseline comparison?

This candidate proposes: **Require baseline Sharpe measurement (at threshold=0.50, same window) before ratifying threshold=0.55 as "better".**
