# Candidate Block: Q-GOVGATE-01 — The Z2 Gate Never Ran; z1-inbox Conversion

**Z1 Proposer:** Claude (AI agent)
**Date Submitted:** 2026-09-13
**Pinned SHA:** `758aef32be4d43608a903a078e1280d85a53a15b`
**Branch:** `claude/z1-inbox-z2-conversion-reviews-w54cil`
**Phase:** 0 (control infrastructure)
**Status:** AWAITING Z2 RATIFICATION

---

## §A Position · Destination · Probability

**Position:** `operations` pinned at `758aef3`. CLAUDE.md describes a Z2 serial gate enforced by
CI: "Cannot execute without Z2 hash (CI enforces)", "CI: no write without Z2 hash", and a
`z2_ratification_gate.yml` whose four listed checks include falsifier presence. The workflow
exists. **It has never executed a single step.**

**Destination:** make the gate run, and give z1-inbox the SSOT → validator → renderer → CI shape
that `.doc-control/` and `.tool-control/` already prove out, so that "what does Z2 owe a decision
on, and for how long" is a query rather than an archaeology exercise.

**Probability:** **75%** that the repaired gate stays green on `main` for 30 days without an
exception being carved for it. Held below 90% for the same reason Q-TOOLCONTROL-01 held its
number down: the coverage rule is strict, and a contributor who drops a file into `z1-inbox/`
without touching `INDEX.yaml` gets a failed PR. That friction is exactly where a new gate usually
gets disabled instead of obeyed.

---

## The finding

`.github/workflows/z2_ratification_gate.yml` carries **two top-level `name:` keys** — line 1 and
line 111. GitHub rejects a workflow with duplicate top-level keys. The result is not a visible
error: it is a run that completes in **zero seconds with zero jobs and `conclusion: failure`**,
which in the Actions list is indistinguishable from a gate that ran and failed.

Measured, not inferred:

| | |
|---|---|
| Total runs of the workflow | **122** |
| Runs that executed ≥ 1 job | **0** |
| Runs concluding `failure` | **122** |
| Present in the file's first commit (`2937821`, #267, 2026-09-10) | **yes**, at line 108 |

Run #5 and run #122 have identical shape: `created_at == run_started_at == updated_at`, jobs
`total_count: 0`. The gate was born dead and stayed dead for its entire life, across every merge
to `main` in that window.

**This is the same class as items 2 and 3 of Q-TOOLCONTROL-01** — a governance artifact asserting
an enforcement that is not running. There it was a renderer that did not exist and a `CODEOWNERS`
file shadowed by another. Here it is a gate whose YAML GitHub refuses. Three instances now, which
makes it a pattern rather than three accidents: **this system's characteristic failure is
documenting a control instead of checking that it fires.**

### It is not the only one

Parsing all 43 workflow files the way GitHub does (duplicate keys rejected) finds **four more**
in the same state:

| workflow | defect |
|---|---|
| `drift-monitor.yml` | line 68 — `**Run timestamp:**` begins a line inside a mis-scoped block; YAML reads `*` as an alias |
| `sonarcloud-baseline-auto.yml` | line 226 — `- **Rule:**` inside a Python `"""` heredoc breaks the block mapping |
| `weekly-funding-rescore.yml` | duplicate top-level `permissions:` (lines 3 and 11) |
| `weekly-profile-sync.yml` | duplicate top-level `permissions:` (lines 3 and 11) |

`drift-monitor.yml` has **462 runs, all zero-job**. Five workflows total are decoration. Repairing
the other four is **not** done here — it is out of this change's scope and each needs its own
reading. Routed as an IC candidate below.

---

## What was built

### The gate, repaired

The duplicate key is removed, which is what makes the rest of the file start being true. Three
further defects fixed while it was open:

