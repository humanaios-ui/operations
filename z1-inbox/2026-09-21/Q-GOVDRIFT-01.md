# Q-GOVDRIFT-01 — Derived-artifact convention, and four items only Z2 can close

**Proposal ID:** Q-GOVDRIFT-01
**Date:** 2026-09-21
**Authority:** Z1 (Claude) proposes; Z2 (Night) ratifies
**Tier:** Tier 1 (governance convention + registry corrections)
**Session:** S-092126-01
**Registry SHA pinned:** `026322ec1e7f5ab4f6cbd4a624a5c253fcb94489` (local HEAD ≡ `origin/main`, 0 behind — IC-030 satisfied)
**Status:** Awaiting Z2 ratification

---

## Executive Summary

A trace of REGISTERED.md's collateral documents surfaced four drift defects. Three
were mechanically fixable by Z1 and are fixed in the accompanying PR. This block
asks Z2 for the part Z1 cannot do: **a stated convention** that would have prevented
all of them, and **four corrections inside Z2-owned artifacts**.

The four defects were not four mistakes. They were one mistake made four times:
**a hand-maintained mirror of state that a machine already knows, with no gate.**

| Defect | Mirror | Source of truth it restated |
|:---|:---|:---|
| 8 present files marked 🔴 MISSING | `GOVERNANCE_FILES.md` status column | the filesystem |
| Registry described as "YAML array" | `GOVERNANCE_FILES.md` purpose cell | `REGISTRY_SPEC.md` |
| `operations/NF_LEDGER.jsonl` | `NF_LEDGER_SCHEMA_v1.md` header | `ledgers/NF_LEDGER.jsonl` |
| "4,093 lines, 142 entries" | `REGISTERED_FAILURE_MODES.md` | `REGISTERED.md` (4,992 / 154) |

Two further defects found while fixing those, both red on `main` before this session:

| Defect | Mirror | Source of truth |
|:---|:---|:---|
| `counts.candidates: 69` | `z1-inbox/INDEX.yaml` header | the `candidates:` list (67 at discovery) |
| IC-035 / IC-037 each defined twice | new entries' `id:` | the live registry |

*Both figures in the fifth row are the values at discovery (SHA `026322e`), not
current state: the declared count read 69 while the list held 67. The list has
since grown — this block's own submission and the seven candidates from #436 —
so the live number is not 67 and is not meant to be read as one. The defect was
the gap between the two, which `.z1-control/validate.py` now reports and blocks.*

Six for six. The pattern is the finding.

---

## Root cause

`REGISTRY_SPEC.md` already states the governing law, under **DERIVED VIEWS**:

> *"Every mirror, cache, summary, or database view is DERIVED and non-authoritative.
> Where a mirror and the canonical file disagree, the file wins and the mirror is
> repaired."*

The law is correct and was never applied as a law. It was applied three times as an
implementation — `.doc-control/`, `.z1-control/`, `.tool-control/`, each an SSOT plus a
renderer plus a blocking `--check`. Each works. Nothing that passed through those
planes drifted.

Every artifact that drifted was outside them:

- `GOVERNANCE_FILES.md` — no control plane, **and not in `document-registry.yaml`**, so no
  review cadence ever applied to it either.
- `REGISTERED_FAILURE_MODES.md` — no control plane, not in the document registry. Its
  scanner has supported `--verify-doc` since it was written; **no workflow ever ran it.**
- `NF_LEDGER_SCHEMA_v1.md` — no control plane.

So the gap is not that three files went stale. It is that **the derive-and-block pattern
is opt-in.** A new summarizing document is born ungated, and stays ungated until somebody
remembers. Memory is the control that failed.

### The sharpest instance

`REGISTERED_FAILURE_MODES.md` exists to argue that hand-copied counts drift. Its own
header says every count *"is produced by that tool and verified against it by
`scan --verify-doc`, which fails if this document drifts."* That sentence was false: the
verifier was real, but unwired. The document asserting RFM-11 had become an instance of
RFM-11 — which is precisely the self-application its opening paragraph claims has never
been done.

---

## What Z1 has already done (in the accompanying PR — no ratification required)

1. **`.gov-control/`** — new control plane on the established pattern.
   `governance-files.yaml` (SSOT) → `render.py` → `GOVERNANCE_FILES.md`, with
   `validate.py` and a blocking `governance-files.yml` workflow. **The `Status`
   column is derived by stat-ing each declared path at render time.** There is no
   `status` field in the SSOT, and `validate.py` rule 2 rejects one if added
   (including nested). A file can no longer be reported missing while it sits in the
   tree, because nobody types the answer.
2. **Wired `scan --verify-doc` into `findings-registry.yml`**, and added
   `REGISTERED_FAILURE_MODES.md` and the scanner to that workflow's `paths:` filters —
   a gate that does not fire on the file it guards is the IC-041 shape.
3. **Re-measured the failure-mode map** from tool output (154 entries, 119 defects,
   616 opportunities, 80.7% FPY, 193,182 DPMO). `verify-doc` now passes.
