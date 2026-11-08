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

Real-UID probes (A, B, control as separate users) confirmed: agents could not reach each other's or the control socket, list host storage, or finalize on their own socket. Gaps found and fixed: agent-owned key file accepted, no kernel peer UID in evidence, isolated and shared-UID receipts indistinguishable, open server API, unattested readback between verify and score, unpinned `pins.py`, unbounded late `finalize`, unchecked ancestors of secured paths. **Built since, offline:** the signed response ledger (section 8 of the Z1 candidate): the host hashes and parses relayed replies, the verifier re-derives them, and the bridge refuses contradicting caller observations. It trusts the orchestrator to relay faithfully. **Open:** descriptor-relative traversal; out-of-process deployed-tree check; off-host snapshot; orchestrator trust.

### Red-team round 2: response ledger (author-run, offline)

Probed the newest code, the signed response ledger. Found and fixed, test first (`tests/test_redteam_ledger.py`):

- **Hostile model text crashed the host.** A reply made of tens of thousands of `[` raised `RecursionError`, which the parser and the socket handler did not catch. A model, or a prompt injection into one, could make a slot impossible to record. Now recorded as `UNPARSEABLE`.
- **Ledger named any model.** `model_id` was only format-checked. The host and the verifier now require the model the frozen plan pinned for that actor (`model_a` / `model_b`).
- **One reply could fill two slots.** `provider_request_id` could repeat. Reuse is now refused by the host and by the verifier.

Probed and held: largest legal reply (32768 control characters, JSON-escaped) fits the control channel; deeply nested objects and huge number literals are `UNPARSEABLE`; lone surrogates are refused.

**Still true:** the model id and request id are what the orchestrator *reports*. A provider cannot sign its replies, so a lying or compromised orchestrator can still report a pinned model and a fresh id. These checks catch mistakes and lazy forgery, not a determined orchestrator. Run-level model verification stays open. Evidence: 140 tests, author-run, Python 3.13 and 3.11. Not independently rerun.

### Round 3: the two threads left open on purpose (author-run, offline)

- **`secure_dir` (writer.py).** Now walks from `/` with directory descriptors and `O_NOFOLLOW`, reading ownership, mode and ACL from the descriptor it then uses (`fstat`, `fchmod`), and refuses a path that resolves elsewhere after the walk (`PATH_CHANGED_DURING_CHECK`). Any POSIX ACL (access or default) on a secured directory is refused (`ACL_PRESENT`), as is a `..` component. Tests: `tests/test_secure_dir_round3.py` (real ACL xattrs; a root-only attacker under another UID racing in a sticky directory, where a returned path must always be host-owned 0700 and a canary directory is never chmod-ed).
- **Deployed tree (pins.py).** `tools/deploy_check.py` is an out-of-process, stdlib-only check of the on-disk tree against the plan's pins: modified or missing pinned files, a modified `pins.py`, extra `.py` files that could shadow a module, planted bytecode, `.pth` files, `sitecustomize`, stray top-level `.py` files, symlinks, and a non-empty package initializer (`src/__init__.py`, `integration/__init__.py` run on import, so they must exist and be zero bytes, because without `src/__init__.py` a top-level `src.pyc` wins the import of `src`; top-level bytecode, `.so`, `.pyd` and `.pth` files are refused too; a symlinked `src/` or `integration/`, a package root reached through a symlink, and any unexpected top-level directory such as `json/` that could shadow a library are refused as well; added after three CodeRabbit findings and one self-review). Tests: `tests/test_deploy_check.py`.

**Limits, stated plainly:** the live race test is probabilistic and would pass against some unsafe variants; the deterministic tests (descriptor `fchmod`, re-pointed path) carry that guarantee. Later reads and writes under the secured directory are still path-based; they rely on the checked ancestors staying unwritable by others. NFS, FUSE and filesystems without xattrs are untested. Only POSIX ACLs are looked for, not LSM policy or capabilities. The deploy check does not prove what a running process executes, its own hash must be pinned separately, and nothing forces a deployer to run it. 183 tests, author-run, Python 3.13 and 3.11.

**What the deploy check cannot cover (it is an enumeration of import-path vectors, so it will never be complete):** the Python installation and its `site-packages`, `PYTHONPATH` and other environment variables, `.pth` files outside this tree, the working directory a launcher chooses, and anything that changes after the check runs. The launcher should use `python -I`, a clean environment, and a read-only mount of the checked tree.

### Round 4: descriptor-relative evidence and socket operations (candidate; NOT independently tested)

The original reviewer reproduced an ancestor substitution before pathname `chmod` at e95ac77. Round 3 corrected that one permission update with `fchmod`, but later evidence file reads and writes, the writer lock, and socket ownership/mode changes still used pathname-based operations. This candidate round makes these operations relative to open, checked directory handles:

- `src/writer.py` `_open_parent_fd` walks from the filesystem root with `O_DIRECTORY|O_NOFOLLOW`, checks ownership/mode and POSIX ACL on each opened directory, and returns a live parent FD.
- `new_file` uses `os.open(..., dir_fd=parent)` and `os.unlink(..., dir_fd=parent)` for cleanup. `open_read_no_follow` reads via the checked parent FD and rejects non-regular leaves. The writer lock is opened using the same method. These changes aim to prevent an ancestor-swap between validation and a leaf operation from redirecting writes or reads to a substituted tree.
- `src/service.py` uses a checked parent FD and `fchmod` for socket-parent permissions, and `dir_fd`-relative `chown`, `chmod`, and `stat` for socket entries. Unix socket `bind` itself still requires a pathname; an independently verified protected parent tree is required.
- `tests/test_descriptor_io_round4.py` adds six tests, including deterministic ancestor substitution exactly between parent-descriptor acquisition and leaf access. These tests are staged, **not yet claimed passing**.
- The package log `TEST_RESULTS.txt` records **183/183 author-run tests before this round**, not a run of the modified source. A fresh full suite and privileged real-UID probes are required at the final commit.

**Not established:** these changes do not prove that the process loaded independently verified source, that a deployed parent cannot be renamed by a malicious host or same-UID process, that off-host evidence is immutable, or that the orchestrator relayed genuine provider-origin responses. `tools/deploy_check.py` remains an optional checker, not an enforced trusted launch gate. The trusted deployment launcher, its hash, the runtime/import path, a read-only code mount, signer/store custody, the independent off-host snapshot and the provider hard spending cap all remain external execution blockers. **NO_GO_LIVE; no merge or scored runs.** Z2 may review the evidence, not convert test results into authority.