- `actions/checkout` defaults to depth 1, so the seed-constitution step's `git diff HEAD~1 HEAD`
  had no parent to diff against. It silently produced nothing and the check never fired — a
  second dead check inside the dead gate. Now `fetch-depth: 0` and a diff over the event's own
  range (PR base, or the push's before-SHA): `HEAD~1..HEAD` would still have missed a
  seed-constitution change in any earlier commit of a multi-commit push.
- The `config-lint` job imports `yaml` but never installed PyYAML — it only ever passed by
  relying on what the runner image happens to preinstall. And neither path filter covered
  `seed-publication/**` (what that job checks) or `Z1_INBOX_INDEX.md` (what `render.py --check`
  guards), so both checks were blind to PRs touching only the file they exist to protect.
- The falsifier loop demanded `## Falsifier` of **every** `*.md` under `z1-inbox/`. Eleven of the
  24 files present have none, because they are handoffs, receipts, manifests, templates and cycle
  reports — documents that predict nothing. Un-breaking the gate as written would have failed
  every subsequent PR on files it did not introduce.
- `set -euo pipefail` on the shell steps, and `⚠ Warning:` promoted to a real `::warning::`.

Scoping the falsifier rule to **candidate blocks** follows the rule Q-TOOLCONTROL-02 established:
*a finding becomes blocking only once its count reaches zero.* Which file is which is now
declared, not guessed.

### `.z1-control/` — new, modelled on `.doc-control/`

| file | role |
|---|---|
| `z1-inbox/INDEX.yaml` | SSOT. 14 candidates + 13 records. |
| `.z1-control/validate.py` | The merge gate — 12 structural rules, 2 advisory. |
| `.z1-control/render.py` | `INDEX.yaml` → `Z1_INBOX_INDEX.md`. |
| `Z1_INBOX_INDEX.md` | Generated. "What does Z2 owe a decision on." |

**Why a sidecar and not frontmatter.** `z1-inbox/2026-09-06/MANIFEST.md` sets the inbox
convention: *"Append-only; a correction is a new dated folder, never an edit."* Writing frontmatter
into 24 existing dated drops would be 24 edits. The metadata lives beside them instead — the same
shape `document-registry.yaml` and `tools-manifest.yaml` already use. **No file in any dated
folder was modified by this change.**

**The load-bearing rule is coverage** (rule 3): every `*.md` under `z1-inbox/` is a candidate, a
record, or explicitly `excluded`. This is what stops the index becoming a description of the past
— the same rule whose absence produced the 6-of-136 tool gap.

**`decision_due` is DERIVED** from `submitted + decision_window_days`, so the 48h window in
CLAUDE.md is arithmetic rather than prose. A hand-set value that disagrees is a merge error: the
window cannot be extended by editing the record of it.

**No self-grant.** A terminal status (`ratified` / `edit_requested` / `rejected`) requires
`ratified_by`, a `ratified_at` not preceding submission, a `z2_ruling` that resolves to a file
*indexed as a record*, and a `z2_hash` that actually appears in that ruling. This mirrors
`.tool-control/validate.py`'s existing refusal of a self-granted Z2 tool waiver.

The allowed signer set lives in `KNOWN_RATIFIERS` **in the validator**, not in the index — an
adversarial review round caught that reading `ratifiers:` only from `INDEX.yaml` made the rule
self-defeating, since a proposer could add themselves to the list in the same PR that signs a
candidate. The index's list must now be a subset of the code's, so widening it means editing
`.z1-control/`, a separate CODEOWNERS surface.

**Index paths are contained.** An entry must be a normalized relative path inside `z1-inbox/`.
Without that, `os.path.join(ROOT, "/etc/passwd")` discards `ROOT` and `../` walks out of it, so
an index entry could make CI read an arbitrary file while "checking a candidate's falsifier" —
and a path outside the inbox could stand in for one inside it, defeating coverage.
`.doc-control/validate.py` already applies the same rule to `canonical_path`.

**The SSOT is parsed strictly.** `yaml.safe_load` silently keeps the last of a duplicate key —
precisely the defect that left the Z2 gate dead for 122 runs. Both the validator and the renderer
use a duplicate-key-rejecting loader, so a second `ratifiers:` or `counts:` key is an error rather
than a silent substitution.

### `workflow-lint.yml` — ADVISORY

Parses every workflow the way GitHub does. **Advisory, not blocking**, because four workflows
already fail it; shipping it as a gate would fail every PR on defects it did not introduce. The
promotion condition is written into the file: blocking once those four are repaired.

---

## Gates verified to actually fail

A gate that cannot fail is decoration — which is the entire subject of this block, so the
self-test drives **20 rules red** against a virtual tree (`--smoke-test`):

| test | result |
|---|---|
| Z1 signs its own ratification (`ratified_by: Claude`) | `::error::a candidate cannot grant itself Z2 approval` |
| Ratified with no `z2_ruling` | `::error::requires z2_ruling pointing at the decision record` |
| `z2_ruling` naming a file that does not exist | `::error::does not resolve to a file` |
| `ratified_at` back-dated before `submitted` | `::error::precedes submitted` |
| Undecided candidate carrying a signature | `::error::must not carry ratified_by` |
| `decision_due` hand-stretched to 2026-09-30 | `::error::decision_due is derived (submitted + 2d …)` |
| File on disk, absent from `INDEX.yaml` | `::error::absent from INDEX.yaml` |
| `counts:` falsified to 0 | `::error::counts.candidates says 0 but the index holds 1` |
| Malformed `q_id` | `::error::does not match Q-<AREA>-<nn>` |
| Z1 adds itself to `ratifiers:` and then signs | `::error::not in KNOWN_RATIFIERS` **and** `cannot grant itself` |
| `z2_ruling` not indexed under `records:` | `::error::a decision record must itself be covered by the index` |
| `z2_hash` missing, or absent from the cited ruling | `::error::requires z2_hash` · `does not carry the signature claimed for it` |
| Index path `/etc/passwd`, `../secrets.md`, `z1-inbox/../../etc/passwd` | `::error::not a normalized relative path inside z1-inbox/` |
| `INDEX.yaml` with a duplicate `ratifiers:` key | `::error::duplicate key` (and `safe_load` is asserted to take the last, so the test cannot rot) |
| Candidate with no falsifier and no waiver | `::error::has no falsifier` |
| Waiver on a candidate that has a falsifier | `::error::drop the waiver` |
| Decision field on a record | `::error::must not carry 'status'` |
| Overdue candidate | **warns only** — Z2's clock, not the open PR's defect |
| Clean case | passes with zero errors and zero warnings |

That last row matters: a rule set that only ever rejects is as broken as one that never does.

---

## What the index immediately showed

| | |
|---|---|
| Candidates awaiting Z2 | **11** |
| **Past the 48h window** | **5** |
| Longest wait | **Q-ACAT-BENCHMARK-01**, **Q-DOC-LIFECYCLE-01** — 3 days |
| Already decided (Z2 rulings 2026-09-08) | 3 |
| Falsifier waivers open | 1 |

**The coverage rule fired for real within minutes.** The first CI run of the repaired gate
failed on `z1-inbox/2026-09-13/Q-TOOLCONTROL-02.md` — a candidate block that landed on `main` via
PR #306 while this branch was open, and which nothing had indexed. That is the evidence this
block's falsifier asked for (clause 3), and the same way #304's coverage rule caught an
unregistered tool roughly half an hour after landing. It is now indexed as a candidate awaiting
Z2, which is why the count above is 11 rather than the 8 first measured.

`Q-FRAMEWORK-MAPPING-01` has no falsifier. Its own header declares it *"Type H (Hypothesis
mapping, no falsifier required — reference architecture)"* — the candidate asserts its own
exemption. That is recorded as a `falsifier_waiver` with the stated reason, which **warns and
renders**, rather than either blocking it or letting it pass silently. **Accepting or refusing
the waiver is Z2's act, not Z1's.** It is checklist item 3 below.

