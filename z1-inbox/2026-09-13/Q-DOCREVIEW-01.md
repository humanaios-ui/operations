# Candidate Block: Q-DOCREVIEW-01 — The 39 Overdue Document Reviews

**Z1 Proposer:** Claude (AI agent)
**Date Submitted:** 2026-09-13
**Pinned SHA:** `758aef32be4d43608a903a078e1280d85a53a15b`
**Branch:** `claude/z1-inbox-z2-conversion-reviews-w54cil`
**Phase:** 0/1 (control infrastructure)
**Status:** AWAITING Z2 RATIFICATION
**Answers:** Q-TOOLCONTROL-01 Z2 checklist, item 6

---

## §A Position · Destination · Probability

**Position:** `.doc-control/validate.py` emits 39 `::warning::review overdue` lines on every run.
Q-TOOLCONTROL-01 routed them to Z2 as "set new `review_due` dates or accept the backlog."

**Destination:** neither of those two options, because both are wrong. Supply the review
lifecycle the registry never had, so that a review can be *recorded* and the next date *derived* —
then put the one genuinely owner-shaped decision to Z2 as a single act instead of 39.

**Probability:** **70%** that at least one review is recorded via `--record` within 30 days of
ratification. Held low deliberately: the mechanism removes every obstacle except the one that
actually matters, which is that somebody has to read 39 documents.

---

## The 39 are not 39 lapses

| `review_due` | documents | days late (2026-09-13) |
|---|---|---|
| **2026-08-01** | **35** | 43 |
| **2026-08-15** | **4** | 29 |
| 2026-10-12 | 1 | — not due |
| 2026-12-31 | 1 | — not due |
| *(none set)* | 5 | — |

Thirty-five documents share one date and four share another. That is not thirty-nine independent
review cycles that independently lapsed — it is **the 2026-07-02 seeding pass stamping the whole
corpus with a single date**, after which the entire corpus necessarily tips overdue on the same
day, every time.

Measured across all 46 registered documents:

| field | present |
|---|---|
| `owner` | **0 / 46** |
| `last_reviewed` | **0 / 46** |
| `review_interval_days` | **0 / 46** |

So nothing can record that a review happened, nothing can schedule the next one, and nobody is
assigned. **The backlog is not a lapsed process. It is the absence of one**, and `review_due` was
the only field it ever had — a date with no mechanism behind it.

This is the same class as items 1 and 2 of Q-TOOLCONTROL-01: a registry field asserting a
lifecycle nothing implements.

---

## Why "set new dates" is the wrong fix

Bumping 39 dates clears 39 warnings, resets the clock on 39 documents **nobody reviewed**, and
leaves every structural cause untouched — so the same 39 re-form on whatever new date is chosen.
It also converts a visible backlog into an invisible one, which is strictly worse than the
warnings.

`document-registry.yaml`'s own header states the governing rule: *"status stays `review` —
approval is the OWNER's human act, never automated (no self-grant)."* A review date is the same
class of act. **Z1 did not move any of the 39 dates**, and the mechanism below is built so that it
cannot: the only supported way `review_due` moves forward is a recorded review.

---

## What was built

### `.doc-control/review.py`

| command | what it does |
|---|---|
| `--record <DOC_ID> --by <owner>` | A review **happened**. Stamps `last_reviewed` + `reviewed_by`, derives the next `review_due` from the interval. The only supported way a date moves forward. |
| `--queue` | What is due, how late, under whose name, grouped by the date they were stamped with. |
| `--propose --start --per-week` | A staggered schedule for the backlog, printed for Z2. **Writes nothing.** |
| `--check` | CI: a `review_due` that contradicts its own `last_reviewed + interval` is a merge error. |

### Schema: `review_due` becomes DERIVED

`review_policy: {draft: 30, review: 90, approved: 180}` in the registry, overridable per document
with `review_interval_days`. `superseded` and `retired` are off the cadence entirely.

Once a document carries `last_reviewed` + `reviewed_by`, its `review_due` **is** `last_reviewed +
interval`, and `--check` fails the merge if the registry says otherwise. This is the same
DERIVED/CURATED split `.tool-control/` already established, applied to the one field that had
drifted furthest from anything that could verify it.

**This moves no date today.** No document carries `last_reviewed`, so the policy has nothing to
derive from and the 39 stay visibly overdue until somebody records an actual review.

### Wired into CI

`document-control.yml` gains the review self-test and `review.py --check` as a **blocking** step.
Note what is and is not blocking:

- **Blocking:** a `review_due` that contradicts its own recorded history. That means somebody
  moved a date without a review happening.
- **Advisory (unchanged):** being overdue. Lateness is a fact about the world, not a defect in
  whatever PR happens to be open. Making it blocking would turn every contributor into a hostage
  of the backlog — the fastest route to the rule being disabled.

### `governance-triage.yml` — the automation

The 39 were only ever visible as `::warning::` lines inside a CI log nobody opens unless a PR is
already red. This runs **Mondays at 07:00 UTC** and keeps one GitHub issue per queue up to date
(the shape `priority-queue-triage.yml` already uses): the document review backlog grouped by
stamped date, and the Z2 decision queue from Q-GOVGATE-01. It closes the issue when a queue
clears, opens nothing when there is nothing to say, and **decides nothing**.

---

## Gates verified to actually fail

`review.py --smoke-test` drives each rule red:

| test | result |
|---|---|
| `review_due` hand-edited to contradict `last_reviewed + interval` | `::error::review_due is derived … Run --record rather than editing the date` |
| `last_reviewed` with no `reviewed_by` | `::error::a review is somebody's act` |
| `review_interval_days: "ninety"` | `::error::must be a positive integer` |
| A document with no history | yields **no** derived date — it cannot be invented |
| `retired` document | excluded from the cadence, not reported overdue |
| `--propose` | staggers, and writes nothing |

End-to-end, against the real registry (then reverted — the review did not happen):

```
$ python3 .doc-control/review.py --record HAIOS-GOV-001 --by Night --on 2026-09-13
HAIOS-GOV-001: reviewed 2026-09-13 by Night; next review_due 2026-12-12 (+90d).
```

Overdue fell 39 → 38; `--check` passed; `render.py --check` **failed** until
`CONTROLLED_DOCUMENTS.md` was re-rendered, which is the existing sync gate correctly noticing a
review date moved. Comments and inline `drift: {…}` flow blocks survived the edit — the write is
a targeted text edit, not a `yaml.dump` round-trip that would reformat the file.

---

## The decision Z2 actually has to make

Two things here are the owner's, and only two:

### Decision A — the backlog

| option | effect |
|---|---|
| **A1. Accept the staggered schedule below** | 39 documents get distinct dates across 7 weeks; each then moves onto its status interval. The herd does not re-form. |
| **A2. Review-then-record, no re-dating** | The 39 stay overdue and visible; each clears only when `--record` runs. Most honest, slowest to green. |
| **A3. Retire or supersede some** | Several of the 35 are dated collaborator HTML reports from March–May 2026. If they are historical records rather than live documents, `retired` takes them off the cadence truthfully. |

**Z1's reading:** A3 first, then A1 for what remains. Nine `HAIOS-COLLAB-*` entries are
point-in-time reports (`..._S-051426-02.html`); re-dating a frozen record for review is ceremony.
But which of them are live is not Z1's call.

Proposed schedule under A1 (`--propose --start 2026-09-22 --per-week 6`, 6/week):

| | |
|---|---|
| First slot | 2026-09-22 (`HAIOS-COLLAB-001`) |
| Last slot | **2026-11-05** (`HAIOS-PROC-005`) |
| Span | 7 weeks, no two documents sharing a date |

Full table: `python3 .doc-control/review.py --propose --start 2026-09-22 --per-week 6`.

### Decision B — owners

**0 of 46 documents have an owner.** A review cadence with no assignee produces a queue nobody is
late on. The intervals are also proposals: `{draft: 30, review: 90, approved: 180}` is Z1's
default, chosen so a `draft` cannot sit indefinitely, and is a one-line edit.

---

## Falsifier

**Prediction (window: 30 days from ratification, closes 2026-10-13):**

1. ≥ 1 review is recorded via `--record`, and its next `review_due` is derived, not typed.
2. No `review_due` in the registry contradicts its own `last_reviewed + interval`.
3. The overdue count moves **only** through `--record`, `retired`/`superseded`, or an explicit
   Z2-ratified re-dating — never through an unexplained edit.

**Falsifier — any one of these refutes the change:**

- 30 days pass with **zero** uses of `--record` and the overdue count still ≥ 39. *(The mechanism
  removed an obstacle that was not the obstacle; the binding constraint is reviewer time, and this
  is ceremony.)*
- Any `review_due` is edited directly in a merged PR without a corresponding `last_reviewed`.
  *(The derivation is bypassable and `--check` does not bind.)*
- `review.py --check` is removed from `document-control.yml`, or made `continue-on-error`.
  *(The friction was rejected.)*
