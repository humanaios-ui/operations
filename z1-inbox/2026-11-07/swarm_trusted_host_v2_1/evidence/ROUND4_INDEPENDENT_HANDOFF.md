# PR #1153 — Round-4 independent security challenge handoff

**Evidence class:** Z1 offline candidate for bounded Z2 review consideration only. **Authority: NONE.** No merge, scored run, live model call, external spending or Z2/Z3 execution grant.

## Immutable review target (source-bounded)

- Repository: `humanaios-ui/operations`
- PR: https://github.com/humanaios-ui/operations/pull/1153
- Branch: `claude/zen-dijkstra-e181ql`
- **Candidate source HEAD at handoff creation:** `d9da5e45de771459195a97d46a951c460d9e0b33`
- Prior independently reviewed E95 commit: `e95ac77bd6824a7f195737e6a7d4fdc5ec8fe2fe`. DeMarius reported 140/140 passing there on Python 3.13.5 and cryptography **46.0.4**, a dependency mismatch against pinned 50.0.1, plus a deterministic **same-UID** ancestor-substitution before pathname `chmod` (redirected permissions, distinct-UID exploitability not established).
- Pre-round-4 author-run test evidence: `TEST_RESULTS.txt`, **183/183** at `ab39aa542eec8011df66f90d8e849111acea11d7`. Do **NOT** transfer that pass to the candidate head.
- Round-4 changed: `src/writer.py`, `src/service.py`, `tests/test_descriptor_io_round4.py`, `README.md`, `docs/SECURITY_GAPS.md`, `MANIFEST.sha256`. Source changes were *not* run locally in this handoff.
- Manifest: **32 entries**. Manifest file SHA-256 as computed during assembly: `035ddf6c83e21140c8362a0ad86d11972d63855a94e443ca747d351937d9cfd1`. Recompute independently from the exact checkout; do not trust this line alone.

## Repair claims to challenge, not assume

1. `_open_parent_fd` walks from `/` through `O_DIRECTORY|O_NOFOLLOW` descriptors and checks UID, permissions and POSIX ACLs on each opened directory.
2. `new_file`, `open_read_no_follow`, and the writer-lock creation use descriptor-relative `os.open`; failure cleanup uses `os.unlink(..., dir_fd=...)`.
3. The isolated service sets parent permissions by `fchmod`, and endpoint ownership/mode by `dir_fd`-relative `chown`/`chmod` with `follow_symlinks=False`. **The Unix-domain socket bind remains pathname-based.** Inspect replacement and reachability in an independently configured host.
4. `tests/test_descriptor_io_round4.py` adds **six new synthetic tests**, including deterministic forced swaps after directory validation but before the leaf read/write. New tests are **not recorded as passing** in `TEST_RESULTS.txt`.
5. `tools/deploy_check.py` checks on-disk source out of process, but no trusted launcher requires it. The checker, interpreter, site-packages, environment, read-only mount and post-check file immutability remain outside its proof.

## Exact-head independent reproduction

**Freeze the full SHA before starting.** If any byte changes, label the old receipt historical and begin a new review.

```bash
git checkout --detach <FULL_HANDOFF_COMMIT_SHA>
cd z1-inbox/2026-11-07/swarm_trusted_host_v2_1
sha256sum -c MANIFEST.sha256
python3 -m pip show cryptography
# In a disposable virtualenv with an approved package source, require cryptography==50.0.1.
# Stop or mark the dependency gate UNKNOWN if unavailable. Do not silently substitute.
PYTHONPATH=. python3 -m unittest discover -s tests -v 2>&1 | tee independent_round4_full_suite.log
PYTHONPATH=. python3 -m unittest tests.test_descriptor_io_round4 tests.test_secure_dir_round3 tests.test_isolation_boundary -v 2>&1 | tee independent_round4_boundary.log
```

Run the privileged Linux real-UID tests as root **inside a disposable sandbox**; confirm no skips. Preserve `uname -a`, Python version, `python -m pip freeze`, exact SHA, full stdout/stderr, manifest and raw hostile test output. Do not use production keys or providers.

**Adversarial falsifiers:** use DeMarius's original deterministic same-UID check/use interleaving and vary it for leaf file read/write, cleanup, writer lock, socket parent mode/owner, socket bind, ACL grants, and concurrent attacker UID rename. Show canary bytes, modes, ownership, device/inode before and after. Distinguish a synthetic same-UID race from cross-UID exploitability. Reject any result claiming that a passed suite proves deployed signer or provider independence.

## Independent receipt format

For every gate: `PASS | FAIL | UNKNOWN | NOT_TESTED`, exact source SHA, OS/kernel, Python and pinned dependencies, immutable hashes of logs, reference to the raw reproduction, observation vs inference, counterexample/falsifier, and residual risk.

Minimum gates:
- Manifest and pinned dependency match
- Full package suite, exact count, zero privileged skips
- Original E95 deterministic reproduction at vulnerable source vs repaired candidate
- Evidence and signer paths: ancestor swap, symlink, ACL, cross-UID and race
- IPC socket bind and endpoint ownership
- Deployed-source identity under independently pinned launcher
- Independent signer/private-key custody
- Immutable off-host, read-only snapshot and independent receipt verification
- Provider/model identity from evidence independent of the orchestrator
- External hard spend cap and explicit Z2/Z3 grants

**Stop conditions:** any cross-boundary file permission change, evidence read/write redirect, unauthorized socket access, source/manifest mismatch, unsigned or caller-fabricated ballot, absent reviewer log, or dependency mismatch. Do not convert UNKNOWN to PASS.

## Boundary and requested decision

Accept prior reviewer findings for **bounded Z2 review**; do not grant merge/security clearance. Z2 can inspect a candidate with unresolved failures. The build team owns repair, independent reviewer owns challenge, Night/Z2 owns ratification and Z3 owns any separate tool/model grant.

**Handoff output requested:** one source-bound independent review packet; raw logs plus checksums; PASS/FAIL/UNKNOWN per gate; unresolved blockers; recommendation for Z2 review consideration only. Keep initial October research baseline and all earlier independent evidence intact.
