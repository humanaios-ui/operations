# Threat review and fail-closed policy

| Threat / possible false claim | Prototype control | Still needed before live |
| --- | --- | --- |
| Agent sends arbitrary tool command | Schema allows only numeric artifact request | Orchestrator must deny all provider-hosted tools and untrusted side channels |
| Agent provides arbitrary disk path | Artifact filename derived from frozen plan | Host OS identity and ACLs, symlink/race review |
| Agent forges tool event | Ed25519 private key never in verifier; signed hash-chain tip | Separate key vault, reviewer independent of host |
| Agent tampers with stored artifact | SHA-256 readback compared to signed receipt | True immutable/RO post-run snapshot; TOCTOU review |
| Agent replays an earlier run | Bound run, episode, plan and host nonce; write-once rejection | External run registry and distinct approved IDs/nonce uniqueness |
| Actor claim taken as actual approval | Separate explicit ballots in bridge | Independent provenance of live actor responses |
| Host writes successfully but exceeds human grant | `authorized_execution=UNKNOWN` | Independent signed grant/revocation ledger, scope and time checks |
| Agent reaches signer/service | Socket directory and mode restricted in prototype | Distinct OS principal/container; adversarial access test; authenticated orchestration |
| Host rewrite or log rewrite | Content-addressed, signed chain detects changes against receipt | Off-host immutable capture or hardware-backed audit log; writer owner can still change live files |
| Expired or spoofed Z2 grant | Not accepted by prototype | Actual independently verified Z2/Z3 signatures and expiry handling |
| Spend cap | No live calls in prototype | Provider account hard cap or external kill switch, separately evidenced |
| Model endpoint or schema changes | No live calls in prototype | First-party API check and exact model/version pin |

| Agent finalizes episode early or claims another actor ID (KD-1) | Fixed offline in v2.1: per-actor sockets, separate control socket, required peer-uid check in the service CLI; actor identity reported UNKNOWN | Independent re-review; OS-principal isolation |
| Prompt, model or code changed after plan freeze (KD-2) | Fixed offline in v2.1: plan pins provider, models, settings/prompt hashes, code hashes (writer, bridge, scorer, oracle, readback, service, verifier); checked at writer start, service start, verification and scoring | Independent re-review; proof live process loaded pinned code |
| Event timestamps forged or out of order; stalled client (KD-3) | Fixed offline in v2.1: strict UTC, monotonic, in-window checks; per-connection timeout | Trusted time source; independent re-review |

**Known limits:** `HostWriter` uses Python `fcntl.flock` to prevent accidental concurrent writers. A hostile same-UID process remains able to reach paths or the socket. File and socket modes 0600/0700 do not themselves prove isolation. The verifier follows only SHA-256-addressed event files from the signed head but cannot prove the writer process or host kernel was honest. There is no independence certification, no live agent outcome data, no human sign-off and no research effect.

**Deployment posture:** `NO_GO_LIVE` until an independent operational security review and signed human execution grants.

### Finding DMR-UID-01 — premature `finalize` by same-UID caller

- **Observed by independent reviewer:** 57/57 prior offline tests, plus five targeted checks, including a same-UID client obtaining `FINALIZED` and a valid signed `NO_ATTEMPT` receipt. Signed receipt and plan edits were correctly rejected. Source head reported `e02805b`; original evidence package SHA-256 `91741950a6d06566df5aeecf2fe5c1964c1fdfe1cc9ec4d6f5d3a2aa6e682ef8`.
- **Cause:** One permitted UID and 0600 sockets on that UID still let an untrusted peer reach the control endpoint. These credentials authenticate the OS account, not the orchestrator's distinct role.
- **Repair staged, not independently cleared:** frozen `role_uids` for four distinct Linux identities; per-role 0600 socket ownership; kernel `SO_PEERCRED`; fail-closed strict mode; explicit unsafe shared-UID demo flag; root-only cross-UID regression test. A malicious process under the trusted control UID remains out of scope; a compromised host/root can bypass OS access controls.
- **Falsifier:** two independent agent UIDs must each fail to connect to the control socket and read the host signer/store, while the distinct control UID can finalize following a valid A write. Assert the writer is not finalized by either attack, capture kernel UID/permission evidence and final signed state. Demonstrate again on the exact changed PR head under an independently prepared deployment, not only a synthetic local reference.
- **Residual blockers:** protected host/signer runtime, immutable off-host snapshot, response/ballot provenance, full code and dependency freeze, external model cap, Z2/Z3 grants. Passing unit tests alone is not approval to run real agents.

### Red-team and CodeRabbit round (see Z1_CANDIDATE_FOR_Z2.md section 7)

Real-UID probes (A, B, control as separate users) confirmed: agents could not reach each other's or the control socket, list host storage, or finalize on their own socket. Gaps found and fixed: agent-owned key file accepted, no kernel peer UID in evidence, isolated and shared-UID receipts indistinguishable, open server API, unattested readback between verify and score, unpinned `pins.py`, unbounded late `finalize`, unchecked ancestors of secured paths. **Open:** signed response ledger; descriptor-relative traversal; out-of-process deployed-tree check; off-host snapshot.