4. **Corrected the NF_LEDGER path** and marked the root `z2_ratification_gate.yml` as
   the non-executing design draft it is.
5. **Registered both orphans** in `document-registry.yaml` (HAIOS-GOV-003, HAIOS-RES-010),
   status `draft` — approval is the owner's act.
6. **Resolved a committed merge conflict** in `z1-inbox/INDEX.yaml` (markers `=======` /
   `>>>>>>> origin/main` were on `main`, so the file did not parse and both `.z1-control`
   gates were red). Union resolution; no entry lost — 67 candidates / 37 records at
   that point. The branch has since merged `main` (#436), so the current index holds
   **75 candidates / 37 records**: main's 74 plus this block, verified by q_id set
   difference with nothing dropped from either side.

---

## What this block asks Z2 to decide

### ASK 1 — Ratify the derived-artifact convention (the upstream fix)

Add to `REGISTRY_SPEC.md` **DERIVED VIEWS**, as a rule rather than a description:

> Any file that restates state held elsewhere — counts, statuses, inventories,
> file lists, schedules — is a DERIVED VIEW. A derived view must declare its
> source, be produced by a renderer, and be held to its source by a CI check that
> blocks the merge. A derived view that is hand-maintained is a defect on sight,
> independently of whether it currently happens to be accurate.

Consequence: the next `GOVERNANCE_FILES.md` cannot be created ungated, because being
ungated is itself the violation — no one has to notice it has gone stale first.

**Falsifier.** If, 90 days after ratification, a hand-maintained restatement of
machine-known state has been introduced anywhere in `operations/` *and* CI accepted it,
the convention has failed as a control and reverts to advisory. Mechanically checkable:
any new root-level `.md` carrying a count, a status column or a file inventory, with no
`ssot:` declaration in `.gov-control/governance-files.yaml` and no renderer.

**Prediction (pre-registered):** zero such files at 90 days. The three existing control
planes have produced zero drift incidents between them; the claim is only that the rule
generalizes what already works.

**Resource cost:** one `REGISTRY_SPEC.md` amendment. Enforcement reuses gates that exist.

### ASK 2 — IC-035 and IC-037 are each defined twice (BLOCKING — `main` is red)

`findings-registry.yml` is declared BLOCKING and its header states *"main is at 0 hard
failures (audit A2, S-070726) so blocking is safe."* That is no longer true:

| ID | First entry | Second entry |
|:---|:---|:---|
| IC-035 | `REGISTERED.md:1576` — canonical-workflow-not-documented (2026-06-09) | `REGISTERED.md:4810` — q-witness-phase-0-resource-allocation-undefined (2026-09-20) |
| IC-037 | `REGISTERED.md:1597` — legibility-test-scorer-conflation (2026-06-09) | `REGISTERED.md:4870` — legal-ethics-pre-assessment-not-commissioned (2026-09-20) |

The S-092026-01 red-team session assigned numbers without checking the live registry —
the condition G-4 / IC-030 exists to prevent. **Z1 has not touched these.** Renumbering
is a write to the canonical registry and belongs to Z2.

Highest IC currently in use is **IC-059**. Proposed: the 2026-09-20 pair becomes
**IC-060** and **IC-061**, with the June entries left untouched (they hold the external
citations), and a superseded-by pointer not used, since neither supersedes anything —
this is an ID collision, not a correction.

**Note this is an append-only file.** Renumbering two entries is therefore itself a Z2
judgment about what "never renumber" means when an ID was issued twice; Z1 states the
options and does not choose:
- **(a)** renumber the newer pair to IC-060/061 — restores uniqueness, but edits entries in place;
- **(b)** append two corrected entries and mark the 2026-09-20 pair SUPERSEDED with forward
  pointers — pure addition, consistent with the never-delete rule, leaves the collision
  visible in history as the record of what happened;
- **(c)** neither, and whitelist the pair in the validator as documented collisions, the way
  F-32/F-33 are whitelisted as honest gaps.

Z1's reading is that **(b)** is the option most consistent with the spec's own
"corrections happen by addition" rule, but the call is Z2's.

---

**RESOLVED 2026-09-21.** Z2 (Night) ratified option (b), in-session, per
`REGISTRY_SPEC.md`'s "In-session approval + formal declaration" receipt form —
the same form used for the spec's own 2026-08-04 activation.

Executing it surfaced a conflict this ask's own drafting had not caught: option
(b)'s bullet says "mark SUPERSEDED with forward pointers," but the "Proposed"
paragraph two above it already says "a superseded-by pointer not used, since
neither supersedes anything." Those disagree, and `check_id_collisions()` in
`tools/registered_findings_validator_v1_0.py` settled which one governs —
it counts literal `id:` occurrences only, with no exemption for `status` or
`superseded_by`, so a duplicate id marked SUPERSEDED still hard-fails. Its own
message says as much: *"deduplicate before commit."* `superseded_by` would also
have been the wrong semantic regardless — these entries carry
`zone2_ratification: "Night · 2026-09-21 · issue #429 ratification"`; they are
live, already-ratified findings under the wrong number, not findings later
found obsolete.

Executed per the file's own precedent for exactly this shape of problem —
`F-RLHF → F-20` (documented three bullets above): `id:` corrected in place,
`name:` unchanged, no `superseded_by`, one conventions-list line recording
what happened and why. IC-060 = the 2026-09-20 entry filed as "IC-035";
IC-061 = the one filed as "IC-037." The June IC-035/IC-037 entries — which
hold every existing citation, including in `REGISTERED_FAILURE_MODES.md` —
are untouched.

`tools/registered_findings_validator_v1_0.py --input REGISTERED.md`: **WARN**,
zero `FAILURES` (was 2). `registered_failure_mode_scan_v0_1.py scan --verify-doc
REGISTERED_FAILURE_MODES.md`: PASS, no changes needed there — its cited counts
did not move. Full local gate sweep green, including the exact `grep -q
FAILURES` shape `findings-registry.yml` uses to gate.

Asks 1, 3 and 4 remain open.

### ASK 3 — RFM-17 header staleness on `REGISTERED.md`

Header declares `**Last updated:** August 15, 2026`; newest dated content is 2026-09-20.
Z1 did not edit the header — it is the canonical file. Z2 to refresh, or rule that the
header tracks schema-version changes rather than content and have the scanner stop
flagging it.

---

**RESOLVED 2026-09-21.** Z2 (Night) ratified: refresh the header date. In-session
receipt, same form as ask 2.

Set to `September 20, 2026 (S-092026-01-red-team-audit)` — the newest
`date_registered` in the file per `evaluate_header_staleness()`'s own formula (max
of every `date_registered:` and every `### YYYY-MM-DD —` heading). Not "today"
(2026-09-21): nothing in the file carries that as a `date_registered` — the 16
occurrences of "2026-09-21" already present are `zone2_ratification`/`date_ratified`
fields and my own ask-2 prose, none of which the scanner counts, and inventing a
`date_registered` the file doesn't have would be a different lie than the one being
fixed. `python3 tools/registered_failure_mode_scan_v0_1.py scan` confirms:
`[RFM-17] Header staleness — PASS`.

