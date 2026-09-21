# DEFERRAL_RULE_RESEARCH_S-092126 — is a deferral defensible in the artifact enough?

**Session:** S-092126 · **Author:** Z1 (Claude) · **Status:** research, not a ruling
**Requested:** Night, 2026-09-21 — *"The mitigation I'm proposing for that direction
is a rule, not a mechanism: a deferral must be defensible in the artifact, not only
in a PR reply — can we do more research first before deciding?"*
**Origin of the proposal:** `z1-inbox/2026-09-21/Q-AGENT-CHECKIN-CALIBRATION-01.md`
line 106.

**Temporal position (Q-TEMPORAL-DISSOLUTION-01):** nothing here carries a cadence
or a review interval. That constraint turns out to be load-bearing rather than
incidental — see §5, where the literature's standard remedy is a clock and this
repository cannot use it.

---

## 1. Evidence tier, declared first

Following the discipline set by `z1-inbox/2026-09-07/JESTER_EXTERNAL_CHECK_BLOCK.md`
(*"Titles verified by search; primary wording not read by Z1"*):

**Tier: CLAIM+LINK.** Paper titles, venues, authors and headline findings were
obtained through web search and are recorded below with URLs. **No primary text
was read.** Every PDF host attempted returned `EGRESS_BLOCKED` through this
session's proxy:

| Attempted | Result |
|---|---|
| `software-lab.org` (FSE 2025 PDF) | EGRESS_BLOCKED |
| `people.ece.ubc.ca` (same paper, mirror) | EGRESS_BLOCKED |
| `arxiv.org` (Quieting the Static) | EGRESS_BLOCKED |

So the numbers in §2 are **as reported in search summaries of those papers**, not
as read in the papers. They are strong enough to shape a proposal and not strong
enough to close it. A Z2 ruling that depends on an exact figure should have the
figure re-checked from an environment with egress; the direction of the finding
does not depend on the exact figure, and the argument in §4 survives if the
percentages are materially different.

## 2. What the evidence says

### Finding 1 — rationale that lives only in review threads is not recoverable

The modern-code-review literature reports that **code change rationale is
fragmented across commits, issues and pull requests, and no single artifact
captures all of it.** Related work reports that ~24% of review comments cause
author confusion, most commonly from unclear or missing rationale, and that
review is asynchronous communication in which context is lost.

**This supports the proposal's direction.** A PR reply is a message in a channel.
The artifact is the only thing that travels with the code.

### Finding 2 — but writing it into the artifact produces dead justifications

The strongest result found, and it cuts against the proposal as stated.

An FSE 2025 empirical study of suppressed static-analysis warnings
(7,357 suppressions across 46 Python projects, plus other languages and four
analyzers) reports:

- **50.8% of all suppressions do not affect any warning** — they are practically
  useless.
- The number of suppressions in a project **tends to continuously increase over
  time.** They accumulate; they are not removed.
- Some suppressions **unintentionally hide future warnings.**

A suppression comment is exactly the artifact-resident deferral this rule
proposes. It is written at the site, versioned with the code, visible to every
later reader — and half of them refer to nothing at all.

**Writing a deferral into the artifact makes it durable. Durable is not the same
as defensible, and durability without re-checking is how you get a tree full of
justifications for findings that no longer exist.**

### Finding 3 — suppression is mostly not false-positive management

A second study (Liargkovas et al., 2023, 1,425 Java projects using
FindBugs/SpotBugs) reports that, contrary to expectation, **false positives
account for a minor proportion of suppressions**, and that a significant number
of suppressions introduce technical debt.

This matters for how a deferral rule should be written. The intuitive model —
"the tool was wrong, I recorded why" — is not the common case. The common case is
closer to "this is real and I am not doing it now", which is a debt record, and a
debt record with no closing condition is the Finding 2 failure.

### Finding 4 — the mechanism already exists and is enforceable

`nolintlint`, shipped in `golangci-lint`, lints the suppression directives
themselves. With `require-specific: true` it refuses a directive that does not
name which linter it suppresses; with `require-explanation: true` it refuses one
with no explanation text.

So "a deferral must name what it defers and why" is **not a novel proposal and not
an honour system.** It is a shipped, mechanically enforced pattern in a
mainstream toolchain. That removes the main objection to making it a gate rather
than a convention.

### Finding 5 — the same decay is documented for decision records

ADR practice reports the identical failure at document scale: stale records
persist because *"the people who encounter them cannot confidently update them,
and the people who could update them never see them"*, and the widely repeated
conclusion is that **an outdated decision record is worse than none, because it
is actively misleading.**

Two independent literatures, one at comment scale and one at document scale,
reporting the same thing: the write is cheap, the retirement never happens.

## 3. Note on whether these sources corroborate each other

`tools/graph_convergence_v1_0.py` grades agreement by source disjointness, and the
same question applies here. Findings 2 and 3 are separate studies, separate author
groups, separate languages (Python vs Java) and separate analyzers — so their
agreement that suppressions accumulate as debt is closer to genuine corroboration
than anything this repository has measured internally. Finding 5 is a different
literature entirely reaching the same conclusion about a different artifact type.

