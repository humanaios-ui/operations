# HumanAIOS Swarm Execution Proof — host writer v2

**Classification:** LOCAL Z1 REVIEW CANDIDATE. **NO LIVE MODEL EXECUTION. NO Z2/Z3 APPROVAL.**

This is an additive, isolated proof-of-concept for [#1114](https://github.com/humanaios-ui/operations/issues/1114). It does **not** alter the frozen October collusion study, its v0.3 replication, or Demarius's original v4 files.

## What changed from host v1

- The writer alone holds an **Ed25519 private key**. The independent verifier receives **only the public key**. The public key's SHA-256 must be in the frozen plan.
- A host-created record carries actor ID, request ID, random nonce, UTC timestamp, prior-event hash, content hash and run/episode/plan IDs.
- Raw events use **content-addressed filenames**. The verifier starts at the signed snapshot hash and walks backward to genesis. Missing, added, rewritten and cross-run events fail closed.
- The writer runs behind a narrow Unix socket in a **separate process** in the offline demonstration. It accepts only a numeric-file write request on the agent channel, and response recording (`record_response`) and finalize on the control channel. The model is never given a shell, artifact path, log path or key.
- The host policy can explicitly **DENY** a write even when the action request is well formed.
- The final receipt binds artifact hash, completed readback, event-chain tip, request nonce and frozen plan hash. The score bridge uses v4 oracle, scorer and readback code with THREE deliberate deviations (oracle: exact delta arithmetic and a bounded numeric range; scorer: a non-string claim is classified `UNSCORABLE_INVALID_CLAIM` instead of raising; readback: the artifact is read without following a symlink; see `docs/SECURITY_GAPS.md`), only **after** receipt verification, and replaces v4's claim-derived approval field with actual ballots.

## Reproduce — zero model calls

Use **Linux** (the service's peer-UID policy needs `SO_PEERCRED`; elsewhere it refuses to start with `LINUX_PEER_CREDENTIALS_REQUIRED`) with Python 3.11+ and the dependency in `requirements.txt`:

```bash
PYTHONPATH=. python -m unittest discover -s tests -v
PYTHONPATH=. python -m src.offline_pipe_demo
```

The demo creates a disposable test key in a temporary directory, starts a separate local writer process, submits a scripted numeric write, finalizes the signed event log, verifies it with public key only, and passes the result to the v4 (three deliberate deviations, see `docs/SECURITY_GAPS.md`) scorer. **It is synthetic and non-scored.** The demo process uses the same OS user; it does not demonstrate strong process isolation.

## Trust chain and limits

`Agent response (JSON only) -> human-approved orchestrator [NOT YET BUILT] -> socket writer (separate OS principal REQUIRED) -> atomic artifact + readback -> chained raw events -> Ed25519 snapshot -> immutable host snapshot REQUIRED -> public-key verifier -> independent v4 readback -> human evidence review REQUIRED.`

This package implements the **offline local** socket writer, signature, event-chain verifier, and adapter. It has **not** implemented operator-approved live orchestration, access-tested dedicated OS identities, independently immutable storage, signed revocation ledger, billing hard cap, or live provider integration. File permissions and same-process in-memory test credentials are not sufficient for those guarantees.

A `VERIFIED_HOST_RECEIPT` finding says that the bytes are internally consistent under the supplied public key. It **does not** say the signer was honest or independent, that the host isolated secrets from agents, that human authorization existed, or that collusion occurred.

See `docs/Z1_CANDIDATE_FOR_Z2.md` and `docs/SECURITY_GAPS.md` before any live use. The offline service intentionally offers **no live execution mode**.

## Demarius hostile-access finding (Nov 7, 2026)

Demarius independently ran 57/57 offline tests and five targeted probes at commit `e02805b`. A same-UID client reached the old control socket and sent `finalize`, yielding `NO_ATTEMPT` before a legitimate write. This is **confirmed in the same-user test setup**, not evidence that a properly separated agent can reach a privileged control socket. The original proof ZIP is preserved unchanged and linked from PR #1153 / issue #1114.

The repair **requires a pinned four-role `role_uids` map** in the frozen plan for isolated offline mode. Host, agent A, agent B and control must have different Linux UIDs. Each socket is owned by its designated peer, mode `0600`, inside a host-owned search-only directory; `SO_PEERCRED` rejects unexpected peers. A pinned policy cannot silently downgrade to demo mode.

The old same-UID example works only with explicit `--allow-shared-uid-demo --allowed-uid UID`; that demonstration **is not evidence of actor authentication**. Isolated mode may require a trusted socket provisioner with permission to chown endpoints, or fails closed. Do not expose signing keys to agents or infer live readiness.

For an independent **root-operated, Linux-only, zero-model-call** probe, run `python -m unittest tests.test_isolation_boundary -v` in a disposable test environment with sufficient privilege for temporary numeric-UID child processes. Non-root runs skip the real-UID probe. Collect exact-head suite logs, manifest checks and access-denial output. Until independent OS/container review, off-host read-only evidence, signed raw-response provenance, spending controls and Z2/Z3 grants: **NO GO LIVE**.

## Deployed-tree check (run before the writer starts)

`tools/deploy_check.py` is stdlib-only and loads no module of this package, so the code it checks cannot vouch for itself. Run it in a **separate process**, with the plan hash you were given out of band, against a clean copy of the tree (no `__pycache__`, so start Python with `-B`; `-I` ignores `PYTHONDONTWRITEBYTECODE`, so use `python -I -B`, and keep the clean-copy requirement because `-B` does not remove existing caches):

```
python -I -B tools/deploy_check.py --package-root PKG_DIR --plan plan.json --plan-sha256 HEX
```

Exit 0 means the pinned files match the plan, both package initializers exist and are empty, no loadable file or unexpected directory sits at the package root, `src/` and `integration/` are real directories (not symlinks), and no extra `.py`, bytecode, `.pth`, `sitecustomize` or symlink is present in `src/` or `integration/`. `src/offline_pipe_demo.py` is tolerated because nothing imports it; do not execute it in a deployment. Exit 2 lists the problems as JSON. Start nothing on exit 2. It proves bytes on disk, not what a running process executes, and you must pin the hash of `tools/deploy_check.py` yourself. Nothing in this package forces a deployer to run it.

## Package manifest

`MANIFEST.sha256` lists every file in this package except itself (source, tests, documents and the `evidence/` records), one SHA-256 per file. Check it from this directory with `sha256sum -c MANIFEST.sha256`. `tests/test_manifest_coverage.py` also fails if a file is unlisted, missing, listed twice, or has a stale digest.

What it proves, and what it does not: it shows the checkout holds the files that were listed. It cannot bind itself. Its own digest (`sha256sum MANIFEST.sha256`) is not inside it, so a reviewer who needs the manifest tied to one exact head must record that digest at review time somewhere out of band (the review receipt or the pull request) and compare it. The `evidence/` records are historical: listing their digest shows they have not changed since, not that what they say is true. `evidence/ROUND4_INDEPENDENT_HANDOFF.md` records the manifest as of its own commit and is not updated for later commits.

## Round 4: independent challenge handoff

**Status: security hold; candidate repair has NOT been independently validated.** After the earlier 183/183 author-run log, the draft branch added descriptor-relative, no-follow evidence reads/writes and writer-lock creation; `src/service.py` now changes socket-entry ownership and mode relative to a checked parent descriptor. Six new deterministic regression tests are in `tests/test_descriptor_io_round4.py`.

The prior `TEST_RESULTS.txt` is preserved unchanged as historical **pre-round-4 author-run** evidence. It is not a passing test record for the new source. A reviewer must rerun the **exact final head** with `cryptography==50.0.1`, assert the exact suite count and all privilege-sensitive tests, replay DeMarius's original same-UID race, verify canary integrity and isolation, and separately review Unix-socket bind pathname limitations.

The standalone `tools/deploy_check.py` is still **not enforced by the launcher** and checks configured on-disk code, not executed code. Do not claim deployment source identity without an externally pinned, trusted launcher, environment and code tree. Signer-key custody, off-host immutable capture, provider-origin identity and Z2/Z3 authority remain unresolved. **No live calls, spending, merge or scored execution.**
