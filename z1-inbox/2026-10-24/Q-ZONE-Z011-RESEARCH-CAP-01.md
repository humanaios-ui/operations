# Q-ZONE-Z011-RESEARCH-CAP-01 — Change Z-011 (research) from READ-ONLY to LIMITED cap

**Status:** Z1 proposal. Unratified. Awaiting Z2 signature.
**Authority effect:** NONE until ratified. This file changes no row in `ZONE_REGISTRY.md`. The exact edit is in §4 for Z2 to apply.
**Pinned at:** operations `main` `52aa7c0e`; research PR #6 head `e2b5543` (includes PR #7, the release rehearsal). The earlier pin `d0579c6` is superseded: the head has grown to 28 files, and the release pipeline and migration described in §2.1 were not part of it.

---

## 1. Why

`ZONE_REGISTRY.md` lists Z-011 `research` as 🔒 READ-ONLY ("Frozen papers archive", no proposals).

On 2026-10-24, in Claude session `session_01Sq12pdVorzji1sVLmLHd98`, the operator (Night) was asked whether to work in `research` or stage a proposal in operations. The answer selected was **"Night unlocks research"**. Z1 then opened draft PR humanaios-ui/research#6 (publishing foundation).

That answer is an in-chat instruction. It is not a ratified zone change. The independent review on PR #6 flagged the drift: the registry still says READ-ONLY while the PR says unlocked. This candidate either regularizes that instruction or reverses it.

## 2. Proposal

Move Z-011 to the Limited-Cap table with this proposal cap:

> **Publishing infrastructure only.** Layout READMEs, `registry/`, `scripts/`, `tests/`, `.github/`, `docs/`, and design-only `infra/`. No edit or delete of any file under `datasets/` or `corrections/` (append-only), except `README.md` navigation files inside those trees, which research `scripts/inventory.py` classifies as source and not data. No release without a per-release Z2 record (`research-release` block, see research `docs/publishing-architecture.md`).

What does **not** change:
- Published papers and datasets stay frozen. Research `main` has **no** CI enforcing this today. Draft PR #6 adds a check that blocks any modify or delete under `datasets/` and `corrections/` against the PR base, and fails if the base cannot be resolved. Until #6 merges, the cap rests on review alone. Z2 may make ACCEPT conditional on #6 merging first.
- Every release still needs its own Z2 ratification. This cap lets Z1 *propose* infrastructure; it grants no publish authority.
- Z3 executor stays TBD.

Suggested resource cap: 20 units/cycle, written in the registry's existing per-zone unit so the row matches the other rows. Whether the registry should keep the per-cycle unit at all is a separate question and is not decided here.

### 2.1 Release pipeline is proposal-only until the human gate exists

Research PR #6 at the pinned head contains more than layout and checks:

- `.github/workflows/publish.yml` runs on tags `paper-*-v*` and `dataset-*-v*` and holds `contents: write`, `id-token: write` and `attestations: write`. It reads the secret `OPERATIONS_READ_TOKEN` and declares `environment: production`.
- `scripts/z2_release_auth.py` and `scripts/build_release_manifest.py` bind a release to an operations Z2 record.
- `infra/supabase/migrations/20261024000000_publication_catalog.sql` is a real migration, not a design note.

Under this cap those files may be **proposed and reviewed**. They may not be **enabled**: no tag matching the release patterns is pushed, and the migration is not applied, until preconditions P1 to P3 in §2.2 are verified by Z2. The cap still grants no publish authority.

### 2.2 Preconditions Z2 verifies before ACCEPT takes effect

- **P1.** Research PR #6 is merged at a head Z2 has re-pinned. The frozen-path check exists on research `main`, so the cap no longer rests on review alone.
- **P2.** In research repository settings, a `production` environment exists with a required human reviewer, and a tag ruleset protects `paper-*` and `dataset-*`. Z2 confirms it directly in the settings; this candidate cannot see them.
- **P3.** Research `main` branch protection requires the `validate` job from `ci.yml`, so a failing frozen-path check blocks a merge instead of reporting after one.

Until P1 to P3 hold, ACCEPT records the cap but the pipeline in §2.1 stays disabled.

## 3. Options for Z2

| Decision | Effect |
|:--|:--|
| ACCEPT | Apply §4. PR #6 is in scope as a Limited-cap proposal. The release pipeline stays disabled until §2.2 P1 to P3 are verified. |
| EDIT | Narrow or widen the cap text; Z1 revises. |
| REJECT | Z-011 stays READ-ONLY. PR #6 should be closed or moved to operations as a design proposal. |

