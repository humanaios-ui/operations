# Q-ZONE-Z011-RESEARCH-CAP-01 — Change Z-011 (research) from READ-ONLY to LIMITED cap

**Status:** Z1 proposal. Unratified. Awaiting Z2 signature.
**Authority effect:** NONE until ratified. This file changes no row in `ZONE_REGISTRY.md`. The exact edit is in §4 for Z2 to apply.
**Pinned at:** operations `main` `a9fd403`; research PR #6 head `d0579c6`.

---

## 1. Why

`ZONE_REGISTRY.md` lists Z-011 `research` as 🔒 READ-ONLY ("Frozen papers archive", no proposals).

On 2026-10-24, in Claude session `session_01Sq12pdVorzji1sVLmLHd98`, the operator (Night) was asked whether to work in `research` or stage a proposal in operations. The answer selected was **"Night unlocks research"**. Z1 then opened draft PR humanaios-ui/research#6 (publishing foundation).

That answer is an in-chat instruction. It is not a ratified zone change. The independent review on PR #6 flagged the drift: the registry still says READ-ONLY while the PR says unlocked. This candidate either regularizes that instruction or reverses it.

## 2. Proposal

Move Z-011 to the Limited-Cap table with this proposal cap:

> **Publishing infrastructure only.** Layout READMEs, `registry/`, `scripts/`, `tests/`, `.github/`, `docs/`, and design-only `infra/`. No edit or delete of any file under `datasets/` or `corrections/` (append-only). No release without a per-release Z2 record (`research-release` block, see research `docs/publishing-architecture.md`).

What does **not** change:
- Published papers and datasets stay frozen. The research CI already enforces append-only for `datasets/` and `corrections/` against the PR base, and fails if the base cannot be resolved.
- Every release still needs its own Z2 ratification. This cap lets Z1 *propose* infrastructure; it grants no publish authority.
- Z3 executor stays TBD.

Suggested resource cap: 20 units/cycle (same order as Z-009 docs, content-only).

## 3. Options for Z2

| Decision | Effect |
|:--|:--|
| ACCEPT | Apply §4. PR #6 is in scope as a Limited-cap proposal. |
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
- On ACCEPT: one small PR touching `ZONE_REGISTRY.md` and `CLAUDE.md`.

## Falsifier

The cap is wrong, and Z-011 should go back to READ-ONLY, if either of these happens within 90 days of ratification:

1. Any merged research PR modifies or deletes a file under `datasets/` or `corrections/`. Check: `git log --diff-filter=MD -- datasets corrections` on research `main`.
2. Any GitHub Release exists on research without an operations Z2 record that verifies for its tag. Check: rerun `validate_repository.py --release <tag> --operations <checkout>` for every release.

Either one trips the falsifier. Z1 files the revert candidate.
