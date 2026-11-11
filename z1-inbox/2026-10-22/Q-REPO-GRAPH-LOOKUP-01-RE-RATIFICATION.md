# Z2 re-ratification: Q-REPO-GRAPH-LOOKUP-01

**Ratified by:** Night (Z2), 2026-10-22
**Candidate:** `z1-inbox/2026-10-15/Q-REPO-GRAPH-LOOKUP-01.md`
**Decision:** ACCEPT (re-ratification; supersedes `Q-REPO-GRAPH-LOOKUP-01-RATIFICATION.md`, dated 2026-10-15)
**Signature:** `sha256(candidate | by=Night | at=2026-10-22 | decision=ACCEPT)` over the candidate's bytes at signing
**Z2 hash:** `3d9fd60e45ad381233420f6086dcfee37da3b44d657c6ba6986ea9286d63e800`

## Why re-ratified

The 2026-10-15 signature (`d80d38e5…`) no longer verifies. The candidate file was changed after signing, and no version in git history reproduces that hash. The verifier also hashes the file's own `ratification_hash` line, so a candidate cannot carry its own signature.

## What changed

- Candidate: the `ratification_hash` value is cleared. The signature lives only here and in the index.
- Index: `ratified_at` is `2026-10-22`; `z2_hash` and `z2_ruling` point to this record.
- Scope: unchanged. Ratifies the read-only tool and its candidate block only. SESSION_RITUALS §A wiring and committing a pinned graph remain open decisions.

The 2026-10-15 ruling file is kept in history as superseded.
