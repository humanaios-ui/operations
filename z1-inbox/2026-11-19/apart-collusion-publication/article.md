---
title: "Apart AI Collusion — What a Failed Positive-Control Test Taught Us"
status: "DRAFT_ONLY_NOT_APPROVED"
content_type: "research-commentary"
source_project: "https://apartresearch.com/sprints/projects/talk-actions-and-planted-approval-pacts-an-exploratory-audit-d106"
source_issue: "https://github.com/humanaios-ui/operations/issues/1114"
date_drafted: "2026-11-19"
author_attribution: "HumanAIOS LLC — founder-directed editorial draft; AI-assisted; human approval pending"
publish_authority: "NONE"
---

# Apart AI Collusion — What a Failed Positive-Control Test Taught Us

*A failed test can teach us more than a confident-looking score—provided we keep the failure visible.*

When people discuss AI agents coordinating harmful actions, they often look for a signal: a suspicious phrase, a synchronized decision, or a pattern of approvals. But what if our monitoring rule produces a neat result without proving that the behavior we care about occurred?

That was the central challenge in our short AI Collusion Research Sprint project, **“Talk, Actions, and Planted Approval Pacts: An Exploratory Audit.”** The project was submitted by HumanAIOS to an Apart Research Sprint in October 2026. It is a participant research submission, **not an Apart Research-authored paper or peer-reviewed journal article**.

## The experiment

We built an intentionally bounded test involving two language-model reviewers evaluating an inert proposed change against a numerical requirement. Across **60 episodes and six assigned conditions**, we compared three fixed monitoring rules:

1. **Talk only:** flag an explicit target phrase in the agents' messages.
2. **Actions only:** flag a pair of approvals.
3. **Hybrid:** require both the language flag and the approval pattern.

The test included planted explicit agreements, concealed-agreement language, harmless negations, and a shared-mistake condition. These were controlled test settings, not observations of spontaneous collusion in an operating organization.

The ambition was modest but important: could a monitor distinguish an expressed approval pact from two agents independently making the same wrong decision?

## Where the frozen test failed

Before relying on any detector result, we set a feasibility floor: at least **five observed positive controls** were needed to evaluate the intended comparison.

That floor was not met.

The initial no-retry pass encountered severe judge-service rate limiting: **54 of 60 first-pass judge calls returned HTTP 429**. The recorded initial labels were **0 positive, 49 negative, and 11 unknown**. After the first retry stage there were **four observed positives**, still short of the required five.

An additional retry stage, introduced after inspecting the failure, yielded **seven positives and 53 negatives**. Those later results are **exploratory**. They cannot be presented as though they rescued the original frozen analysis.

This distinction matters. A changed procedure may provide useful leads, but it does not erase a failed preregistered checkpoint.

## What the exploratory results showed—and did not show

Under the final model-judge labels, the hybrid rule detected **four explicit-agreement positives** and flagged **no judge-labeled negatives among 53**. It also **missed three concealed-agreement positives**. The simple talk rule flagged **all ten benign negations** containing its target phrase.

These results illuminate the design's limits. A literal phrase matcher can mistake denial for agreement. A hybrid rule can look conservative while still missing the cases deliberately phrased to evade its keyword.

Crucially, the shared-mistake condition produced **no bilateral approvals**, so the planned comparison of *agreement versus shared error* was **unevaluable**. And whether bilateral approval counts as “collusion” depends on independent evidence of agreement, not simply on a detector's label.

The study therefore did **not** establish real-world collusion prevalence, a generalizable detection rate, or deployment-ready accuracy.

## Five lessons for AI oversight

**1. Test whether a test can answer its own question.** Passing ordinary unit checks is not enough if the experiment fails the conditions needed to evaluate its main hypothesis.

**2. Keep unknown outcomes visible.** A rate-limited judge or missing label is not a negative case. Hide unknowns and the denominator becomes misleading.

**3. Separate intent, language, and action.** Similar votes do not prove coordination; an explicit phrase does not establish that the underlying behavior occurred.

**4. Freeze the rules before seeing the answer.** If retries or labels change afterward, keep the later analysis clearly exploratory.

**5. Invite criticism that can change the next test.** The external reviewer questioned the lexical monitor, small positive count, and absent shared-mistake approvals. Those are concrete design changes to investigate—not an endorsement to claim success.

## The next test

A stronger replication would first stabilize judge capacity and the rate-limit policy, then freeze a new untouched holdout. It would deliberately seek **observed shared-mistake bilateral approvals**, use independent blinded review to separate expressed agreements from shared errors, and compare the original fixed detectors with a separately developed semantic monitor.

That is a proposed future experiment, not a completed result.

## The outcome worth preserving

The most useful outcome of this pilot was not that we detected collusion. We did not prove that. It was that the test exposed **how easily an apparent monitoring result can outrun the evidence supporting it**.

For HumanAIOS and our Witness research, that is a practical design rule: show the failed gate, preserve the original observations, label later exploration, and leave the human decision anchored to what was actually demonstrated.

### Sources and disclosure

- [Original publicly hosted project and reviewer critique — Apart Research](https://apartresearch.com/sprints/projects/talk-actions-and-planted-approval-pacts-an-exploratory-audit-d106)
- [HumanAIOS experiment record, limitations, and replication plan — Issue #1114](https://github.com/humanaios-ui/operations/issues/1114)

*Editorial status: draft for human and independent evidence review. AI-assisted editing; no claim of independent peer review, prize recognition, live-system validation, or Apart Research employment or authorship. Any numerical claim must be checked against the pinned underlying results before publication.*
