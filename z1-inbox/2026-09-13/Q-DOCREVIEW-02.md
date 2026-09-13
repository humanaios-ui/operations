# Candidate Block: Q-DOCREVIEW-02 — Findings from the first real document review pass

**Z1 Proposer:** Claude (AI agent)
**Date Submitted:** 2026-09-13
**Branch:** `claude/tool-manifest-doc-registry-344ako`
**Phase:** 1 (control infrastructure)
**Status:** AWAITING Z2 RATIFICATION
**Occasioned by:** Z2 instruction, 2026-09-13 — "39 overdue document reviews - go."
**Executes:** Q-DOCREVIEW-01, which built the lifecycle and deliberately moved no date

---

## Q-DOCREVIEW-01's prediction, resolved

That block staked **70%** that "at least one review is recorded via `--record` within 30 days of
ratification," held low because "the mechanism removes every obstacle except the one that actually
matters, which is that somebody has to read 39 documents."

**Resolved: 11 recorded, same day.** The prediction was correct in direction and badly calibrated in
magnitude — but the reason is worth recording rather than claiming a win. The obstacle it named was
real; it was cleared by Z2 instructing the work and by the reviewer being an agent that can read 11
documents in one session. It was *not* cleared for the other 28, and for exactly the reason the
block anticipated: somebody has to be able to read them.

---

## What was asked and what was done

Z2 cleared the overdue review backlog for action. The backlog was 39 of 46 documents: 35 sharing
`review_due: 2026-08-01` and 4 sharing `2026-08-15`, because one seeding pass on 2026-07-02 stamped
the corpus with a single date.

**11 were reviewed and recorded. 28 could not be, and the reason is structural, not effort:**

| Canonical repo | Overdue | Reviewable from this session |
|:---|---:|:---|
| `operations` | 11 | yes — reviewed |
| `humanaios-internal` | 10 | **no** — outside this session's repository scope |
| `lasting-light-ai` | 18 | **no** — outside this session's repository scope |

A document that cannot be opened cannot be reviewed. Recording a review for those 28 would be a
false claim of exactly the kind `--record` was built to prevent, so they remain overdue and
visible. **Z2 decision needed on routing them** — either grant this session access to those two
repositories, or assign them to those repos' Z3 executors per `ZONE_REGISTRY.md`.

Reviews are recorded as `reviewed_by: Claude (Z1)`. That is who read them. Z1 review is not owner
approval; every one of these remains at its existing `status`, and `approved` is still the owner's
separate act.

---

## §A Position · Destination · Probability

**Position:** the review lifecycle existed but had never run. No document carried `last_reviewed`,
so no next date could be derived and the whole corpus tipped overdue together.

**Destination:** a corpus where reviews are recorded acts with derived next dates that do not
re-synchronise, and where what a review *finds* is routed rather than lost.

**Probability:** 85% that the 11 in-scope documents stay off the overdue list through Q4, given the
derived dates now span 2026-12-01 → 2027-03-20 rather than two days. The 28 out-of-scope documents
will remain overdue indefinitely absent a Z2 routing decision — that is not a forecast, it is the
current mechanism.

---

## F-CANDIDATE-01 — `DOCUMENT_CONTROL_PLAN.md` does not exist

**Severity: high.** The document control system's own method document is absent from the repository,
while being cited as authoritative by:

- `.doc-control/validate.py` — its module docstring says it "Enforces the mechanical
  controlled-document rules from DOCUMENT_CONTROL_PLAN.md"
- `document-registry.yaml`
- `DOCUMENT_CONTROL_ACTIVATION_BRIEF.md` (an `approved` document), as "**Method:** full design + rationale"
- `TOOLS_MANIFEST.md`
- `PRACTICES_ANNOUNCEMENT.md`
- `NOTIFICATION_empirica-foundation.md`, `NOTIFICATION_humanaios-core.md`,
  `NOTIFICATION_lasting-light-ai.md` — **communications sent to other practices**

This is the recurring defect of this repository in its purest form: a rule set asserted by many
documents, enforced by a validator that names it as its source, and not present. Four external
notifications direct other practices to read it.

**Falsifier:** find `DOCUMENT_CONTROL_PLAN.md` at any path in `humanaios-ui/operations`, or in the
history of the default branch. `git log --all --diff-filter=A -- '*DOCUMENT_CONTROL_PLAN.md'`
returning a commit falsifies this finding.

**Z2 decision needed:** write the document, or correct all seven references to name whatever
actually holds the rules. The validator citing a nonexistent source is the load-bearing instance.

---

## F-CANDIDATE-02 — a ritual instructs running a tool that is not there