CLAUDE.md's own appended events note `Q-FRAMEWORK-MAPPING-01` as "awaiting Z2 RATIFY signature"
since 2026-09-10. Nothing had counted the days since.

---

## Falsifier

**Prediction (window: 30 days from ratification, closes 2026-10-13):**

1. `z2_ratification_gate.yml` executes ≥ 1 job on every triggering event, and its
   `conclusion` tracks the validator's exit code rather than being constant.
2. No candidate reaches `main` with a `ratified` status lacking a resolvable `z2_ruling`.
3. The coverage rule catches ≥ 1 real unindexed inbox file.

**Falsifier — any one of these refutes the change:**

- A zero-job run of `z2_ratification_gate.yml` occurs on `main` after this merges. *(The defect
  recurred, or was never the cause.)*
- The gate is disabled, its `on:` paths narrowed to exclude `z1-inbox/**`, or a `continue-on-error`
  is added to the validate step. *(The friction was rejected rather than obeyed — the 25% this
  block's probability is holding back.)*
- A candidate lands with `status: ratified` and no `z2_ruling`, by any route including a manual
  merge. *(The no-self-grant rule is bypassable.)*
- 30 days pass with zero coverage-rule firings **and** ≥ 1 file added to `z1-inbox/` outside
  `INDEX.yaml`. *(The rule is inert.)*

**Prediction that the falsifier does NOT fire: 0.75.**

---

## Registrable items surfaced (routed, not self-registered)

1. **`z2_ratification_gate.yml` was invalid YAML from its first commit; 122 runs, 0 jobs.**
   The single CI gate CLAUDE.md names as the enforcement point for the entire Z1→Z2→Z3 model
   never executed a step. **IC candidate.** Same class as IC-031 (a claim exceeding what the tree
   supports), but the overstated claim is in the authority map rather than a receipt.

2. **Four further workflows are in the same zero-job state**, `drift-monitor.yml` for 462 runs.
   **IC candidate** — and an open question about how many other CI assurances in CLAUDE.md are
   unwired. Repairs deliberately **not** made here.

3. **A dead workflow is indistinguishable from a failing one in the Actions UI.** Zero-job
   `failure` runs read as a gate that ran. This is the detection gap that let #1 and #2 persist
   for 584 combined runs. Mitigated here by `workflow-lint.yml` (advisory). **F candidate.**

4. **`.z1-control/` is not in `.tool-control/scan.py`'s `SCAN_ROOTS`** (`tools`, `scripts`,
   `bin`), so its two scripts are unregistered tools. PR #307 adds `.tool-control` and
   `.doc-control` to `SCAN_ROOTS` but not `.z1-control`. **Flagged as a follow-up, not fixed
   here**, to avoid a conflict in a generated manifest three open PRs are already touching.

