# E3 — Controlled Witness public Resource Miner projection

**Gate:** Z1 / read-only. Authority effect: NONE. No production claim.

## Hypothesis

The MCP host, independently of Claude, can ask `haios_find_resources` to query only the public Resource Miner `POST /api/intent` route with `source_mode=snapshot`, preserve source and incompleteness disclosures, reject private-program rows, omit non-allowlisted candidate fields, and make no eligibility or authority assertions.

## Procedure

1. Existing Keychain MCP bearer token is loaded only into an isolated subprocess environment; credentials are not printed. The already-installed v0.1.1 service on port 8768 is untouched.
2. An ephemeral, loopback-only synthetic HTTP server exposes the expected public `/api/intent` shape. The isolated v0.2 MCP server is started on a different ephemeral loopback port. The script authenticates, checks all five tools, and issues a public objective query. It asserts preserved `PARTIAL_CANDIDATES_FOR_HUMAN_REVIEW`, `unexamined_count=2`, source warning, allowlisted provenance, `eligibility=NOT_ASSESSED`, `execution=DISABLED`, `authority=NONE`, and removal of a synthetic private canary field. A second candidate with a private source class must be refused.
3. If the operator has an accessible local Resource Miner source tree with `data/resources.snapshot.jsonl`, launch its `app.py` in an **isolated subprocess** on 127.0.0.1 and a random port. Query via a **second isolated v0.2 MCP server**, again with `source_mode=snapshot` only. Record the Miner `app.py` hash and snapshot hash before/after; require an unchanged snapshot. No `live` discovery, scan, admin API, external provider, private HackerOne account, or Anthropic request.
4. Print E3 **PASS** only if *both* synthetic and real local Miner paths verify; otherwise clearly print **PARTIAL**. The receipt is an **unsigned local hash**, not a signed independent evaluator attestation.

## Real Miner source discovery

The script checks known HumanAIOS Mac paths and optionally `HAIOS_E3_MINER_ROOT`; it will not download, rebase, reset, mutate, or refresh any checkout. If no stored snapshot is found, the real-backend gate remains unverified. Use an explicit local `HAIOS_E3_MINER_ROOT` only if needed. The test never prints API keys or persistent user identifiers.

## Known limitations

- Local snapshot observations are not live program availability, ownership, eligibility, or recovery benefit.
- The MCP tool cannot independently authenticate official source websites. Its SHA receipt is not signed and does not establish external provenance.
- A private program, endpoint, or source must not be added to this bridge without separately approved per-user consent, isolation and security review.
- Even if E3 passes, admission, merge, deployment, and autonomous execution remain outside scope.