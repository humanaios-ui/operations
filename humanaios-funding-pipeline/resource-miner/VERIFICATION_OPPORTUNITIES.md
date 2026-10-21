# RMO-VERIFY-001 — passive verification opportunity screen

Admission / session graph: https://github.com/humanaios-ui/operations/issues/773

This experimental Resource Miner module **does not** fetch URLs, crawl LinkedIn, evaluate inventions, contact inventors, or grant permission. It evaluates submitted, attributed observations only. GitHub and public-innovation-challenge source kinds are accepted as normalized **manual/public inputs**, not automated discovery connectors.

## Entry point

`resource_miner.verification_opportunities.evaluate(observation, capabilities)`

Input observations require a public HTTPS source URL, explicit need state, claim summary, source kind, and optional evidence-reference URLs. Screening differentiates `CANDIDATE`, `CLAIM_ONLY`, `REVIEW_ONLY_NO_CONSENT`, `INSUFFICIENT_SIGNAL`, and `BLOCKED_EXTERNAL_ACTION`.

Output is always `authorization_state=NOT_AUTHORIZED` and `can_authorize=false`. Capability fit `POTENTIAL_ONLY` is not suitability proof. `DASE_SEED` is only a linked, unverified candidate; author consent, patent status, novelty, benchmark results, and commercial intent have **not** been independently established.

## Offline unit tests

From `humanaios-funding-pipeline/resource-miner`:

```sh
python3 -m unittest discover -s tests -p test_verification_opportunities.py -v
```

## Boundaries & limitations

This first implementation is a deterministic screening contract with synthetic tests, not a deployed Resource Miner ingestion adapter. The public-URL check is lexical only; do not dereference accepted URLs without independent SSRF/DNS and platform-policy controls. LinkedIn ingestion is user-provided URLs only. Real pilot counts and precision metrics are not yet measured. Coordinator admission, CI, graph integration, and external-source adapter implementations remain follow-up work.
