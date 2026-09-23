# Q-DEFERRAL-RULE-01 — a deferral needs an ending condition, not just a better home

**Type:** H (hypothesis) + proposed rule · **Author:** Z1 (Claude) · **Status:** awaiting_z2
**Requested:** Night, 2026-09-21 — *"a deferral must be defensible in the artifact,
not only in a PR reply — can we do more research first before deciding?"*
**Research:** `audits/DEFERRAL_RULE_RESEARCH_S-092126.md` (tier CLAIM+LINK)
**Origin of the proposal:** `Q-AGENT-CHECKIN-CALIBRATION-01` line 106

---

## What the research changed

Night asked for research before a decision. The research supports the rule's
**direction** and says its **form is insufficient in a specific, documented way.**

Supporting the direction: the modern-code-review literature reports that change
rationale is fragmented across commits, issues and PRs with no single artifact
capturing it, and that review is asynchronous communication in which context is
lost. A PR reply is a message in a channel; the artifact is the only thing that
travels with the code.

Against the form, and this is the load-bearing finding: an FSE 2025 study of
suppressed static-analysis warnings — 7,357 suppressions across 46 Python
projects — reports that **50.8% of all suppressions do not affect any warning**,
that their number continuously increases over time, and that some unintentionally
hide future warnings. A suppression comment *is* the artifact-resident deferral
this rule proposes: written at the site, versioned with the code, visible to every
later reader. Half of them refer to nothing.

> Writing a deferral into the artifact makes it **durable**. Durable is not
> **defensible**. Durability without re-checking is how a tree fills with
> justifications for findings that no longer exist.

A second study (1,425 Java projects, FindBugs/SpotBugs) adds that false positives
are a *minor* share of suppressions — so the intuitive model, "the tool was wrong
and I recorded why", is not the common case. The common case is a debt record, and
a debt record with no closing condition is the failure above.

ADR practice reports the same decay at document scale, with the conclusion that an
outdated decision record is worse than none because it is actively misleading.
Three literatures, one conclusion: the write is cheap, the retirement never happens.

## The constraint that shapes the answer

The literature's standard remedy is **periodic review** — audit your suppressions
every N months. `Q-TEMPORAL-DISSOLUTION-01` forbids it: an internal cadence is an
`INVALID_INTERNAL_DEADLINE`.

The unavailability is useful. This repository has **proposed** a solution to the
same problem for molt closure — **resolve by pinned observation set, not by
elapsed window** — and that form applies directly:

> *Corrected on review (Copilot, PR #447), and the correction changes what Z2 is
> being asked to ratify.* An earlier version said the repository "already solved"
> this. It has not. `MOLT_STATE.md` line 125 reads **"Status: PROPOSED —
> Q-MOLT-TEMPORAL-PURITY-01. Not in force until a Z2 hash"**, and the index has
> that candidate at `awaiting_z2` with no hash. Leg 3 borrows a **specified but
> unratified** pattern. Z1 has spent this session reminding Z2 that those
> ratifications are outstanding and then wrote that one of them was done — the
> same defect class this session has been cataloguing, committed while
> cataloguing it.

> A deferral names the **observation whose arrival ends it**, not a date by which
> someone will look again. A check reports a deferral whose observation has
> arrived, and a deferral whose referent has disappeared.

The second clause answers the 50.8% directly: a dead suppression is one whose
finding no longer exists, and that is mechanically checkable with no clock.
`MEASUREMENT_STARVED` is the same shape — a state predicate over a census.

## Proposed rule

A deferral is admissible when all three hold:

| Leg | Requirement | Enforced by |
|---|---|---|
| 1 | Lives **in the artifact**, not only in a PR reply | present in the diff |
| 2 | Names **what it defers and why** — the specific finding, not a category | a lint over deferral markers |
| 3 | Names the **observation that ends it**; a check reports arrival, and reports a deferral whose referent is gone | a scan, no clock |

Leg 2 is not novel and not an honour system: `nolintlint`, shipped in
`golangci-lint`, already refuses a suppression directive that names no linter
(`require-specific`) or carries no explanation (`require-explanation`). That
removes the usual objection to making this a gate rather than a convention.

## Tested against its author first

On PR #442 Z1 deferred one review finding — extending `.tool-control/validate.py`
to assert the documented `--help`/`--input` contract rather than fixing the one
tool. The reasoning went into a review reply and the PR description.

**Under this rule that deferral fails, on two of three legs:**

1. ✗ It lives in a review reply and a PR description. Both are channel messages.
   Nothing under `tools/` or `.tool-control/` records that the contract is held by
   hand.
2. ✓ It names the specific finding.
3. ✗ It names no ending observation. Nothing will report that 171 registered tools
   are unchecked against a documented contract, and nothing will notice when the
   172nd arrives without `--input`.

A live instance of the failure, produced by the rule's author, in the session that
proposed the rule. It is the most defensible argument available and it is why this
candidate exists as an artifact rather than as a reply.

## Recommendation, stated as a single question

**Adopt three legs or none.** Leg 1 alone is the documented failure mode, not a
safe first step: it would move deferrals from a place where they are lost to a
place where they are permanent and unretired, with the rule nominally in force and
nobody able to say it had failed.

Z1 recommends the tool for legs 2 and 3 be built **before** the rule binds, and
recommends against a staged adoption beginning with leg 1.

**This recommendation is conditional on `Q-MOLT-TEMPORAL-PURITY-01`.** Leg 3's
form is specified in `MOLT_STATE.md` and explicitly not in force there. Ratifying
a deferral rule whose third leg borrows an unratified closure pattern would create
the dependency without the dependency — the `G-Z2-RATIFY` mistake in a new place,
where a node claimed a gate that the workflow did not actually enforce. If Z2
declines the molt candidate, this one should be re-read rather than applied.

## What Z2 is asked to decide

1. **Three legs, or none.** Z1 recommends against splitting the question.
   Ordering note: this depends on `Q-MOLT-TEMPORAL-PURITY-01`, which is
   `awaiting_z2` with no hash, so that one is decided first or this one is
   decided knowing leg 3 rests on a proposal.
2. **Scope.** Which deferrals bind? Three legs for a one-line nit is
   disproportionate, and disproportionate rules get routed around. Z1 has no basis
   to draw the line and does not recommend guessing — candidate boundaries include
   any deferred review finding, any finding a review bot marked non-optional, or
   any deferral whose subject is a gate.
3. **Who writes leg 3's check**, and whether it gates a merge or reports
   advisorily. Note that making it gate is Tier 2.
4. **Whether the #442 deferral above is retro-fitted** as the first instance, or
   left as the worked example of the failure.

## What Z1 is not doing

Not applying the rule, not building the check, not retro-fitting the #442
deferral, and not writing deferral markers into any artifact. Night asked for
research before a decision; this is the research and a recommendation.

## Falsifier

*Rewritten on review (Copilot, PR #447).* The first version measured Go `//nolint`
directives and treated the result as deciding whether leg 3 is over-engineering
**here**. That does not follow — those are analyzer suppressions in Go source,
this rule governs review-finding deferrals in a governance repository, and no
population, baseline or materiality threshold was stated. It falsifies the
analogy, not the rule. Both are now stated, separately, with thresholds.

**F1 — falsifies the analogy.** FALSE if artifact-resident suppressions do not
accumulate unretired where justification is *required*.
Population: Go repositories whose `.golangci.yml` sets `nolintlint:
require-explanation: true` **and** `require-specific: true`.
Measure: the fraction of `//nolint` directives suppressing no diagnostic the
configured analyzers would emit.
Baseline: 50.8%, as reported for mostly-unjustified corpora.
Materiality: **below 25%** means enforcing a justification does most of the work
and the evidence motivating leg 3 does not transfer.

**F2 — falsifies the rule here.** FALSE if deferrals recorded under legs 1 and 2
alone do not go dead in this repository.
Population: deferrals recorded in this tree's artifacts under legs 1 and 2,
counted from the first one.
Measure: the fraction whose named finding no longer exists in the tree and which
were never retired.
Threshold: **below 10% at a census of 20 deferrals** — a count predicate, not a
window, carrying no scheduling authority.
Note: running F2 requires adopting legs 1–2 without leg 3, which the
recommendation above argues against. Z2 may reasonably prefer the recommendation
to the experiment; if so this is a falsifier the repository has declined to run,
and that should be recorded rather than left implicit.

Also FALSE if the 50.8% figure is materially wrong when the primary text is read.
**The evidence tier is CLAIM+LINK: every PDF host returned `EGRESS_BLOCKED` from
this session, so the figures are as reported in search summaries, not as read.**
The direction survives a smaller figure; the urgency does not.

Also FALSE if this repository already carries a deferral practice Z1 failed to
find. Z1 searched `defer`/`deferral`/`deferred` across `.md`, `.py` and `.yaml`
and found only the proposal itself.

## Evidence

- `audits/DEFERRAL_RULE_RESEARCH_S-092126.md` — the full research, sources, and
  the declared evidence-tier limits
- `z1-inbox/2026-09-21/Q-AGENT-CHECKIN-CALIBRATION-01.md` line 106 — the proposal
- `TEMPORAL_DISSOLUTION_POLICY.md` — why periodic review is unavailable
- `MOLT_STATE.md` — closure by pinned observation set, the form leg 3 borrows
- PR #442, the `--input` thread — the worked failure

```yaml
z2_decision: {status: awaiting_ratification, ratified_at: null, ratification_hash: null, z2_notes: ""}
```
