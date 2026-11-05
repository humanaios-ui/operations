# Resource Broker → Oracle Consumer E1 (issue #1123)

**Status:** Z1 draft integration, advisory-only. **Not merged, deployed, authenticated, queued, admitted or run in production.**

## Connection, not a second miner

`resource_miner.broker_oracle_bridge.bridge(snapshot)` calls the **existing**
`resource_miner.internal_repository_broker.project()`; it hands that same
projection to `oracles/engine/resource_broker_consumer_v0_1.py`.
The consumer does not implement resource discovery or search. It preserves
`resource_id`, `opportunity_id`, `need_id`, exact PR identity, and declared
capability-code matches. No source fetches or network connections occur.

```
Approved public-safe GitHub snapshot (caller-provided)
       | actual Resource Miner internal_repository_broker.project()
       v
Canonical broker projection: resource IDs + need/capability matches
       | new read-only bridge
       v
Oracle consumer: schema v1 observation records + graph delta
       | advisory only; NOT delivered or persisted
       v
Human-reviewable proposed tests, without a separate queue database
```

**Boundaries:** No Gmail import or private message IDs, account entitlement
claims, CodeRabbit review triggers, production storage, PR comments, CI or
CodeRabbit invocation, Actualizer, Coordinator writes or authorization changes.
The official marketing email is not proof of account entitlement. A PR's
presence, match, CI result, or review-skip notice is not an independent review.
The output's graph delta represents **declared matches**, not established facts.
No mutation or `candidate_change` is sent to the Coordinator.

## Run in a checked-out operations tree

```
cd humanaios-funding-pipeline/resource-miner
python3 -m unittest discover -s tests -p 'test_broker_oracle_bridge.py' -v
python3 -m resource_miner.broker_oracle_bridge \
  --input tests/fixtures/broker_oracle_public_snapshot.json > /tmp/broker-oracle-advisory.json
```

The fixture pins a November 3 observation of PR #1121 for an offline CodeRabbit-
related E1 test. It is not a current status check and has no private Gmail data.
The CLI writes only to stdout; file redirection is an operator choice.
Repeated runs of the same snapshot produce stable IDs (including when the
output record time changes), so a future approved sink can deduplicate by ID.
The consumer emits `queue_delivery=NOT_ATTEMPTED` and `persisted=false`.

## Gate before activation

1. Separate trusted connector read-back confirms exact PR and CI SHA; detect
   stale captures and contradictory source history rather than mutating it.
2. Independent tests and review on the **exact candidate PR head**.
3. Apply optional schema validation with a JSON Schema 2020-12 validator.
4. Decide private, durable append-only Oracle delivery only under a separate
   human authorization; idempotent sink and provenance/authentication required.
5. Bind strategy display in INTENT-OS with explicit human choice and result
   receipts; do not confuse code review, admission, acquisition or benefit.

Existing canonical controls remain #735 (Oracle), #1055 (CodeRabbit offers),
Resource Miner, Coordinator, and Z2 authority. No new active authority source.
