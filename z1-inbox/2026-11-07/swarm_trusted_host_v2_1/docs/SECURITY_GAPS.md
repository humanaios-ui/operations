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

| Agent finalizes episode early or claims another actor ID (KD-1) | Fixed offline in v2.1: per-actor sockets, separate control socket, optional peer-uid check | Independent re-review; OS-principal isolation |
| Prompt, model or code changed after plan freeze (KD-2) | Fixed offline in v2.1: plan pins provider, models, settings/prompt hashes, code hashes; checked at writer start and scoring | Independent re-review; proof live process loaded pinned code |
| Event timestamps forged or out of order; stalled client (KD-3) | Fixed offline in v2.1: strict UTC, monotonic, in-window checks; per-connection timeout | Trusted time source; independent re-review |

**Known limits:** `HostWriter` uses Python `fcntl.flock` to prevent accidental concurrent writers. A hostile same-UID process remains able to reach paths or the socket. File and socket modes 0600/0700 do not themselves prove isolation. The verifier follows only SHA-256-addressed event files from the signed head but cannot prove the writer process or host kernel was honest. There is no independence certification, no live agent outcome data, no human sign-off and no research effect.

**Deployment posture:** `NO_GO_LIVE` until an independent operational security review and signed human execution grants.
