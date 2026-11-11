# Quiet Infrastructure ↔ existing Witness / Unit Zero (read-only E0)

**Status:** Z1 draft integration, not deployed. **Authority:** NONE. **Execution:** DISABLED.

This is an integration with the existing Witness work, **not a second Witness agent**.

## What is already present

1. `WITNESS_SERVICE_CONTRACT.md` specifies an evidence-bearing assistant that reduces burden, shows uncertainty, and never ratifies its own work.
2. The local Resource Miner on `main` already exposes an opt-in, loopback-only `/api/witness/ask-resource` path via `resource_miner/witness_bridge.py`. It accepts **only** bounded public Resource Miner leads and operator-typed questions. It is **not** a private-resource or Quiet Plan API. It sends the allowed payload through the authenticated Unit Zero MCP `haios_talk` route to a model provider. This is **not air-gapped**.
3. Draft PR #1012 contains Unit Zero / `haios_talk` streaming, source-manifest and operational self-model work. PR author reports Mac v0.1.1 tool discovery and manual model streaming, but PR v0.2 installed SDK round-trip is **not independently verified**. Do not treat this draft as an admitted Witness runtime.
4. `WITNESS_STATE_V0_1.schema.json` defines authorized state, omission codes, reconstructed record chains and nonauthority. The full Arena is an unratified design, not a permission grant.

## This PR's integration

`resource_miner/witness_plan_projection.py` creates a deterministic, **public-safe orientation brief** from this PR's specific Quiet Infrastructure plan using the already-shipped `resource_miner.planning.resolve_resource_plan`. It does **not** send to an AI service and does not claim an AI Witness has observed, verified or approved its content.

Contract:
- Source JSON is limited to `RP-QUIET-INFRA-001` and 64 KiB. Other plan IDs and authority or execution changes are rejected.
- Only concept-token IDs, evidence states, mapped need IDs, source-reference *counts*, derived requirement IDs, gap statuses and mineable booleans are emitted. Free-form plan text, private notes and provider credentials are never included.
- Stable SHA-256 fingerprints the **entire input** as an unsigned content digest; it is not a signature, trusted read-back or certification.
- Output includes explicit omissions: no independent MCP round-trip, no P1/P2/P3 live record, no observed zero-egress proof, no independent human/buyer result.
- `WITNESS_IS_NOT_THE_AUTHORITY`, `ADAPTATION_SERVES_COMPREHENSION_NOT_COMPLIANCE`, and no execution persist.
- No source fetch, sockets, HTTP, provider authentication, persistent memory, graph mutation, model call, human approval or UI change.

### Run a safe, local read-only preparation

From `humanaios-funding-pipeline/resource-miner`:

```sh
python -m resource_miner.witness_plan_projection \
  --file data/resource_plans/quiet_infrastructure.seed.json

python -m unittest tests.test_witness_plan_projection -v
```

The result is a **candidate brief for the existing Witness agent**. A human may later use the existing authenticated Unit Zero `haios_talk` tool to ask for explanation, **only after** reviewing the exact allowed content and consenting to any provider transmission. No such tool call is made by this PR.

For an actual *public Resource Miner lead*, the already-existing UI `Ask the Witness about this Resource` is the narrower active integration seam. It requires its own opt-in, and its data sent to the external model is not air-gapped. Do not disguise an internal resource plan as a public candidate to bypass its existing allowlist.

## E1 — next proof of the live agent (not done here)

1. Independently verify #1012 at exact head, its release/gates and whether the operator's Mac is running the target version (not an older v0.1.1 process).
2. Verify authenticated MCP `initialize → tools/list → tools/call(haios_self_model) → tools/call(haios_talk)` with unique nonce and independently checked source manifest.
3. Run negative tests for invalid bearer, origin, private payload, redirection, consent denial, stale document snapshots and provider failure. Confirm no task submission, financial action or governance change.
4. Keep assistant generation separate from the **independent Witness verification**: the same agent cannot certify its own correctness. Preserve P1 → challenge P2 → correction P3 as separate immutable event receipts.
5. Use **synthetic** records until data handling, encryption, per-user grants, revocation and threat model are separately approved. Do not claim an offline/air-gap product when the model provider receives a network request.
6. Compare against manual administrative QC baseline: error rate, explanation correctness, operator burden, privacy exposures and independent replay. Human decides admission only after exact-head gates and review.

## Integration ownership

`INTENT-OS` holds the explicit human objective and approval boundary; `Resource Miner` holds public candidate observations and resources; the **existing Unit Zero / Witness** explains, cites and exposes missing evidence; `ACAT-R` compares behavior against an independently maintained reference; the **independent verifier** checks immutable source receipts; `Project Desk` records human-reviewed next actions. No model interpretation grants authority or changes canonical state.