- The overdue count reaches 0 without 39 recorded reviews, retirements, or a ratified re-dating.
  *(The backlog was cleared by re-dating, which is the failure this block exists to prevent.)*

**Prediction that the falsifier does NOT fire: 0.70.** The first clause is the live risk: nothing
here makes reading 39 documents faster.

---

## Registrable items surfaced (routed, not self-registered)

1. **`review_due` was a field with no lifecycle behind it.** 46 documents carry a review date;
   0 carry a reviewer, a review record, or an interval. The field could only ever be set by hand
   and could never be satisfied. **IC candidate** — same class as Q-TOOLCONTROL-01 items 1 and 2
   (a registry asserting a mechanism that does not exist), on the field rather than the index.

2. **A single-date bulk seed guarantees a synchronised backlog.** Any registry seeded with one
   `review_due` produces N simultaneous overdue warnings, which read as N process failures and
   are one. Generalises beyond documents to any dated bulk import. **F candidate.**

3. **39 advisory warnings is the same as none.** They have been emitted on every
   `document-control` run since 2026-08-01 without being acted on. A warning channel with no
   escalation path is write-only. Mitigated here by `governance-triage.yml`. **F candidate**, and
   the reason that workflow exists rather than a louder `::warning::`.

---

## Honest limits

- **Nothing here reviews a document.** The mechanism makes recording and scheduling reliable; the
  reading is unchanged and unassisted. If the real constraint is reviewer hours, this changes
  nothing about the backlog, which is exactly what the first falsifier clause tests.
- **The intervals are invented.** `{30, 90, 180}` are plausible, not derived from anything. No
  evidence in this repo says an approved document goes stale in 180 days. They are defaults to be
  argued with, not measurements.
- **`--record` asserts a review happened; it cannot verify one.** It is a receipt, and carries the
  same overstatement risk as IC-031. What it does add is a name and a date, where previously
  there was nothing to overstate against.
- **`--record` edits by targeted regex, not a YAML round-trip.** That preserves comments and
  inline flow blocks, but a future hand-edit that reformats an entry's indentation would defeat
  the block match. It fails loudly (`could not locate its block`) rather than writing wrongly.
- **The 5 documents with no `review_due` at all are not addressed.** They are not overdue because
  they have no date, which is a third state this block does not resolve.
- **Not applied:** no date was changed, no owner assigned, no document retired.

---

## Files

| file | change |
|---|---|
| `.doc-control/review.py` | new — the scheduler |
| `document-registry.yaml` | `review_policy:` block added (16 lines). **No document entry changed.** |
| `.github/workflows/document-control.yml` | review self-test + `--check` added as blocking steps |
| `.github/workflows/governance-triage.yml` | new — weekly triage for both queues |
| `z1-inbox/2026-09-13/Q-DOCREVIEW-01.md` | this block |

`validate.py` still reports **39** overdue, unchanged and on purpose.

---

## Z2 Review Checklist

- [ ] **Decision A — the backlog.** A1 staggered schedule / A2 review-then-record / A3 retire
      first. Z1 recommends **A3 then A1**.
- [ ] **Decision A3 specifically:** are the nine `HAIOS-COLLAB-*` point-in-time reports live
      documents or historical records? If records, `retired` is the truthful disposition.
- [ ] **Decision B — owners.** 0 of 46 assigned. A cadence with no assignee produces a queue
      nobody is late on.
- [ ] `review_policy: {draft: 30, review: 90, approved: 180}` — accept or set real intervals.
- [ ] Overdue stays **advisory** while derivation-mismatch becomes **blocking** — confirm that
      split is the intended one.
- [ ] `governance-triage.yml` cadence (Mondays 07:00 UTC) and the issue-per-queue shape.
- [ ] The 5 documents with **no** `review_due` — give them one, or declare them off-cadence.

---

## Summary

Thirty-five of the 39 share a single `review_due`, and four share another, because a seeding pass
stamped the corpus with one date. No document has an owner, a recorded review, or an interval —
so nothing could record that a review happened or schedule the next one. The backlog is not a
lapsed process; it is the absence of one.

Re-dating the 39 would clear the warnings, reset the clock on documents nobody read, and rebuild
the same synchronised backlog on a later date. So Z1 built the lifecycle instead and moved no
dates: a review is recorded, the next date is derived, a contradiction between them fails the
merge, and a weekly job puts both queues where someone will see them.

What is left is the part that was always the owner's: whether to stagger the backlog, retire the
records among it, and who owns what.

**Ratification requested.**
