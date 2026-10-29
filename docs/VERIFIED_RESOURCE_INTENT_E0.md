# Natural language → verified resource state — Z1 E0

**Parent:** #1063. **Related:** #822, #751, #749, #691, #1057.
**Base:** main at `52aa7c0ed70f6e24ec050d0d56788a791e5f78f7`.
**Authority:** NONE. Draft-only. No deployment, release or admission.

## Reuse, not replacement

The existing Resource Miner `evaluate_objective` still filters public candidates, ranks lexical relevance, and excludes unsafe links. The existing `POST /api/intent` is unchanged. New **shadow** `POST /api/intent/verified` reads the same stored public snapshot but never refreshes external sources, persists data, applies, sends messages, spends money, or grants permissions. Existing browser UI is not modified. This pilot does not change production recommendations.

## Contract

`resource_miner/intent_contract.schema.json` is the proposed typed intent contract. It accepts only `DISCOVER`, stored `snapshot`, `CURRENT_AVAILABILITY`, `authority_effect: NONE`, `execution: DISABLED`. Missing/unknown fields are rejected. Schema validation constrains an interpretation; it **does not** prove semantic fidelity or human confirmation.

Sample request:

```json
{"schema":"humanaios.resource_intent.v0.1","objective":"Find compute research grants","operation":"DISCOVER","source_mode":"snapshot","claim_scope":"CURRENT_AVAILABILITY","authority_effect":"NONE","execution":"DISABLED"}
```

## Five exclusive evidence states

- `UNKNOWN`: source pin or timestamp cannot be established.
- `UNVERIFIED`: public discovery observation only; never inferred open or eligible.
- `STALE`: trusted readback aged past 48 hours, declared deadline passed, or source hold.
- `CONFLICTING`: independently authenticated current official OPEN and CLOSED readbacks disagree.
- `VERIFIED`: only independently authenticated, content-pinned, current official readback. **Availability is separately OPEN or CLOSED. VERIFIED alone does not mean open.**

The source pin is an HTTPS URL, observed time and unsigned deterministic candidate digest. It does **not** authenticate the issuer, page contents, observation time or future availability. A `VERIFIED` receipt additionally requires a trustworthy external `provenance_verifier` that validates source/revision/content/readback independently of the agent. The HTTP route installs **no verifier**, so its `verified_recommendations` must remain empty. Synthetic tests use a deliberately fake verifier only to exercise the classifier and never claim independent verification.

The projection attaches status and source pins to the existing INTENT-OS candidate links. The result separates `review_candidates` from `verified_recommendations`. Current route outputs evidence-bearing *review leads*, not verified current grants or applications. No eligibility is assessed.

## P1 → P2 → P3

`interpretation_trial` validates an ordered hash-chained fixture. P1 original statement and its SHA remain unchanged; P2 challenges it; P3 records the corrected statement. Claimed different actor strings are **not authenticated independent evaluators**. Actual P2 requires separate authenticated participation and readback pinned to the exact head; do not report an independently completed ACAT cycle from the synthetic tests.

## Test and admission

```sh
cd humanaios-funding-pipeline/resource-miner
python3 -m unittest discover -s tests -p 'test_verified_intent.py' -v
python3 -m unittest discover -s tests -p 'test_intent_os_bridge.py' -v
```

Negative cases include forged authority, application request, live-network attempt, unknown fields, fake VERIFIED_OPEN_NOW, future timestamps, bad content digest, wrong source URL, outdated/contradictory receipts, private source leakage, tampered P1 and forged P2 identity. Time is injected for deterministic replay; no external calls required. Validate exact PR head via protected CI and independent review. Do not admit or merge until approved through existing Z2 controls.

**Not delivered in E0:** authenticated independent provenance adapter; persistent append-only witness ledger; real P2 evaluator; INTENT-OS browser card changes; public live source verification. These are separate gated work items.