## 4. Exact edit to `ZONE_REGISTRY.md` (apply only on ACCEPT)

Add a row to **Limited-Cap Zones**:

```
| Z-011 | research | Frozen papers archive + publishing infrastructure | Publishing infrastructure only; datasets/ and corrections/ append-only; no release without per-release Z2 record | TBD | 20 units/cycle | ⚠️ LIMITED |
```

Remove the Z-011 row from **Read-Only Zones** and leave the table with a "None" row.

Update the totals line:

```
**Total active:** 13 zones (9 full-cap + 4 limited-cap + 0 read-only)
```

`CLAUDE.md` "Caps by zone" also lists `research` under Read-only. On ACCEPT it should move to the Limited cap line with the same text, via the normal `CLAUDE.md` change path.

## 5. Cost

- One Z2 slot to rule.
- Z2 verifies P1 to P3 once each, in research repository settings and on research `main`.
- On ACCEPT: one small PR touching `ZONE_REGISTRY.md` and `CLAUDE.md`.

## Falsifier

The cap is wrong, and Z-011 should go back to READ-ONLY, if any of these happens at any point after ratification. The falsifier has no time window and does not expire: it is checked on events (each research PR merged to `main`, each research release), per Q-TEMPORAL-DISSOLUTION-01. Timestamps below only order events.

1. Any research PR merged after ratification modifies or deletes a file under `datasets/` or `corrections/`, other than a `README.md` navigation file, which matches research `scripts/inventory.py` `FROZEN_EXEMPT_NAMES`. Z2 records research `main`'s SHA at ratification as `BASE`. Check, on each merge event: `git fetch origin main`, then take the merge commit SHA from the event as `MERGED` and require `git merge-base --is-ancestor MERGED FETCH_HEAD`; then run `git log --first-parent --no-renames --diff-filter=MDT --name-status BASE..MERGED -- datasets corrections` on research. A failed fetch, or a `MERGED` that is not on the fetched `main`, fails closed: the check is reported as not run, never as passed. A stale `origin/main` is never used. `--no-renames` turns a move into delete + add, so it is caught; `T` catches a file swapped for a symlink. Changes before `BASE` do not count.
2. Any GitHub Release published after ratification has no operations Z2 record that verifies for its tag. Releases are selected by `publishedAt`, not `createdAt`, so a draft created before ratification and published after it is included. Check, for each such tag, against the commit that was actually published, never the movable tag: download the release's own `manifest.json` (`gh release download <tag> -p manifest.json`) and take its `git_commit` as `PUBLISHED`. `PUBLISHED` must equal the `git_commit` in the Z2 record's research-release block, and the tag's commit on GitHub at check time must still equal `PUBLISHED`, read from the server, never a local ref: `git ls-remote origin 'refs/tags/<tag>^{}' 'refs/tags/<tag>'` (the peeled `^{}` line for an annotated tag, else the plain line). A moved tag trips the falsifier; a failed lookup counts as the check not run, never as passed. Then, in a clean research checkout, run `validate_repository.py --release <tag> --commit PUBLISHED --operations <checkout>`. A missing manifest trips the falsifier. Each release is judged at its own published commit, not at current `main`. Protected release tags (tag ruleset) and immutable releases, where offered, are a precondition Z2 sets up on ACCEPT; this check still runs without trusting them. The record must also predate the release, judged by server-recorded times only, never by a commit date (a committer date can be set freely): find the first operations `main` commit that carries its `z2_hash` (`git log --first-parent --reverse -S <z2_hash> --format=%H origin/main -- z1-inbox/INDEX.yaml | head -1`), take the `merged_at` of the merged pull request that landed it (`gh api repos/humanaios-ui/operations/commits/<sha>/pulls --jq '[.[] | select(.merged_at)][0].merged_at'`), and compare it with the release's `publishedAt` (`gh release view <tag> --json publishedAt`). A record commit that did not land through a merged pull request has no server-recorded time and trips the falsifier. A record that landed after publication, or is missing, trips the falsifier even if it verifies today.

3. Any tag matching `paper-*` or `dataset-*` is pushed on research before §2.2 P2 is verified by Z2, or any release is created by `publish.yml` while its `production` environment has no required reviewer. Checked per tag-push event, read from the repository's settings and the run's deployment record. A settings read that fails counts as the check not run, never as passed.

Any one trips the falsifier. Z1 files the revert candidate.
