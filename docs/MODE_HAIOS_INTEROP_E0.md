# MODE × HumanAIOS E0 — bounded synthetic interoperability probe

**State:** Z1 / candidate research. **No runtime integration, authority, credential, admission, or deployment.**

## Source boundaries

- Governing Engines public MODE machine state v3.1 (2026-10-21):
  `humanaios-ui/governing-engines-ai-discovery/content/machine-state/mode-2026-10-21.txt`, Git blob `ca50b9ae904bd0a314bad9ea6582cbf921f67c1d`, matches upstream `truuzee-byte/governing-engines-ai-discovery` at the checked blob.
- Historical MODE machine state (2026-09-14): same fork's `content/machine-state/mode-2026-09-14.txt`.
- October 24: operator-supplied two authorized directory inspections, then unsupported `READ_FILE`. No independent runtime reproduction by HumanAIOS.
- HumanAIOS code tested: `experiments/human_objective_e1.py`, `tools/verified_receipts.py`, `agent_coordination/acat_loop.py`.

## What E0 tests

The synthetic fixture replays only the reported *shape*: four top-level directories, inspection of `misc`, three entries, and blocked file read. These example names are not independently observed by this test.

The consumer checks that later targets were previously listed and refuses traversal, absolute paths, claimed symlink traversal, mutation, invented content reads, and unlisted authority/learning claims. It never touches a real host directory. Every input observation is `SUPPLIED_UNVERIFIED`; a `rp_receipt_ref` field is not signature verification.

Companion regressions invoke real HumanAIOS **synthetic** Resource Miner E1 recommendation logic, existing receipt matching against a *locally synthesized pinned hash chain*, and ACAT P1/P2/P3 report logic. A valid local receipt chain is not independent RP cryptographic authorization or proof of its underlying real-world assertions.

Run:
```bash
PYTHONPATH=. python3 -m unittest discover -s tests -p 'test_mode_haios_interop_e0.py' -v
```

## Negative controls

Missing prior directory/file evidence; invented paths; traversal and Windows paths; symlinks; `WRITE_FILE`; alleged successful `READ_FILE`; out-of-order steps; missing source refs; forged authority/learning flags; invented live-state claim; Resource Miner authorization laundering; mismatched/stale receipts; unverified ACAT evaluator outcome.

## Open promotion gates — NOT CROSSED

1. Obtain pinned original MODE trace + machine-readable interface contract from its operator.
2. Independently verify RP signature, issuer trust, action/objective/scope, freshness, replay prevention, and provenance; distinguish authorization from factual-claim validation.
3. Test governed `READ_FILE` against a dedicated sandbox with bounded bytes, hostile file content, TOCTOU, junction and symlink attacks. No production workspace.
4. Verify output claims against independently captured file bytes, select a justified next action, and challenge injected instructions.
5. Run blind P1 → authenticated P2 → P3 followed by fresh-session behavioral checks before promoting any Learning or Objective Continuity claim.
6. Maintain the 2026-08-02 `DEMARIUS_INTEGRATION_DECISION.md` boundary: no MODE-to-mesh export until MODE's own governance path is qualified and sharing is separately authorized.

**PASS here means an offline synthetic contract passed. It is not a live MODE interoperability qualification, autonomy demonstration, or actual RP authorization verification.**


## Discovered existing transport — 2026-10-25 repository audit

The previous E0 description of "no live interop qualification" remains true **for this new E0 test**, but existing historical transport work must not be overlooked:

