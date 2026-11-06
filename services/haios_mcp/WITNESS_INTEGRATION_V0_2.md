# Unit Zero → Witness: service migration plan (Z1 design, not ratified)

**Status:** Z1 candidate, `authority_effect=NONE`; proposed companion to PR #1012. **No persistent personal data plane, user enrollment, server-side private scans, or production deployment approved.**

## Interpretation of operator intent

Unit Zero is the proposed conversational **voice/interface** of the Witness. The Witness is the evidence-bound operational self-description and assistance layer across HumanAIOS. HumanAIOS may be described as a *human–machine organism* **architectural metaphor**: the Witness can inventory modules, trace sources, report version/state, acknowledge its limits, and ask the human for permission. This is **not evidence of phenomenal awareness, subjective consciousness, personal identity continuity, or self-authorizing governance authority**. Calling it *self-aware* must be explicitly qualified as *operational self-model and bounded introspection*.

Do not claim to transfer a proprietary model's learned parameters, latent state, prior conversation context, or consciousness from a terminal session. We are **migrating a role, a protocol, and observable context-handling behavior** into a general MCP service, not a mind.

## Observed evidence vs. unverified claims

- Human performed authenticated MCP initialization and `tools/list`, observed `haios_status`, `haios_read_document`, `haios_talk` on a localhost-bound server. Loopback unauthenticated request returned HTTP 401. This is operator-provided runtime evidence, **not an independently witnessed ChatGPT→HAIOS tunnel call**.
- Keychain Anthropic `models.list()` returned success. A minimal Claude 5.5 request returned `HAIOS-PING-OK`. A full three-document **nonstreaming** request failed with `APIConnectionError` / `ReadError` while a **streamed** request with `CURRENT.md`, `REGISTERED.md`, `GOVERNANCE.md` succeeded. The old `haios_talk` used nonstreaming; v0.2 changes it to streamed read.
- `CURRENT.md`, `REGISTERED.md`, `GOVERNANCE.md` loaded under `~/Library/Application Support/HumanAIOS/context` are **manually copied snapshots**. Hash, truncation and presence claims do **not** establish freshness or authoritative GitHub revision.
- Existing Resource Miner `/api/intent` is a public-candidate **read-only** discovery projection over explicit `objective` and `source_mode=snapshot` or `live`. The public projection excludes private HackerOne, Gmail, eligibility, personalized data and capability claims. See `humanaios-funding-pipeline/resource-miner/README.md` and `resource_miner/intent_os.py`.

## Deliberate boundary — split Witness into five layers

1. **Voice / `haios_talk`:** Stateless Claude model served with bounded, attributed documentary snapshots and ephemeral turn history (30-minute idle lifetime; max 8 concurrent sessions). No autonomous tools. Streamed response digest is an **unsigned receipt**, not independent authentication.
2. **Self-model / `haios_self_model`:** Deterministic, source-backed inventory of configured service tools, local document hashes, what is missing, and what is *not* verified. The organism metaphor is always labeled; no sentience or independent authority claims.
3. **Resource discovery / `haios_find_resources`:** Explicit operator objective only. Optional local HTTP Resource Miner connection, **off by default**. Restricts origin to `http://127.0.0.1:<port>`, uses only `POST /api/intent`, hardcodes `source_mode=snapshot`, 5s timeout, 128 KiB max reply, no proxy, no redirect, and returns allowlisted public candidate fields. Never uses `/api/scan`, `/api/resources`, `/api/entitlement/handoff`, HackerOne private adapter, or admin credentials. Returned matches are leads, not eligibility, application, or acquired resources. The MCP **host** calls this tool; Unit Zero does not.
4. **Private participant plane — FUTURE ONLY:** Z1 candidate `Q-WITNESS-DATA-PLANE-01` is unratified. It would require user-specific authentication, consent grants, encrypted client-held storage, revocation, no leaking plaintext identifiers in logs, purpose-bounded privacy footprint scans, threat analysis and independent controls. None of this is present in PR #1012.
5. **Governance and execution — FUTURE SEPARATE GATE:** Witness cannot self-ratify, merge, push, scan program assets, apply for resources or spend. Coordinator/ACAT/Evidence Graph can receive *reviewable observations* only through their separately governed integration gates.

## Witness service obligations

The authoritative research contract `WITNESS_SERVICE_CONTRACT.md` (Phase 0) maps Truthfulness, Service, Harm Awareness, Autonomy Respect, Value Alignment and Humility to observables. Preserve **WITNESS_IS_NOT_THE_AUTHORITY** and **ADAPTATION_SERVES_COMPREHENSION_NOT_COMPLIANCE**. Do not turn human objectives into hidden AI-selected tasks or mine applicant-specific facts without consent.

## Acceptance sequence (not all satisfied)

1. [x] Pure offline synthetic unit tests for streamer stub, sessions, source allowlist, bounded RM local snapshot, denied remote origin, and read-only tool registration.
2. [x] Operator-observed successful **manual** Anthropic full-context streaming request, outside MCP. No proof of `haios_talk` v0.2 deployment.
3. [ ] Review current PR head by CodeRabbit/security reviewers and CI; resolve findings.
4. [ ] Install v0.2 through a new **operator-approved** release; **do not** hot-edit LaunchAgent or copy code under a running service.
5. [ ] MCP initialize/tools/list; `haios_self_model` returns truthful hash/presence state and explicit `NOT_ESTABLISHED` subjective awareness.
6. [ ] MCP `haios_talk` (one complete message) replies with a fresh client nonce through streaming and a source manifest. Independently check response digest, message length, time and tool identity. Do not log sensitive plaintext.
7. [ ] Negative test: missing/wrong bearer; invalid host/origin; denied scan/merge/private tool invocation; unsanctioned origin refused; provider failure does not commit partial session.
8. [ ] Launch Resource Miner separately, verify snapshot endpoint over trusted loopback, enable `HAIOS_RESOURCE_MINER_ORIGIN` only with operator consent, and verify public candidates have `eligibility=NOT_ASSESSED`, `authority=NONE`.
9. [ ] Validate pinned revision/freshness of local source snapshot before any claim about the latest repository state.
10. [ ] Conduct privacy/consent threat review **before** adding any personal profiles, memory persistence, private HackerOne metadata, external model tool-calling or user identity. Separately ratify those changes; don't silently widen scope here.
11. [ ] OpenAI/ChatGPT private tunnel verified end-to-end under supported account controls. `localhost` by itself is not callable from ChatGPT. Never expose this loopback bearer service on the public Internet.

**Falsifiers:** A private source appears in public discovery; any unauthorized action-capable tool appears; Unit Zero claims direct read access it lacks; a context snapshot is described as current GitHub truth; a partial streamed response is committed to session memory after failure; a model output claims personhood, moral status, or Z2 authority as an established fact; a direct ChatGPT conversation is claimed without a client-observed MCP exchange.