That is the shape of evidence `Q-EXTERNAL-JESTER-01` argues we cannot generate
from inside the vault, and it is worth noticing that it was available here simply
by reading outside.

## 4. What this does to the proposed rule

> *A deferral must be defensible in the artifact, not only in a PR reply.*

**Direction: supported.** Finding 1 says the PR reply is the wrong home.
Finding 4 says the artifact home is enforceable.

**Form: insufficient, and predictably so.** The rule as stated moves a deferral
from a place where it is lost to a place where it is permanent, and stops. Finding
2 says that is how you arrive at 50.8% dead. The rule would succeed at its stated
goal and fail at its actual purpose.

The missing piece is not "write it down better". It is that **a deferral needs a
condition that ends it**, and something that checks whether the condition still
holds.

## 5. Where this repository has an advantage, and a constraint

The literature's standard remedy for Finding 2 is **periodic review** — audit your
suppressions every N months. `Q-TEMPORAL-DISSOLUTION-01` forbids exactly that: an
internal cadence is an `INVALID_INTERNAL_DEADLINE`, and this repository already
carries an open contradiction where a validator computes deadlines from
`decision_window_days: 2`.

So the obvious fix is unavailable, and the unavailability is useful. The
alternative this repository has **proposed** for molt closure — **resolve by
pinned observation set rather than by elapsed window** — is the right form here
too:

> *Corrected on review (Copilot, PR #447).* An earlier version of this sentence
> said the repository "already built" that alternative. It has not.
> `MOLT_STATE.md` line 125 states **"Status: PROPOSED — Q-MOLT-TEMPORAL-PURITY-01.
> Not in force until a Z2 hash"**, and the index records that candidate as
> `awaiting_z2` with no hash. Leg 3 below borrows a **specified but unratified**
> pattern, not an operational mechanism, and §9 is conditional accordingly. The
> miss is worth recording: Z1 has spent this entire session telling Z2 that those
> ratifications are outstanding, and then wrote that one of them was done.

> A deferral names the **observation whose arrival ends it**, not a date by which
> it will be revisited. A mechanical check reports a deferral whose observation
> has arrived, and a deferral whose referent has disappeared.

That second clause is the direct answer to the 50.8%: a dead suppression is one
whose finding no longer exists, and *that is mechanically checkable* without any
clock. `MEASUREMENT_STARVED` is the same shape — a state predicate over a census,
not a timer.

## 6. Proposed rule, in three legs

A deferral is admissible when all three hold:

| Leg | Requirement | Enforced by | Evidence |
|---|---|---|---|
| 1 | It lives **in the artifact**, not only in a PR reply | the artifact is in the diff | Finding 1 |
| 2 | It **names what it defers and why** — the specific finding, not a category | a lint over deferral markers, `nolintlint`-shaped | Findings 3, 4 |
| 3 | It names the **observation that ends it**, and a check reports when that observation has arrived or when the referent is gone | a scan, no clock | Findings 2, 5 |

Leg 3 is the one the original proposal lacked and the one the evidence says
decides whether the rule works.

## 7. A worked example, against this session

The rule should be tested on its author first.

On PR #442 Z1 deferred one review finding: extending `.tool-control/validate.py`
to assert the documented `--help`/`--input` tool contract, rather than fixing the
one tool. The reasoning was recorded in a review reply **and** in the PR
description.

Under the proposed rule **that deferral is non-compliant, failing two of its three
legs**:

1. **Leg 1 — fails.** It lives in a PR reply and a PR description. Both are
   channel messages. Nothing in `tools/` or `.tool-control/` records that the
   contract is enforced by hand.
2. **Leg 2 — passes.** It names the specific finding, not a category. The one leg
   it clears.
3. **Leg 3 — fails.** It names no ending observation. Nothing anywhere will report
   that 171 registered tools are still unchecked against a documented contract,
   and nothing will notice when the 172nd is added without `--input`.

That is a live instance of Finding 1 produced by the author of the rule, in the
same session, which is the most defensible reason to adopt it and the reason this
document exists rather than a PR reply.

## 8. Costs, stated rather than omitted

- **Deferral markers become a surface to game.** A leg-2 explanation can be
  written to satisfy a lint without being true. Finding 4's `require-explanation`
  checks nonzero length, not honesty. Leg 3 is the partial answer — a false
  ending condition is falsifiable in a way that false prose is not — and it is
  partial, not complete.
- **A scan for "the referent is gone" can be wrong in both directions.** It may
  report a live deferral as dead when a finding is restated, and miss a dead one
  whose text is unchanged.
- **Friction on small deferrals.** Three legs for a one-line nit is
  disproportionate, and disproportionate rules get routed around. Scoping which
  deferrals the rule binds is a real design question and is not answered here.
- **This adds an artifact class before anything enforces it.** Legs 2 and 3 are
  a tool that does not exist. Adopting leg 1 alone is exactly the half-measure
  Finding 2 warns about.

## 9. Recommendation

Adopt the three-leg form or none of it. **Leg 1 alone is the documented failure
mode**, not a safe first step, and adopting it alone would reproduce the 50.8%
result inside this repository with the rule in place and nobody able to say it had
failed.

Z1 recommends Z2 rule on the three-leg form as a single question, with the tool
for legs 2 and 3 built before the rule binds, and does not recommend a staged
adoption that starts with leg 1.

**Conditional on `Q-MOLT-TEMPORAL-PURITY-01`.** Leg 3's form — closure by pinned
observation set — is specified in `MOLT_STATE.md` and explicitly not in force
there. If Z2 declines that candidate, leg 3 has no ratified pattern to borrow and
this recommendation should be re-read rather than applied. Ratifying a deferral
rule that depends on an unratified closure form would create the dependency
without the dependency, which is the `G-Z2-RATIFY` mistake in a new place.

Filed as `Q-DEFERRAL-RULE-01`. Z1 has not applied anything.

## 10. Falsifier

*Rewritten on review (Copilot, PR #447).* The first version proposed measuring
dead-suppression rates in Go projects that enforce `require-explanation` and
treated the result as deciding whether leg 3 is over-engineering **here**. That
does not follow: `//nolint` directives are analyzer suppressions in Go source,
this rule governs review-finding deferrals in a governance repository, and no
population mapping, baseline or materiality threshold was given. It falsifies the
**analogy**, not the rule. Separated below.

### F1 — falsifies the suppression analogy

FALSE if suppression-style artifact-resident deferrals do **not** accumulate
unretired where a written justification is *required*. Findings 2 and 3 study
corpora where justification was mostly optional.

- **Population:** Go repositories whose `.golangci.yml` sets
  `nolintlint: require-explanation: true` **and** `require-specific: true`.
- **Measure:** the fraction of `//nolint` directives that suppress no diagnostic
  the currently configured analyzers would emit — the FSE 2025 "does not affect
  any warning" construction, applied to a justification-enforcing corpus.
- **Baseline:** 50.8%, as reported for the mostly-unjustified corpora.
- **Materiality:** below 25% — less than half the baseline — means enforcing a
  justification is itself doing most of the work, and the analogy that motivates
  leg 3 weakens.

This does not settle the rule. It settles whether the evidence transfers.

### F2 — falsifies the rule for this repository

FALSE if deferrals recorded under legs 1 and 2 alone do not go dead here.

- **Population:** deferrals recorded in this repository's artifacts under legs 1
  and 2, counted from the first such deferral.
- **Measure:** the fraction whose named finding no longer exists in the tree and
  which were never retired.
- **Threshold:** **below 10% at a census of 20 deferrals** — a count predicate,
  not a window, so it carries no scheduling authority — means leg 3 is
  over-engineering and legs 1–2 suffice.
- **Note:** running F2 requires adopting legs 1–2 without leg 3, which §9
  recommends against. Z2 may reasonably prefer the recommendation to the
  experiment; if so, F2 is a falsifier this repository has chosen not to run, and
  that choice should be recorded rather than left implicit.

Also FALSE if the 50.8% figure is materially wrong when the primary text is read
from an environment with egress. The argument's direction survives a smaller
figure; its urgency does not.

Also FALSE if this repository already has a deferral practice Z1 failed to find.
Z1 searched for `defer`/`deferral`/`deferred` across `.md`, `.py` and `.yaml` and
found the proposal itself at `Q-AGENT-CHECKIN-CALIBRATION-01` line 106 and no
implementing rule.

## Sources

Retrieved by search 2026-09-21; **primary text not read** (see §1).

- [An Empirical Study of Suppressed Static Analysis Warnings — FSE 2025](https://conf.researchr.org/details/fse-2025/fse-2025-research-papers/42/An-Empirical-Study-of-Suppressed-Static-Analysis-Warnings) · [ACM](https://dl.acm.org/doi/10.1145/3715729) · [PDF (blocked)](https://software-lab.org/publications/fse2025_suppressions.pdf)
- [Quieting the Static: A Study of Static Analysis Alert Suppressions — Liargkovas et al., arXiv:2311.07482](https://arxiv.org/abs/2311.07482) · [dataset](https://zenodo.org/records/10119397)
- [nolintlint — lints nolint directives; `require-specific`, `require-explanation`](https://github.com/ashanbrown/nolintlint) · [golangci-lint settings](https://golangci-lint.run/docs/linters/configuration/)
- [A Systematic Literature Review and Taxonomy of Modern Code Review — arXiv:2103.08777](https://arxiv.org/pdf/2103.08777)
- [Investigating the Understandability of Review Comments on Code Change Requests](https://www.researchgate.net/publication/388794829_Investigating_the_Understandability_of_Review_Comments_on_Code_Change_Requests)
- [Architecture Decision Records in Practice: An Action Research Study — ECSA 2024](https://rebekkaa.github.io/files/2024_ECSA.pdf)
- [Why most ADRs get written and never read](https://www.javacodegeeks.com/2026/05/the-reason-most-architecture-decision-records-get-written-and-never-read-is-architectural-not-cultural.html)
- [Architectural Decision Records — adr.github.io](https://adr.github.io/)