`SESSION_RITUALS.md:384` locates `intent_object_population_v1_0.py` in "operations repo, `tools/`".
It is not in `tools/`, nor anywhere in the tree. `CURRENT.md:189` states it was "built and
self-tested" with a capture inserted as "pipeline proof".

The tool manifest registers 150 tools by a coverage rule that fails the build on any unregistered
tool file; this one is absent rather than unregistered.

**Falsifier:** the file exists at any path in the repository, or `git log --diff-filter=A` shows it
was added and later removed (which would make this a retirement record rather than a phantom).

---

## F-CANDIDATE-03 — `SUBSTRATE_CAPABILITY_REGISTRY.md` points at seven absent documents

`SUBSTRATE_AUTHORIZATION.md` and six per-substrate briefs — `CI_CLAUDE_V1_0.md`, `CI_GEMINI_V1_0.md`,
`CI_GROK_V1_0.md`, `CI_META_AI_V1_0.md`, `CI_PERPLEXITY_V1_0.md`, `CI_TEMPLATE_V1_0.md` — are
referenced with explicit `humanaios-ui/operations/` paths. None exists.

**Falsifier:** any one of the seven resolves in this repository.

---

## F-CANDIDATE-04 — an approved document misstates the registry it describes

`DOCUMENT_CONTROL_ACTIVATION_BRIEF.md:30` (status `approved`, `approved_by: carly`) states
"34 documents approved, 5 flagged for reconciliation, 37 excluded".

Actual registry today: **6 approved, 34 in `review`, 6 draft**, 37 excluded. The "34" is the count
of documents in `review`, labelled as approved. An approved brief tells every practice that the
corpus is approved when 74% of it is not.

**Falsifier:** `document-registry.yaml` yields 34 documents with `status: approved`.

---

## F-CANDIDATE-05 — two specs name a registry file that does not exist

`A6_DRIFT_MONITOR_SPEC.md:42` and `A4_INTAKE_PIPELINE_SPEC.md:55,81` instruct implementers to read
and write `registry.yaml`. The file is `document-registry.yaml`. Both specs are `approved`.

Low severity, high certainty; listed because both are implementation specs, where a wrong filename
is not cosmetic.

**Falsifier:** a file named exactly `registry.yaml` exists at the repository root.

---

## What was changed in code, and why it is not a date bump

`review.py` gained a deterministic per-document spread on the review interval.

Recording 11 real reviews fixes the history but not the shape: `review_policy` is keyed on
**status**, so 34 documents at `review: 90` reviewed in one batch come due again on one day, and the
herd re-forms every 90 days. The spread is a sha256 of `doc_id` mapped into ±14 days, clamped to
half the interval, so the same document gets the same offset on every run with no stored state.

**This is deliberately not the staggered schedule `pull_order` refuses to emit.** That one invented
a *deadline* per document when nothing outside the system imposed one. This moves a *staleness
threshold* — the day a document starts being reported as old — which this system already sets
arbitrarily at 90 or 180. It manufactures no obligation; it stops existing ones coinciding. Measured:
34 documents reviewed on one day now fall due across 17 distinct days instead of 1.

**A bug this introduced, and what it showed.** `--record` computed `on + days` itself while `--check`
called `next_due`. Adding the spread to `next_due` alone made every date `--record` wrote fail the
gate meant to confirm it — 10 violations on the first run. Fixed by deriving through `next_due` in
both, so there is one copy of the rule. The `--record` message also reported the policy figure
(`+90d`) beside a date 93 days out; it now reports the interval actually applied.

**Falsifier for the spread:** two documents of the same status, reviewed on the same day, receive the
same `review_due`. Or `--check` rejects a date `--record` wrote.

---

## §B Receipt

| Claim | Evidence |
|:---|:---|
| 39 overdue, 35+4 on two seeded dates | `.doc-control/review.py --queue` before the pass |
| 11 in `operations`, 28 elsewhere | `canonical_repo` grouping over the overdue set |
| 11 reviews recorded, dates 2026-12-01 → 2027-03-20 | `document-registry.yaml` diff; `--check` exit 0 |
| 28 still overdue | `.doc-control/validate.py` — 28 advisory warnings |
| 34 → 17 distinct due days | `spread()` over the 34 `review`-status doc_ids |
| Five findings above | path resolution against `git ls-files`, each verified by hand |

**Not claimed:** that the 11 documents are *correct*. A review establishes that someone read the
document and reports what they found; five findings are what this one found. Fixing them is separate
work and F-CANDIDATE-01 in particular needs Z2 to decide whether the plan is written or the
references are corrected.
