# Held-out gate protocol: GNER-E1 equal-workload study (issue #1081)

**Status: HOLD. No held-out set exists.** The implementer has not selected, seen, or guessed any
held-out case. Nothing in this directory is a held-out label. This file only fixes the procedure so
that when a *different* reviewer authors the set, both methods can be run unchanged against it.

## Roles

| Role | Who | Must not |
|------|-----|----------|
| Held-out author | A reviewer who did **not** write `study.py`, `evidence_classes.json` or the 30 proposed labels | Reuse any of the 30 case ids or inputs; consult the implementer while authoring |
| Implementer | Claude Code (issue #1081 delegated plan) | See any held-out case or label before the sealed manifest digest is posted |
| Sealer | The held-out author, or the operator | Reveal the set before the digest is recorded in issue #1081 |

## Sealing procedure (author side)

1. Write `held_out_manifest.json` following `held_out/MANIFEST_TEMPLATE.json`: an `author`
   identity, an `authored_at` timestamp, a frozen `runtime` pin (same three Git blobs as
   `study.PINNED_BLOBS`), and `cases[]` each with `id`, `lead`, `canonical`, `expected`,
   `evidence_class`, `contract_ref` and `rationale`. Include at least two negative controls whose
   expected state is `CANONICAL_VERIFIED` (valid inputs that must not be flagged). The manifest
   must not reference its own seal (no comment URL, no digest of itself): those bytes are what
   gets hashed, and anything added after hashing would break verification.
2. Compute `sha256(file bytes)` of the manifest. Post **only the digest**, the case count and the
   author identity to issue #1081 before revealing the file. That comment is the seal.
3. Reveal the file (commit it under `held_out/`, or attach it) only after the seal comment exists.
   Then write the unhashed sidecar `held_out/SEAL_RECORD.json` (template
   `SEAL_RECORD_TEMPLATE.json`) with the manifest digest, the seal comment URL, and the seal and
   reveal timestamps. `study.py` is not modified for the held-out run; the runner below is a
   separate entry point.

## Execution (implementer side, after reveal)

1. Verify the revealed file's SHA-256 equals the sealed digest; abort on mismatch.
2. Verify the three pinned blobs are unchanged (`study.check_pins()`).
3. Run the unchanged `reconcile` through the same isolated worker (`study.run_phase`) on the
   held-out cases once (P2) and once more (P3); require byte-identical replay.
4. Run the equal-workload conventional assertions on the same rows and expectations.
5. Report the confusion matrix per method using the held-out author's labels **as given**:
   true positive = flagged and author expects non-match; false positive = flagged on a valid
   negative control; false negative = author expects a mismatch the method did not flag;
   agreement between methods; replay result. Do not reclassify a held-out label; record any
   disagreement as a reviewer question.
6. Keep held-out results separate from the 30-case results. Neither replaces the other.

## Stop conditions

Stop and record HOLD if: no sealed digest exists; the revealed bytes do not match the seal; any
pinned blob changed; the author is the implementer or reused implementer-authored cases; or any
label lacks an `evidence_class` and rationale.

## What this is not

It is not a claim that ACAT-R detects more than conventional tests. On identical inputs and
labels, the 30-case study measured zero additional detections; the held-out gate exists to test
that measurement on labels the implementer never saw, not to overturn it.
