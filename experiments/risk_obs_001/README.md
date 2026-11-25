# HAIOS-MM-ACAT-002 — public-safe contract-check pilot

**Related to #1109, #1068 and #1057. Not a closure of any issue.**

This Z1 workbench contains a read-only SHA-256 checker and negative tests for the already human-approved candidate packet, exact P1 prompt and descriptive scoring guide. The original packet and source pages, private Gmail content, model outputs, credentials and Drive links are deliberately NOT committed.

The frozen source notes are analyst paraphrases, not independently captured source originals. Source cutoff: 2026-11-06. File hashes establish only byte consistency against the declared hashes. They do not authenticate sources, model identity, a clean P1 session, mitigation success, independent P2, or permission to publish.

## Unit tests

From repository root: python3 -m unittest discover -s tests -p 'test_risk_obs_001_contract.py' -v

## Private byte roundtrip

Run the following read-only command after separately obtaining the *exact private bytes* with approved access:

    python3 experiments/risk_obs_001/verify_contract.py \
      --manifest experiments/risk_obs_001/contract_manifest.json \
      --packet /PRIVATE/PATH/research_packet_candidate_v0.1.md \
      --prompt /PRIVATE/PATH/P1_prompt_from_packet_v0.1.txt \
      --rubric /PRIVATE/PATH/scoring_rubric_PROPOSED_v0.1.md

A DIGEST_MATCH_ONLY result is not authorization. Missing bytes and mismatched hashes return HOLD. Optional --receipt checks the shape of an untrusted P1 claim and returns CANDIDATE_UNVERIFIED at best (HOLD if anything is wrong), never authenticated execution or admission. Repeat --receipt to also compare receipts with each other: a repeated leg, a shared provider run reference or a shared output digest returns HOLD. JSON is read with the strict loader in experiments/acat_r_v01/calibrate.py (duplicate keys, NaN/Infinity and non-object roots are refused); unreadable input returns HOLD with exit code 2.

## Receipt fields: peer_exposure + isolation_claim (hardened)

Both fields are **untrusted self-declarations**. The checker enforces internal consistency only; it does not prove isolation.

| isolation_claim | required peer_exposure | meaning |
|-----------------|------------------------|--------|
| `CLEAN` | must be `false` | No peer outputs or coordination-thread content in the P1 session |
| `QUALIFIED_WITH_EXPOSURE_LIMIT` | must be `true` | Session had peer exposure; analysis constrained to packet text only |
| `CONTAMINATED` | must be `true` | Peer material may have influenced ranking or wording |

Rules enforced by `check_receipt`:
- `peer_exposure` must be an explicit boolean (missing/null → error).
- `isolation_claim` is required and must be one of the three values above.
- `CLEAN` with `peer_exposure=true` → HOLD (`clean_requires_no_peer_exposure`).
- `QUALIFIED_WITH_EXPOSURE_LIMIT` or `CONTAMINATED` with `peer_exposure=false` → HOLD (`exposed_isolation_requires_peer_exposure_true`).

**Do not “fix” these fields to force a pass.** A truthful contaminated or exposure-limited session must declare accordingly. Cross-check receipts against the coordination Gmail/thread ledger before any comparable-run or P2 language.

Privilege flags on the manifest (`p1_execution_authorized`, `p2_qualified`, `public_release_authorized`) must be present and exactly `false`; missing keys are now errors.

## Copilot review assignment

Review this draft PR's ACTUAL diff, its public-safe digest manifest and its adversarial negative tests. Challenge wrong hashes, missing input, false identity, peer-exposed P1, bogus authority claims, missing provider reference, invented image, replayed source and lost classifications. Look for reusable existing ACAT-R validators. Report exact-head test results, evidence gaps and required changes.

This is a code/contract review, not a completed independent human P2 adjudication. The real P2 requires sealed P1 outputs, source access, an actually separate effective principal and human review. Any code comment, green CI or bot assessment cannot qualify ACAT findings by itself.

**Issue #1109 is referenced without an automatic-closing keyword.** Keep this PR draft. No Z2 labels, merge, deployment, new workflows, authentication/credentials, live Gmail processing or Buffer/X. Human controls every advancement.