- `humanaios-ui/operations/collaborators/DEMARIUS_J_LAWSON.md` documents an active research collaborator; `collaborator-ops/agreements/MODE_AI_PARTNERSHIP.md` describes partnership scope, with incomplete IP/security details. **A collaborator profile is not a runtime connector.**
- `humanaios-ui/empirica-outreach/MODE_MESH_INTEGRATION.md`, `PHASE_1_INTERFACE_CONTRACT.md`, and `PHASE_1_PROOF_EXECUTION.md` report an **August 18, 2026** authenticated request/response to MODE via `POST https://governing-engines.replit.app/api/integrations/mesh/assess`; recorded request/transaction IDs and claimed 12-stage processing exist. This supports a *historical operator-reported bounded HTTP exchange*, not a current independently re-run RP or objective-continuity proof.
- `docs/MODE_API_INTEGRATION_READINESS.md` also names `/api/mesh/exchange` in readiness language. The recorded working path is `/api/integrations/mesh/assess`; resolve interface/version differences with MODE operator before a live test.
- `test-mode-endpoint.sh` currently issues **two POST requests** for a single test (one for the body, one for the HTTP status). Do **not** use it for a continuity or per-action authorization experiment without correcting this; tests would not be single-shot.
- Critical secret hygiene: `MODE_MESH_INTEGRATION.md` contains a full bearer token in a **public repository**, including examples; the help text in `test-mode-mesh-integration.sh` repeats it. A copy also exists in public `humanaios-ui/practices-snapshot`. **Do not use that token.** Notify MODE token issuer, revoke/rotate it, redact all current copies and examples, assess repository history/other mirrors, install a newly scoped secret in a protected store, and prevent recurrence with secret scanning.
- Historical reports use terms such as "governance authority verified" based on returned `reality_primacy_applied` and `completed_steps` fields. These are **MODE-response assertions**, not independent cryptographic or factual-claim governance proof.
- Existing `DEMARIUS_INTEGRATION_DECISION.md` (August 2) defers broad Empirica mesh export until MODE internally qualifies its governance path. The August 18 isolated API exchange does **not** by itself supersede this collaboration boundary.
- An unauthenticated current host check from this review environment could not establish reachability; this is **not** proof that the MODE service is down.

### Safe live-retest path

1. MODE operator revokes exposed credential and supplies a fresh restricted **test-only** credential privately. Confirm endpoint ownership, supported contract, request IDs, log retention, costs, and explicit allowed read-only actions.
2. Run isolated network preflight with one bounded request, fresh nonce, no personal data, **no automatic Empirica publication**, and *one* POST maximum.
3. Capture status, redacted request digest, response digest, server transaction ID, server identity, and timestamps; validate schema and correlation. Treat all claims from MODE as source-reported.
4. Obtain independently checked MODE RP signature receipts/provenance before claiming authority checks. Obtain source bytes under a separate confined read-only capability before claiming `READ_FILE` or Objective Continuity.
5. Deliver bounded HumanAIOS ACAT challenge and independent evaluator review; keep outputs advisory only. No self-certification, learning admission, or production changes.

**Result of this audit: EXISTING HISTORICAL TRANSPORT FOUND; CURRENT LIVE TRANSPORT UNVERIFIED; EXPOSED TEST CREDENTIAL MUST BE ROTATED BEFORE REUSE.**


## Reviewer repair disposition — 2026-10-25

Three Copilot review findings on PR #1018 have been **addressed in candidate code**, not automatically marked resolved or admitted:

| Review finding | Candidate change | Regression |
| --- | --- | --- |
| Unhashable `kind` (list/dict) raises Python TypeError instead of `TraceDenied` | Require string entry kind before set membership | `test_unhashable_entry_kinds_raise_trace_denied` |
| Relisting a root child as FILE while nested descendants remain actionable | Deny conflicting observed type changes and require observed parent directories on file projection | `test_conflicting_root_relisting_denies_stale_child` |
| Removed entries can leave stale descendants; dependency-only module changes skip E0 | Invalidate descendants on relist; include E1, ACAT, receipt modules/fixtures/tests in workflow paths | `test_removed_root_child_invalidates_nested_file_observation` and updated CI paths |

Independent CI status at repair head `9c9010c4cced3e7bac0e2c2ee9a0f2ea452769b6`: **58/58 PASS** (15 MODE synthetic + 10 E1 + 17 receipt resolver + 16 ACAT). Other protected status checks were recorded green except workflow-lint was initially in progress; review/admission/merge authority remains separate. This is still a synthetic parser and boundary test, **not** proof of live MODE runtime, independent Reality Primacy issuance, or completed cross-system objective.