---

## Honest limits

- **The repaired gate is verified locally, not in CI.** The workflow now parses under a
  duplicate-key-strict loader and each step's logic was run by hand against this tree, but the
  claim "it executes jobs" cannot be confirmed until it runs on GitHub. That is precisely the
  claim the falsifier's first clause tests, and it is the reason this block does not assert the
  gate works.
- **Candidate/record classification is Z1 judgment.** Each of the 24 files was opened and
  classified on what it does, not its filename — the error #306 called out against itself. Two
  are arguable: `IC-030-REPIN-01.md` reads as a Z1 work order with a separate RESULT file and is
  filed as a record though it carries a `Q-` id; `CYCLE_3_FALSIFICATION_REPORT.md` is filed as a
  candidate because Z2 Ruling 1 explicitly decided on it, though it was written as a report.
- **The three `ratified` statuses are transcribed, not granted.** They come from
  `Z2_RULINGS_2026-09-08.md`, which carries Night's hashes. If that transcription is wrong, it is
  wrong in a file Z2 can correct — and the validator forced each one to cite its ruling.
- **q_ids were assigned by Z1 for four blocks that carried none.** `Q-JESTER-CHECK-01`,
  `Q-WITCH-CASCADE-01`, `Q-ACAT-BENCHMARK-01`, `Q-DOC-LIFECYCLE-01`. Renaming them is a Z2 edit.
- **Coverage is enforced; correctness is not.** Nothing checks that a candidate's falsifier is a
  *good* falsifier, only that one is present — the same limit Q-TOOLCONTROL-02 named for
  categories assigned from docstrings.
