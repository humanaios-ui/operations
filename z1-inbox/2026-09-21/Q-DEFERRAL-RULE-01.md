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

The unavailability is useful. This repository already solved the same problem for
molt closure — **resolve by pinned observation set, not by elapsed window** — and
that form applies directly:

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

## What Z2 is asked to decide

1. **Three legs, or none.** Z1 recommends against splitting the question.
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

FALSE if artifact-resident deferrals **do not** accumulate unretired in a corpus
that *requires* a written justification. Findings 2 and 3 of the research study
corpora where justification was mostly optional. If a corpus enforcing
`require-explanation` shows a materially lower dead-suppression rate, leg 2 alone
suffices and leg 3 is over-engineering. Mechanically checkable against Go projects
setting `nolintlint: require-explanation: true`, by measuring what fraction of
their `//nolint` directives suppress a diagnostic the current analyzer would still
emit.

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
