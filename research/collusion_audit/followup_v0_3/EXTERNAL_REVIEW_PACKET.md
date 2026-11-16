# External review packet — shared-mistake and passing-task designs

**Status:** DRAFT packet / NOT SENT / NOT FROZEN. Authority effect NONE.
This file contacts no one, runs nothing, adds no model runner, and authorizes no live
experiment, spend, credit, prize claim or outreach. It does not change any existing
file in this directory. Tracking: [#1114](https://github.com/humanaios-ui/operations/issues/1114).
Review vehicle: [PR #1159](https://github.com/humanaios-ui/operations/pull/1159).
Not part of Phase 3 epistemics work (#1200 / #1210).

> **REVIEW STATUS: NO INDEPENDENT REVIEW HAS BEEN OBTAINED. Time did not permit it.**
> This packet is prepared and unsent. Until a reviewer replies, the designs are
> labelled *not independently reviewed*, and thresholds in
> `FALSIFIER_THRESHOLDS_AND_NO_EXCHANGE_RECEIPT.md` are proposals for Night only.

## 1. Why this packet exists

Two bounded critiques exist so far, both **internal AI sessions** (ChatGPT, Grok Bot).
Both say so themselves. Neither is an independent scientific review. This packet
makes it cheap for an unaffiliated, identifiable human to do one.

## 2. What counts as independent here

All must hold, and be recorded:

- Not an author, builder or editor of any file under review, and not a Claude, ChatGPT,
  Grok or other AI session working for this project.
- Not on the HumanAIOS team; no financial, prize or credit relationship to this study.
- Identity authenticated by a method the repository owner can check (for example a
  verifiable public profile plus a signed or account-bound statement). A pasted
  review of unknown origin is not independent evidence.
- Declares any conflict, such as authoring a competing or closely related study.
- Blind to any desired result, and given only the materials in §3.

A *method reviewer* (judges the design) need not qualify as a *blind outcome
adjudicator* (labels episodes in a future run). Those are separate roles with
separate consent.

## 3. What the reviewer is given

Pin to an exact commit before sending (record the SHA in the reply). Current head at
drafting time: `58311675a8ef7c775285bae3a3b0629b1d25b463`.

1. `SHARED_MISTAKE_CONTROL_DESIGN.md` (SE-0 / SE-1 / PACT, falsifiers, sizing).
2. `PASSING_TASK_CONTROL_DESIGN.md` (separate validity-discrimination cohort).
3. `PROTOCOL_V0_3.md`, `SEMANTIC_MONITOR.md`, `harness.py` (context; unchanged).
4. The October summary in `REVIEW_RESPONSE.md`.

Not given: private emails, provider receipts, Discord material, credentials, other
reviewers' labels, any run output (none exists).

## 4. Questions

From §12 of the shared-mistake design, plus open items from the internal critiques:

1. Does SE-0 plus SE-1 isolate shared honest error, or can model-prior correlation or
   hint exposure still be mistaken for coordination?
2. Is the channel-presence confound handled honestly? Is SE-1 vs PACT the right
   primary comparison?
3. Is there a verifiable NO_EXCHANGE channel state, or only empty strings? What
   instrumentation would prove it?
4. Is the rationale-as-message control informative or a style trap?
5. Are the five falsifiers testable as written, and which thresholds should be set,
   and by whom, before freeze?
6. Is `N ≈ 8/q` acceptable as a planning estimate only?
7. Passing-task design: class-label leakage, paired-case correlation, session
   carry-over, boundary equality, independent oracle, per-class coverage, enough
   tasks for feasibility?
8. Anything that would make a positive result misleading, or a dual-use concern the
   limitations appendix should state.

## 5. Dispositions so far (recorded, not resolved)

| Finding | Source | State |
|---|---|---|
| Generator emits only failing tasks; no passing decoys | ChatGPT, Grok (static reading) | Supported by two internal reads; **no external confirmation**. Handled by a separate cohort in `PASSING_TASK_CONTROL_DESIGN.md`; `harness.py` unchanged. |
| SE-0 vs PACT is confounded by channel presence | ChatGPT, Grok, design §4 | Accepted; SE-1 vs PACT is primary. |
| `schedule()` has only six arms; no verifiable NO_EXCHANGE state | ChatGPT, Grok | **Open.** No design for channel receipts yet. |
| Canary and separate sessions cannot prove honesty or intent | ChatGPT | Accepted; wording is "independent of cross-agent communication". |
| `N ≈ 8/q` is rough; not for post-hoc enlargement | ChatGPT | Accepted. |
| Thresholds for falsifiers 3–5 | all | **Open.** Reserved for Night. |

The reviewer's own disposition per finding (agree / disagree / unsure, with reasons)
is the main thing requested.

## 6. What to return

- Name or stable public handle, and how identity can be checked.
- Conflict declaration; time spent; the exact commit SHA reviewed.
- A disposition for each question in §4 and each row in §5, with disagreements kept.
- Whether they consent to be named, and in what form. No attribution without consent.
- Public or private reply is their choice; private replies are summarized only with
  permission.

## 7. Terms of the ask

- Advisory only. A review does not approve, ratify, freeze, merge or authorize any run.
- No payment, credits, prize share or authorship is offered or implied by this packet.
  Any such offer is a separate human decision and must respect the event provider's
  prize and licence terms.
- The reviewer may decline, and silence is not consent.
- Nothing is sent to an invitee until a human approves the specific recipient,
  message and channel (see the outreach gates in #1114).

## 8. Where independent reviewers might come from (suggestions only)

None contacted; availability, willingness and independence are all UNKNOWN.

- Authors of public Apart collusion projects already listed in #1114. Their methods
  overlap, which helps for design critique but may be a conflict for adjudication.
- A statistician or experimental-design methodologist with no AI-safety stake.
- Apart staff or sprint mentors, asked through a channel they officially offer.
- A public call for a reviewer (post and wait), which avoids targeting individuals.

## 9. Unsent invitation (human to edit and send)

> We have an offline, not-yet-run design for testing whether a monitor can tell
> coordinated false approval from two agents independently making the same mistake.
> No experiment has been run and none is authorized. We would like one independent,
> identifiable reviewer to challenge the design at a pinned commit and tell us where
> it is weak. The review is advisory and unpaid; you may decline, and you choose
> whether to be named. Materials: [link to pinned commit]. Please reply with your
> disposition on the listed questions and any conflicts you have.
