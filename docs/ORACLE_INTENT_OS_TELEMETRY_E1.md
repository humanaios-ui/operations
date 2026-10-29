# Oracle → INTENT-OS authenticated review telemetry E1 (Z1 shadow)

**Issue:** #1065. **Base:** \`main\` \`52aa7c0ed70f6e24ec050d0d56788a791e5f78f7\`.
**Authority:** NONE. **Execution:** DISABLED. **Admission:** NOT GRANTED. **Scope:** one fixed public GitHub review event, not generalized graph ingestion or resource verification.

## Existing architecture, not a new authority plane

\`ORACLE-SOURCE-GITHUB\` retrieves source objects using an explicit operator-supplied read-only GitHub token, HTTPS \`api.github.com\`, five exact allowlisted REST GET paths, a no-redirect client and bounded responses. An Evidence Domain Oracle projection emits one noncanonical \`CONTRADICT\` graph delta between the exact reviewer comment and P1 claim. Oracle telemetry emits one \`INDEPENDENT_ACCOUNT_REVIEW_BRIDGE\` alert. INTENT-OS exposes a read-only local view and endpoint. Both Oracle and UI retain \`advisory_only:true\`, \`can_authorize:false\`, \`authority_effect:NONE\`, \`execution:DISABLED\`. This extends \`oracles/ORACLE_CONSTITUTION.md\`, not the canonical Oracle registry or a general graph store.

**Source subjects** (fixed in \`resource_miner/oracle_review_telemetry.py\`):
- Git commit \`77e872c6ecde828bf965efc3fa82a2ac3cfb4b4b\`.
- Original document at that immutable Git revision, Git blob \`40d3f11e4bc8b9b89d49ae1bc308556f1d389df8\`. The binary blob is rehashed using Git object framing.
- Copilot review id \`5697326401\` and exact-head challenge id \`4412042009\`; separate account identity is verified against GitHub's API, not a guarantee of independent model internals.
- **P1 commitment outside PR**: issue #1065 comment id \`6496931195\`; typed JSON anchors the original commit, blob and exact claim digest. The GitHub server stores it separately from the mutable P3 projection.

**Critical timestamp:** This particular commitment was created **after** P2. The classifier returns \`RETROSPECTIVE_BACKFILL_NOT_PRECHALLENGE\`, and \`historical_immutability_proven:false\`. An editable GitHub issue comment is not an independently controlled, append-only or cryptographically immutable ledger. Even a newly created *pre-P2* comment is classified \`PRECHALLENGE_GITHUB_RETAINED_EDITABLE_NOT_INDEPENDENT_CONTROLLER\` and keeps \`historical_immutability_proven:false\`. Claiming P1 had been precommitted before this historical review would be false.

## Local operator run

Use your existing Resource Miner server; do not add a second server or expose the token in the browser, page, query, log or repository. Provide a GitHub fine-grained **read-only** access token scoped to public repo metadata, Contents, Pull requests and Issues (or a short-lived token with equivalent permissions). The token must never have repository Contents:write, Pull requests:write or Administration permission merely to run this service.

\`\`\`sh
cd humanaios-funding-pipeline/resource-miner
export HUMANAIOS_ORACLE_GITHUB_READONLY=1
# Provision HUMANAIOS_ORACLE_GITHUB_READ_TOKEN from a secure environment/secret store.
python3 app.py --host 127.0.0.1 --port 8766
# Then open http://127.0.0.1:8766/intent-os and follow the Oracle link.
# API: GET http://127.0.0.1:8766/api/oracle/review-telemetry
\`\`\`

Absent token, absent opt-in, nonloopback listener, unsafe Host/Origin, missing GitHub object, unexpected identity, digest mismatch or edited ledger **fails closed**; no fallback to the unsigned E0 fixture. Authenticated GitHub REST access is not external evidence of model independence, claim correctness, current opportunity availability or real human benefit. No user text or personal task content leaves the local service in this route. It does perform read-only live GitHub HTTPS requests when explicitly enabled.

## P1 retention protocol for the *next* challenge

1. Before exposing P1 to a reviewer, record and persist the exact source git SHA, blob SHA, statement digest, issue identity, actor and commit time with a separate controlled evidence custodian. Preserve the custodian-issued immutable, timestamped receipt outside the agent's writable PR/worktree. A GitHub issue comment is useful as an **editable secondary anchor**, not the independent immutable witness.
2. Retrieve the receipt through an authenticated, pinned read-only interface; compare source digest, issuer identity and creation time to P1 and P2, fail if edited, missing, backdated, or not under independently controlled retention.
3. Have a distinct authenticated reviewer evaluate that exact SHA. Retain P2's original review and its source pin.
4. Attach P3 as a new, non-authorizing interpretation, never overwrite P1 or P2; retain contradictions and explicit uncertainty.
5. Only after independent source/readback tests, exact-head CI and human Z2 admission, propose a production change.

## Falsifiers / verification

\`\`\`sh
cd humanaios-funding-pipeline/resource-miner
python3 -m unittest tests.test_oracle_review_telemetry -v
python3 -m unittest discover -s tests -p 'test_*.py'
\`\`\`

Negative cases: absent/expired token, changed original document blob, changed P2 comment, mismatched review source SHA, a changed issue ledger, time reversal, no reviewer, unauthorized public listener, and unexpected REST path. The test fixture is synthetic but mirrors the **actual** source ids; the authenticated live route must read back those five objects, not trust the fixture. Replaying the same five server objects must produce an identical receipt. If the referenced GitHub review or issue comment is later modified, fail closed, report \`UNVERIFIED\`.

**Not yet established:** immutable third-party custody, continuous polling/webhooks, automatic graph-store writes, separate evaluator platform identity, unattended execution, human outcome, deploy health, external resource eligibility. The UI is a deliberately narrow read-only local integration and does not change existing public \`/api/intent\` outcomes.
