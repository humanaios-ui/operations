# HackerOne private query — adapter extension (draft)

This uses the existing `HackerOneClient` and `scan_portfolio` read-only metadata path. It does **not** install or depend on the HackerOne MCP server.

## Private, bounded use

The persistent mine resolver now accepts optional `mine.config.handles` (non-empty list of account-visible program handles) or `mine.config.max_programs` (positive integer). Example **synthetic** local-only config:

```json
{"handles": ["example-fixture"]}
```

Inject actual invitation-only handles through a private, caller-owned configuration at runtime. **Do not commit private handles or project metadata.** Credentials are read from `HACKERONE_API_USERNAME` and `HACKERONE_API_TOKEN` in the local environment; do not put tokens in configuration, commits, issue comments, or chat.

## Important limits

- This change is **query bounding**, not a privacy boundary. Current candidate normalization and opportunity receipts can include program names, scope identifiers, and source metadata. Do not send private results through the public scheduled scan, public artifact upload, issue logs, CI logs, or public Evidence Graph.
- For invitation-only research, use a private local execution context and a private storage sink. A separate privacy-safe projection must be implemented and reviewed before any automatic INTENT-OS/Witness publishing.
- An invitation is not an execution grant. This API bridge only reads program metadata; it must never touch targets, submit reports, attempt jailbreaks, or authorize security testing.
- Program access and policy must be rechecked at query time. Missing program / HTTP failure is not proof that entitlement was revoked.
- Tests use synthetic fixtures. CI runs with HackerOne credentials empty. A live authenticated query and data-flow privacy audit remain **unverified**.

## Offline validation

From `humanaios-funding-pipeline/resource-miner`:

```sh
python3 -m unittest tests.test_hackerone_bounded_mine -v
```

Do not enable private projects in the public seed registry.

## Minimal local account check (no saved program data)

From the `humanaios-funding-pipeline/resource-miner` directory, set `HACKERONE_API_USERNAME` and `HACKERONE_API_TOKEN` in your **local** shell or a local secret manager (never commit, paste, or print them). Then run:

```sh
umask 077
python3 private_hackerone_query.py
```

Enter the handle at the hidden prompt. The script calls the existing read-only `HackerOneClient.find_program`, then outputs only booleans and constant counters: visibility, presence of policy/submission-state fields, and zero target requests / stored records. It does not print program names, policy text, scope, raw API payload, or invitation-only handles. It does not write records.

**Do not use** `resource_miner.cli scan --dry-run` or `resolve-mines --dry-run` for a private invitation: both can expose complete records on stdout. Avoid normal `--out` paths as well; the standard mine pipeline creates opportunity, proposition, claim, and event records. Its existing `app.py` admin routes can serve saved resource records. Those outputs are **not** safe sinks for private program data.

Local API credentials and a local authenticated run have **not** been verified by ChatGPT. Offline tests mock the client only. Next security milestone: private encrypted store, per-user grants, and a privacy-safe INTENT-OS projection.