- **CI cannot authenticate Z2, and this validator does not pretend to.** A review round put the
  point sharply: a resolvable `z2_ruling` is evidence, not authorization, because Z1 could add a
  ruling file and cite it in the same PR. The checks added since raise the cost — the ruling must
  be an indexed record and must literally contain the `z2_hash` claimed for it — but a determined
  proposer with write access can still manufacture all three. **The real control is CODEOWNERS
  plus branch protection on `z1-inbox/` and `.z1-control/`, not this file.** Item 3 of
  Q-TOOLCONTROL-01 found that the root `CODEOWNERS` doc-control rules have never been in force
  because `.github/CODEOWNERS` shadows them — so that control's current state is itself an open
  question, and this one inherits it. **Checklist item 7.**

---

## Files

| file | change |
|---|---|
| `.github/workflows/z2_ratification_gate.yml` | duplicate `name:` removed; fetch-depth; falsifier scoped |
| `.github/workflows/workflow-lint.yml` | new, advisory |
| `z1-inbox/INDEX.yaml` | new — SSOT |
| `.z1-control/validate.py` | new — the gate |
| `.z1-control/render.py` | new — the renderer |
| `Z1_INBOX_INDEX.md` | new — generated |
| `z1-inbox/2026-09-13/Q-GOVGATE-01.md` | this block |

**No file inside a dated `z1-inbox/` folder was modified.** No status was moved to `ratified`
that was not already ruled on by Night on 2026-09-08.

---

## Z2 Review Checklist

- [ ] **Item 1 (priority): the Z2 gate has never run.** 122 zero-job runs. Every "CI enforces"
      claim in CLAUDE.md that routes through this workflow has been unenforced since 2026-09-10.
      Confirm the IC and whether other CI assurances need the same audit.
- [ ] **Item 2:** four further dead workflows, repairs not attempted here — direct Z3, or accept
      as a separate work item.
- [ ] **Item 3:** `Q-FRAMEWORK-MAPPING-01`'s self-declared falsifier exemption — accept the
      waiver, or require a falsifier before ratification.
- [ ] **Item 4:** the **5 candidates past the 48h window** (3d, 3d, 1d, 1d, 1d). CLAUDE.md routes
      a closed window to Admiral re-read.
- [ ] **Item 5:** the four Z1-assigned `q_id`s — accept or rename.
- [ ] **Item 6:** `IC-030-REPIN-01.md` filed as a record and `CYCLE_3_FALSIFICATION_REPORT.md` as
      a candidate — confirm both readings.
- [ ] `decision_window_days: 2` matches CLAUDE.md's 48h. Note CLAUDE.md says 48h while
      `seeds/INDEX.md` line 175 says **72h** for escalation — an **AMBIGUITY** callout, unresolved
      here, and the reason the window is a declared field rather than a constant in code.
- [ ] The coverage rule is accepted as merge-blocking from day one.
- [ ] `ratifiers: [Night]` is the correct and complete list — it is now pinned in
      `KNOWN_RATIFIERS` in `.z1-control/validate.py`, so changing it is a code review.
- [ ] **Item 7:** the no-self-grant rule rests on CODEOWNERS and branch protection over
      `z1-inbox/` and `.z1-control/`, which Q-TOOLCONTROL-01 item 3 suggests may not be in force.
      Confirm, or the validator's authorization checks are advisory in practice.

---

## Summary

The gate that enforces the Z1→Z2→Z3 model has never executed a step. It was invalid YAML from its
first commit, and 122 consecutive runs completed in zero seconds with zero jobs while reading, in
the Actions list, exactly like a gate that ran and failed. Four other workflows are in the same
state; one has been dead for 462 runs.

The duplicate key is removed, the checks inside it are repaired, and the falsifier rule it meant
to enforce now applies to candidate blocks rather than to receipts and handoffs — scoped that way
because the rule as written would have failed on 11 of the 24 files already present.

z1-inbox now has the same SSOT → validate → render → CI shape as the other two control surfaces.
Eight candidates are awaiting Z2; five are past the 48h window; one asserts its own falsifier
exemption. None of that was visible before, and none of it is Z1's to settle.

**Ratification requested.**
