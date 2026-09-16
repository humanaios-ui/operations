---
id: "Q-MERGE-SCOPE-01"
name: "A PR with no Q-ID has no signing path, so the merge ratifies whatever it happens to carry — #343 merged 21 files against a five-item enumerated scope"
status: CANDIDATE
class: MIXED
date_registered: "2026-09-16"
date_origin: "2026-09-16"
session_registered: "S-091626-01-ratify-gap-fixes"
zone2_ratification: null
tags: ["governance", "ratification", "scope", "receipt-gap", "audit-false-pass", "tier-2"]
related: ["IC-031", "IC-041", "IC-050", "H-GOV-01", "F-CAND-SELF-EXEMPT-RULE-01"]
superseded_by: null
source_pr: "humanaios-ui/operations#343"
---

# Candidate Block: Q-MERGE-SCOPE-01 — the ratifying act did not cover what it ratified

**Z1 Proposer:** Claude (AI agent)
**Date Submitted:** 2026-09-16 (20:48 UTC / 15:48 CDT, `bash_tool` verified per P22)
**Pinned at:** `operations` @ `4cf942d` (merge of #349); subject commit `880c01f` (merge of #343)

---

## RECEIPT-GAP

Per CLAUDE.md's callout table, a **RECEIPT-GAP** is "claim in transcript not found in tree." This is the
inverse and the same instrument: **tree not found in claim.**

`Z2_RULINGS_2026-09-16.md` Ruling 1 ACCEPTs PR #343 with an explicitly enumerated scope — five items.
PR #343 merged as `880c01f` carrying **21 files across four separable workstreams**. The merge is the
ratifying act for a PR with no Q-ID, so whatever the merge carried is now canonical, whether or not any
ruling named it.

This was found by reconciling the ruling against the merge commit, not by reading either one.

## Reconciliation — claim vs. tree

**Ruling 1's enumerated scope:** `tools/molting_protocol_diff_v1_0.py` at 1.1.0 · the advisory
`.github/workflows/molt-tier-check.yml` · the 24-test suite wired into `quality-baseline` · the
`molt_tier_claimed` PR-template field · the `MOLT_STATE.md` tier table, classifier version block and
directional under-claim falsifier.

| Merged file | Ratifying act |
|:--|:--|
| `tools/molting_protocol_diff_v1_0.py` | Ruling 1 (item 1) |
| `.github/workflows/molt-tier-check.yml` | Ruling 1 (item 2) |
| `tools/tests/test_molt_tier_classifier.py` | Ruling 1 (item 3) |
| `.github/PULL_REQUEST_TEMPLATE.md` | Ruling 1 (item 4) |
| `MOLT_STATE.md` | Ruling 1 (item 5) |
| `tools/README.md`, `tools/skills/…/SKILL.md`, `TOOLS_MANIFEST.md`, `tools-manifest.yaml`, `tools/tests/test_tool_gap_scaffolds.py` | Consequential to item 1 — regenerated or corrected because it changed. Defensible as in-scope; recorded rather than assumed |
| `.github/workflows/quality-baseline.yml` | Ruling 1 (item 3) **in part** — it also wires `test_ratify_index_write.py`, which item 3 does not name |
| `SESSION_RITUALS.md` | Ruling 3 (v6.4.2 bump), applied ahead of signature by its own terms |
| `z1-inbox/2026-09-15/Q-MOLT-LEDGER-SCAN-01.md` | Ruling 2's **subject**. Ruling 2 is unsigned; a candidate block landing in the tree is not its registration, so this is correct |
| `z1-inbox/2026-09-16/Z2_RULINGS_2026-09-16.md`, `z1-inbox/INDEX.yaml`, `Z1_INBOX_INDEX.md` | Transcript and index bookkeeping |
| **`.z1-control/ratify.py`** (+164) | **The merge only.** Tier 2 gate path. Named by Ruling 6, which is `AWAITING Z2` and unsigned |
| **`tools/tests/test_ratify_index_write.py`** (+256) | **The merge only.** Named by Ruling 6, unsigned |
| **`ledgers/NF_LEDGER.jsonl`** (+7) | **The merge only.** The first seven RESOLVE rows ever written; append-only, Brier `0.2075` |
| **`ledgers/PRACTICE_RESOLUTION_MAP.md`** (+135) | **The merge only.** The file states of itself "Z1 map — **not ratified**" |
| **`.gitleaks.toml`** (+35) | **The merge only.** A security-scanner allowlist |

**Five items are unscoped, which is not the same as unratified.** An earlier draft of this block said they
carried "no ratifying act," which contradicts its own mechanism claim three paragraphs above: the merge
*is* the ratifying act for a PR with no Q-ID, so these five were ratified — by the merge, implicitly, and
outside the enumerated scope of the decision that authorised it. Corrected in place per P2, because the
distinction is the whole question: an unratified change would be an unauthorised one, and the disposition
would be revert-or-ratify. These are authorised and canonical. What is missing is a *decision that names
them*, which is a record defect, and the dispositions below are about the record.

The framing carried into this session — "`ratify.py` 1.2.0 landed inside #343's merge" — still
understated it. `ratify.py` is the one that matters most, being a Tier 2 gate and the signing tool
itself, but it is not the only one.

## What cannot be done about it

**Ruling 1's scope sentence must not be edited to include them.** CLAUDE.md, "Cannot do (by design)":

> Change Z2 decision retroactively (only emit new RATIFY event with new hash)

Widening an enumerated scope after the fact, to make the record match what happened, is that prohibition
exactly. It would also be self-serving in the specific sense the validator exists to make expensive: the
party that wrote the overrun would be editing the decision that failed to cover it. P2 (document
correction, modify the original) does not apply — P2 corrects a description that was wrong when written;
Ruling 1's scope was accurate for the decision Night took.

## IC candidate — the mechanism, not the incident

**`IC-CAND-MERGE-RATIFIES-UNSCOPED-01`:** a PR carrying no Q-ID has no signing path, so its ratifying act
is the merge, and nothing compares what merged against what was accepted.

Ruling 6 already records the asymmetry in one line: *"a PR changing a gate has a weaker signing path than
a candidate block changing prose."* This is that asymmetry costing something measurable. A candidate
block's `z2_hash` pins content, so `ratify.py --verify` shows any drift; a merge pins nothing, and the
enumeration lives in prose that no gate reads.

Same shape as the class already registered this session: the principle existed and was documented, the
mechanism was absent. That is limb (a) of **H-GOV-01**'s promotion gate, and this is the sixth instance.

## Three dispositions, for Z2

Each is a **new RATIFY event**, not an amendment.

1. **Ratify with `880c01f` as the named subject.** A new ruling naming the merge commit and accepting it
   as merged. **The sha is the subject, not the signature** — a commit sha pins the merged tree and
   nothing else, `ratify.py --verify` cannot check it, and CLAUDE.md's contract is
   `sha256(candidate | by=Night | at=timestamp | decision=…)`. So the ruling carries its own Z2 digest in
   the normal way and *names* `880c01f` as what it decides about. Strongest pin — a sha cannot drift the
   way an enumeration can — but it accepts five items wholesale, ledger rows included, on the strength of
   them already being in the tree.
2. **Ratify the unscoped items individually.** Sign Ruling 6, which names `ratify.py` 1.2.0 and its test
   but is currently `AWAITING Z2`; then separate decisions for the `NF_LEDGER` resolutions,
   `PRACTICE_RESOLUTION_MAP.md` and `.gitleaks.toml`. Slowest, and the most honest about the fact that
   four unrelated things rode one merge.
3. **Both.** Option 1's ruling — own digest, `880c01f` as named subject — with option 2's enumeration
   written beneath it, so the record carries the pin and the reasoning.

**Z1's read is (3)**, stated as a recommendation and not a decision. The sha is what actually happened and
is checkable; the enumeration is what a reader needs in order to know *what* happened. Option 1 alone
leaves the same prose-free record that produced this gap; option 2 alone leaves no pin.

## Proposed prevention

Not applied — this is a Z2 call, and one of these is itself Tier 2.

- **P1 — a PR touching a Tier 1 or Tier 2 path requires a Q-ID.** Routes the PR through `ratify.py`, so
  a Z2 signature exists and pins the candidate's bytes. Costs a candidate block per gate PR.
- **P2 — name the merge sha in the ruling.** Cheapest; gives the decision an immutable subject. Detects
  nothing on its own.
- **P3 — a check comparing the merged file list against the ruling's declared scope.** The only one of
  the three that can actually fail. Needs the scope to be machine-readable, which today it is not.

**P1 and P3 are not alternatives — P3 depends on P1 being extended.** An earlier draft of this block
offered them as either/or, which was wrong and is corrected here. `ratify.py` signs the candidate's
*bytes*; it never compares the candidate's scope against the merged file list, and nothing else does
either. A Q-ID alone therefore produces a signature that says "Night decided about this document" and
still cannot detect a merge carrying files the document never mentioned — which is this incident exactly.

For P3 to be buildable, P1 has to be extended: the candidate block must declare its scope as a
**machine-readable file list** (front-matter, alongside the `source_pr` field these blocks already
carry), not as the prose sentence Ruling 1 used. Then P3 is a diff of two lists and the signature covers
the list, because the list is part of the bytes being hashed.

That changes the cost estimate. P1-plus-scope is more work than "require a Q-ID," and P3 is cheap once it
exists. The ordering is P2 (independent, now) → P1-with-scope → P3.

## Falsifier

**If P1-with-scope and P3 are ratified and applied, then for the next 10 PRs touching a Tier 1 or Tier 2
path, the set of files in the merge commit is a subset of the machine-readable scope declared in that
PR's ratifying act.**

Stated against P1-with-scope *and* P3 together, not either alone: P1 without a declared scope produces a
signature that cannot be compared to anything, so it could not make this falsifier pass and naming it
here would have made the prediction unfalsifiable by construction.

Falsified if any such PR merges carrying a Tier 1 or Tier 2 path that its ratifying act does not name.
Measured by reconciling each merge commit against its ruling, the same walk performed above.

Directional on purpose: a merge carrying **fewer** files than the ruling scoped is not a falsification —
that is a decision not fully executed, which is a different failure and one the tree makes visible. The
failure being measured is canon acquiring content nobody ratified.

**Null result is informative.** Ten clean PRs do not prove the mechanism works; they establish that the
gap is not routine, which is itself unknown today — this is the first reconciliation of its kind, so the
base rate is unmeasured.

## What this block does NOT claim

- It does **not** claim the five unscoped items are wrong, unsafe, or should be reverted. `ratify.py`
  1.2.0 fixes a write path that had never worked; the seven RESOLVE rows are the ledger's first real
  measurements. The defect is in the ratifying act, not the content.
- It does **not** claim Night was misled. Every one of the five was described in this session before the
  merge, and `ratify.py` 1.2.0 was flagged in writing on both #344 and #343 as exceeding Ruling 1's
  scope. The gap is that the *record* does not carry what the conversation did.
- It does **not** assign the overrun to the merge. The items were pushed to the branch by Z1 under a
  single-branch instruction, after Ruling 1 was given. Z2 merging a branch is not Z2 re-scoping it.

---

## Z2 Review Checklist

*(Heading and `- [ ]` format are what `.z1-control/render.py` parses — an earlier draft used
`## Z2 checklist` with a numbered list, which the parser does not recognise, so all eight decisions were
silently absent from the generated queue in `Z1_INBOX_INDEX.md`. A checklist nobody is shown is the same
failure class this block is about.)*

- [ ] Disposition for the scope gap: option 1, 2 or 3 above.
- [ ] Ruling 6 — `ratify.py` 1.2.0 and `tools/tests/test_ratify_index_write.py`. It names the pair but is
      `AWAITING Z2` and unsigned.
- [ ] The seven `NF_LEDGER.jsonl` RESOLVE rows — ratify as written, or dispute. Append-only: a wrong
      resolution is correctable only by a DISPUTE event, never by deletion.
- [ ] `ledgers/PRACTICE_RESOLUTION_MAP.md` — it declares itself unratified; ratify, or leave it so.
- [ ] `.gitleaks.toml` — a security-scanner allowlist, merged with no decision naming it.
- [ ] Prevention: P2 now (independent), then P1-with-scope, then P3 — or none. P1 without a declared
      machine-readable scope does not close this.
- [ ] `IC-CAND-MERGE-RATIFIES-UNSCOPED-01` — register as IC, or NM.
- [ ] Whether this extends **H-GOV-01**'s `evidence_basis` as the sixth instance. The register is
      append-only and the forward-pointer is Z2's to write; Z1 has not proposed the edit.
