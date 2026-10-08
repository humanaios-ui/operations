# HMBM-CYCLE-003 — durable epoch continuity protocol

Status: `INIT_PENDING`  
Authority: paper-research only; no real capital, wallets, private keys, fund movement, or live trading.  
Lineage: preserves HMBM-CYCLE-002 exactly as observed. Missing post-P0 epochs from Cycle 002 are not reconstructed.

## Purpose

Test whether exact scheduled paper-research epochs can survive the complete persistence loop:

`SCHEDULE_TRIGGER -> STATE_VERSION_CHECK -> OBSERVE -> PREDICT/ABSTAIN -> HASH_ARTIFACT -> WRITE -> READ_BACK -> HASH_COMPARE -> ACCEPT -> ADVANCE_STATE`

A failed write/read-back/hash comparison creates `MISSING_DATA` and does not advance canonical state.

## Initialization gate

Before `INIT_VALID=true`, Drive must contain and read-back verify:

1. ordered 100-asset manifest;
2. source snapshot + mechanical selection rule;
3. frozen cohort/control bindings;
4. operator/proxy schema;
5. nine opening portfolios of 5,000 simulated USDC;
6. decision schedules;
7. numerical fee/slippage model;
8. prediction/evaluation schema;
9. PAPER ONLY authority boundary;
10. protocol Git commit SHA;
11. artifact hashes;
12. `INIT_RECEIPT.json` binding all required artifacts.

## Epoch identity and replay

Each epoch receives a deterministic idempotency key:

`HMBM-CYCLE-003:<SET>:<EPOCH>:<SCHEDULED_UTC>`

Reprocessing the same key must return the existing receipt. It must not create a second epoch.

## Temporal fields

Every epoch records separately:

- `scheduled_at`;
- `triggered_at`;
- `observation_cutoff`;
- `persisted_at`;
- `lag_seconds`.

Late execution is never silently represented as on-time execution.

## State advancement rule

`COMPUTED != COMMITTED`.

State may advance only when:

- envelope schema validates;
- expected previous state version/hash matches;
- Drive write succeeds;
- read-back bytes hash to the same SHA-256;
- receipt is persisted;
- authority boundary remains PAPER ONLY.

## Gmail projection

Gmail receives compact checkpoint projections only. Email delivery is not proof of epoch persistence.

## Falsifiers

The Cycle-003 substrate fails if duplicate epochs appear for one idempotency key, a failed read-back advances state, a late epoch loses its temporal distinction, Drive/GitHub divergence is undetectable, or any path creates/requests live trading authority.
