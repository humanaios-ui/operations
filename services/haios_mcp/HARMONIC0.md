# HARMONIC-0 — Governed Witness Router (simulation-only)

**Research stage:** Z1 / candidate-only. **Authority effect:** NONE. **Runtime:** no provider, model, network, MCP tool, process, keychain, repo write, resource action, merge or deployment. This is a *policy experiment* beside Witness v0.2, not a replacement or extension of the deployed service.

## Why this is separate

The existing Witness MCP host exposes limited read-only tools (`haios_status`, `haios_read_document`, `haios_self_model`, `haios_find_resources`, `haios_talk`). The Phase 0 router recognizes these tool names as task categories **but never calls them**. Keep the tool authorization boundary independent from the intelligence routing decision: even a cloud-selected request has no right to execute a tool.

## Mechanism

1. **Explicit classification** (`PUBLIC`, `PRIVATE`, `UNKNOWN`). The harness accepts a caller-supplied category for synthetic cases; this is not authenticated or an adequate production data-loss-prevention classifier. Unknown classification abstains.
2. **Tool scope** denies any task identifier outside the existing read-only Witness tool names, including shell and write commands.
3. **Local-first assessment:** a healthy capable simulated local endpoint wins even if cloud permission exists.
4. **Cloud simulation** only when: the tool category is allowed; the input is explicitly PUBLIC; local capability/health fails or a simulated runtime failure occurs; simulated cloud endpoint is available; AND a per-request `CloudGrant` matches the request ID, exact public text SHA-256, boolean operator intent and `HARMONIC0_SIMULATED_CLOUD_ONLY` scope. These grants are **unsigned synthetic permission flags, not actual authorization or identity attestation**.
5. **Abstain** through a third simulated `UNAVAILABLE` endpoint if any required condition fails. Privacy must never be weakened by automatic reliability fallback.
6. **Receipt journal** stores request metadata and payload digest, route, reason code, endpoint attempts, policy version, prior receipt hash, timestamp and new hash. It does **not** store prompt text or response text. Replay recalculates the pure policy from stored metadata and verifies hashes/chain; it cannot verify model quality, evidence completeness, omission of prior entries, or authentic human identity. This is unsigned, single-process journal evidence only. Do not claim remote attestation or cryptographic append-only assurance.

## Run locally (no dependencies beyond Python 3.10+)

From the repository root:

```sh
PYTHONPATH=services/haios_mcp/src python3 -m unittest -v services/haios_mcp/tests/test_harmonic0.py
PYTHONPATH=services/haios_mcp/src python3 services/haios_mcp/scripts/harmonic0_demo.py
```

To retain a local example journal in a **private** operator-selected directory:

```sh
PYTHONPATH=services/haios_mcp/src python3 services/haios_mcp/scripts/harmonic0_demo.py \
  --journal "$HOME/.humanaios/harmonic0-routing.jsonl"
```

The demo is intentionally one-time; using the same journal with the same sample request IDs fails on duplicate IDs. A successful demo prints `REPLAY {"valid": true, "count": 4, ...}` and `EXECUTION SIMULATED_ONLY_NO_PROVIDER_MCP_OR_NETWORK`.

## Acceptance and failure scenarios

| Input | Expected route | Evidence |
| --- | --- | --- |
| Healthy capable local, PUBLIC (even with cloud grant) | LOCAL | `LOCAL_DEFAULT` |
| Public, local lacks capability, request-bound synthetic cloud grant | CLOUD (simulated) | `EXPLICIT_SIMULATED_CLOUD_PERMISSION` |
| PRIVATE, local unavailable, even with synthetic cloud grant | UNAVAILABLE | `PRIVATE_CLOUD_BLOCKED` |
| PUBLIC, local unavailable, missing/mismatched grant | UNAVAILABLE | `CLOUD_GRANT_MISSING_OR_MISMATCHED` |
| PUBLIC, local execution fails, valid grant | CLOUD (simulated) | Attempts show local failure then cloud success |
| PUBLIC, cloud unavailable or fails | UNAVAILABLE | Explicit fallback limitation |
| UNKNOWN privacy, or unauthorized task | UNAVAILABLE | No endpoint attempt |
| Mutated, truncated or inconsistent receipt | replay REFUSED | No overwriting journal |

## Promotion gate (HARMONIC-1)

Do **not** replace the simulated local endpoint with `llama.cpp` until there is an independent human-reviewed policy contract and runtime sandbox evidence. First choose a CPU-compatible quantized model; establish baseline memory, quality and latency; compare local-only, cloud-only, governed hybrid and cost-only hybrid using ACAT P1/P2/P3 independent evaluations. Cloud-only is a separate explicitly approved evaluation and must not send private prompts, accounts or credentials. For real provider calls, add authenticated one-use authorizations, DLP-safe payload handling, rate limits, explicit network destination allowlists, external audit receipts and independent identity verification **before** allowing any cloud egress. Router logs are not grounds to merge, deploy, retrain, spend or promote a model.
