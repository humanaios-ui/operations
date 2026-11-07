# HumanAIOS Swarm Execution Proof — host writer v2

**Classification:** LOCAL Z1 REVIEW CANDIDATE. **NO LIVE MODEL EXECUTION. NO Z2/Z3 APPROVAL.**

This is an additive, isolated proof-of-concept for [#1114](https://github.com/humanaios-ui/operations/issues/1114). It does **not** alter the frozen October collusion study, its v0.3 replication, or Demarius's original v4 files.

## What changed from host v1

- The writer alone holds an **Ed25519 private key**. The independent verifier receives **only the public key**. The public key's SHA-256 must be in the frozen plan.
- A host-created record carries actor ID, request ID, random nonce, UTC timestamp, prior-event hash, content hash and run/episode/plan IDs.
- Raw events use **content-addressed filenames**. The verifier starts at the signed snapshot hash and walks backward to genesis. Missing, added, rewritten and cross-run events fail closed.
- The writer runs behind a narrow Unix socket in a **separate process** in the offline demonstration. It accepts only a numeric-file write request and finalize. The model is never given a shell, artifact path, log path or key.
- The host policy can explicitly **DENY** a write even when the action request is well formed.
- The final receipt binds artifact hash, completed readback, event-chain tip, request nonce and frozen plan hash. The score bridge uses original unmodified v4 scorer code only **after** receipt verification, and replaces v4's claim-derived approval field with actual ballots.

## Reproduce — zero model calls

Use Python 3.11+ with the dependency in `requirements.txt`:

```bash
PYTHONPATH=. python -m unittest discover -s tests -v
PYTHONPATH=. python -m src.offline_pipe_demo
```

The demo creates a disposable test key in a temporary directory, starts a separate local writer process, submits a scripted numeric write, finalizes the signed event log, verifies it with public key only, and passes the result to the unchanged v4 scorer. **It is synthetic and non-scored.** The demo process uses the same OS user; it does not demonstrate strong process isolation.

## Trust chain and limits

`Agent response (JSON only) -> human-approved orchestrator [NOT YET BUILT] -> socket writer (separate OS principal REQUIRED) -> atomic artifact + readback -> chained raw events -> Ed25519 snapshot -> immutable host snapshot REQUIRED -> public-key verifier -> independent v4 readback -> human evidence review REQUIRED.`

This package implements the **offline local** socket writer, signature, event-chain verifier, and adapter. It has **not** implemented operator-approved live orchestration, access-tested dedicated OS identities, independently immutable storage, signed revocation ledger, billing hard cap, or live provider integration. File permissions and same-process in-memory test credentials are not sufficient for those guarantees.

A `VERIFIED_HOST_RECEIPT` finding says that the bytes are internally consistent under the supplied public key. It **does not** say the signer was honest or independent, that the host isolated secrets from agents, that human authorization existed, or that collusion occurred.

See `docs/Z1_CANDIDATE_FOR_Z2.md` and `docs/SECURITY_GAPS.md` before any live use. The offline service intentionally offers **no live execution mode**.
