# INTENT-OS Reconciled E0.3 ↔ Unit Zero MCP v0.2 — offline compatibility review

**Status:** Z1 PROPOSAL / NOT RATIFIED / NOT MERGE-READY  
**Authority:** NONE; human Z2 decision required  
**Scope:** Public resource candidate conversation *boundary*, not a provider-backed test, approved agent, or deployed integration

## Source identity and method

- E0.3: operator-supplied `INTENT_OS_Reconciled.zip`, unpacked into a separate local test copy. The reconciled workbench identifies itself as `reconciled-local-e0.3`. The E0.3 `on-track.html` local-test CSP was corrected in that isolated copy to allow its same-origin scripts. This CSP correction is **not** proposed by this change.
- Main comparison: `humanaios-ui/operations` at `700531851b636674dd50bc53546bd74f6735b8d1` (2026-11-11 checkout before this proposal).
- Unit Zero: open/unmerged PR #1012 at `1c40658814853ff7a721567c524929d8b7795051`, package `humanaios-mcp-service==0.2.0`. This is not the historically installed v0.1.1 binary/source.
- Method: direct source comparison, a real loopback HTTP negative-test server with the MCP bridge disabled, public-envelope tests, mocked *enabled* handoff, and authenticated **read-only** MCP tool-list/status observation with no Anthropic key loaded. No `haios_talk` was invoked during this offline comparison.
- IMPORTANT: Prior one-call synthetic model proof is separate and does **not** constitute this offline test's result, admission, or permission for another call.

## Compatibility matrix

| Boundary | E0.3 ↔ v0.2 finding | Evidence / limit |
|---|---|---|
| Browser candidate input | Compatible **in source shape** | E0.3 dispatches public resource ID/title/source/route/source URL and typed question with consent to `/api/witness/ask-resource` |
| Server-side public envelope | **Identical bridge source** to main at the comparison baseline | `resource_miner/witness_bridge.py` SHA-256 matched E0.3 and main; source is public/unverified, private fields rejected, source URL query/fragment removed |
| Consent | Fail closed | Literal `true` required; no consent → no Keychain/MCP call |
| Same-origin HTTP | Fail closed while disabled | Same-origin request → 503 and no provider call |
| Foreign Origin / Host | Fail closed | Rejected with HTTP 403/404; reject status may depend on which local access check fails |
| Cross-site Fetch Metadata | **Regression found on main** | Main lacked E0.3's `Sec-Fetch-Site` check; a `cross-site` request reaching the disabled endpoint yielded 503 rather than immediate access denial. Proposed one-line restoration plus regression check. Note: same-origin Origin/Host controls remained present; this does **not** prove cross-site access to the model |
| Local MCP endpoint | Read-only MCP protocol PASS | v0.2 `127.0.0.1:8768/mcp`, authenticated list of five tools and `haios_status` with `authority=NONE` |
| Python environment | **Deployment gap** | E0.3 running application uses Python 3.9; `mcp` and `httpx2` were installed only into isolated Python 3.12 virtualenv. Enabling `HAIOS_WITNESS_BRIDGE_ENABLED=1` in the current E0.3 server would not by itself make imports work |
| Model access | **Disabled by design for this review** | No Anthropic key in running Unit Zero process; E0.3 Witness flag false. An enabled real conversation would need a separate service startup / opt-in |
| Model response schema | Partially source-reviewed, **not integrated end-to-end here** | Bridge validates `answer`, `authority=NONE`, manifest list count, and returns `execution=DISABLED`; offline test stubs `_ask_mcp`, not actual `haios_talk` |
| Manifest attribution | Partial | Bridge returns filenames / truncated / available, but omits the underlying SHA-256 values from Unit Zero's model response. Do not claim that displayed browser response independently verifies source hashes |
| Governance | No admission | `authority=NONE`, no automatic application, source verification, profile change, GitHub write or persistent memory |
| Long-term maintenance | Not ready | v0.2 is unmerged and authentication/dependency wiring requires review; source and deployment pinning are separate from an E0.3 build ID |

## Repeatable regression commands

From `humanaios-funding-pipeline/resource-miner` within the proposed main branch:

```sh
python3 -m unittest discover -s tests -p 'test_witness_offline_integration_contract.py' -v
python3 -m unittest discover -s tests -p 'test_witness_bridge.py' -v
```

For a cross-version test, run the new test module with the E0.3 package as the current import root and the proposal's `tests` folder on `PYTHONPATH`; do **not** change or replace E0.3 application files.

## Observed results, 2026-11-11

- New permanent contract module: **13/13 PASS on patched main**.
- Same permanent module: **13/13 PASS with E0.3 code loaded**.
- Existing bridge regression module: **6/6 PASS**.
- E0.3 joined-workspace browser test: PASS (existing script).
- Unit Zero v0.2 local service: 5 tools listed and read-only `haios_status` PASS; no Anthropic key loaded.
- Main full Resource Miner discovery: **625 tests run, 4 failures, 2 errors, 9 skipped**. Observed failures in ACAT-R verification/source-state tests, not in the new Witness contract tests. We have **not yet independently established whether these six failures reproduce at unchanged main**. Do not claim full-suite green or interpret them as caused/cleared by this proposal.
- Test observations are operator-side, not third-party attestation; the exact new test module itself is the repeatable executable evidence.

## Test exclusions and risk register

1. **HOLD provider call**: no model-backed resource handoff in this proposal. The past single synthetic approval does not authorize another one.
2. **HOLD bridge enablement**: no change to default-off environment flag. No Keychain action in tests; the running E0.3 process remains disabled.
3. **HOLD merge**: full-suite drift/baseline must be independently reconciled; cross-site gate needs code review for other local routes.
4. **HOLD production**: no LaunchAgent, persistent credential handling, user-data training, or private-profile transmission approved.
5. **Unresolved provenance fidelity**: browser-side summary content originates in an unverified public candidate, not independently fetched official data; model output is explanation, not verification.
6. **Unresolved browser integration**: mock handoff is not evidence of a successful browser → locally enabled bridge → v0.2 model response flow.
7. **No secret storage in repository**: tests use synthetic markers only. The live Mac Keychain remains outside GitHub.

## Proposed Z2 review

Approve only a **test/security-boundary proposal** after an independent reviewer:

1. Confirms the `Sec-Fetch-Site` check preserves legitimate same-origin user workflow and denies hostile cross-site requests.
2. Reproduces 13/13 new checks on exact proposed head and validates no Keychain or Anthropic access.
3. Separately reruns baseline ACAT-R source-state failures and resolves their cause or explicitly excludes them with evidence.
4. Confirms v0.2 PR #1012 admission is a **separate decision**.
5. Keeps all merges, deployments, model usage, and resource actions subject to explicit Night/Z2 approval.

**No ratification is implied by drafting, testing, opening a PR, or using the word Witness.**