Fixing this exposed a fourth stale table in `REGISTERED_FAILURE_MODES.md` — the
FMEA `Occurrence` column, ten cells stale (RFM-06 58/137, RFM-07 8/137, RFM-08
5/137, RFM-09 30/137, RFM-10 25, RFM-11 10/45, RFM-12 1, RFM-14 2, RFM-15 1,
RFM-17 1), invisible to `_verify_taxonomy_rows` because its rows aren't
bold-formatted (`| RFM-06 |` vs `| **RFM-06** |`) — so it drifted through
every one of the three prior review rounds undetected, including the round
that had just regenerated the same ten numbers three headings above it in the
same file. Regenerated to match the scan, and `_verify_taxonomy_rows` extended
to also match this row shape (anchored on the literal `UNSCORED` token the
table's own honesty rule guarantees is present in every Severity cell today),
proven by deliberately breaking an FMEA-only cell and confirming
`verify-doc` fails on it alone (exit 1), then passes restored (exit 0).

Asks 2 and 3 now resolved; asks 1 and 4 remain open. `REGISTERED.md`'s only
change beyond ask 2 is this header line. Full local gate sweep green,
including `self-test` (existing fixtures unaffected by the refactor) and the
temporal-dissolution gate in CI mode.

### ASK 4 — RFM-15 ratification-hash substitution (8 instances)

`REGISTRY_SPEC.md` specifies `sha256(candidate | by | at | decision)` — 64 hex chars.
Present in the registry: a 7-char git SHA (`e8a501f`), a 63-char near-miss, and six
unterminated `sha256(Q-…` expressions that are labels rather than digests.

This intersects a ruling already on the books — `Z2_RULING_MERGE_IS_RATIFICATION.md`
("the hash echo is retired; the merger and the merge date sign it"). If that ruling
supersedes the 64-hex requirement, then **`REGISTRY_SPEC.md` still states the old rule**
and RFM-15 is scoring against a retired spec. That is an **AMBIGUITY** per the CLAUDE.md
callout table — two governance decisions in conflict on one topic. Z2 to say which
governs, so the scanner can be corrected in whichever direction is right.

---

## Falsifier summary (CI-checkable)

| Ask | Falsifier |
|:---|:---|
| 1 | A hand-maintained restatement of machine-known state merges within 90 days |
| 2 | `registered_findings_validator_v1_0.py` still reports `REG_ID_COLLISION` after the decision lands |
| 3 | `scan` still reports RFM-17 FAIL after the decision lands |
| 4 | `REGISTRY_SPEC.md` and the merge-is-ratification ruling still specify different signature forms |

---

## Receipt / scope note

Every number in this block is tool-produced:
`python3 tools/registered_failure_mode_scan_v0_1.py scan --verify-doc REGISTERED_FAILURE_MODES.md`
and `python3 tools/registered_findings_validator_v1_0.py --input REGISTERED.md`.
Line numbers are at the pinned SHA. No claim here rests on a count typed by hand —
which, given the subject, is the minimum this block owes its own argument.
