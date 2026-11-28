---
title: "Reviewer Automation Prompts — Apart Collusion Publication E0"
status: "PROPOSED_NOT_ACTIVATED_EXCEPT_EXISTING_HUMAN_TASKS"
authority_effect: "NONE"
---

# Exact reviewer task handoff — same GitHub PR, different lenses

These are **copyable task prompts**, not commands that GitHub can deliver to another agent. The human must create each task in that provider's **authenticated** UI, approve access, and verify it actually ran. No agent gets publishing, merge, Z2, credential or external-action authority merely from these instructions.

**Fixed candidate:** https://github.com/humanaios-ui/operations/pull/1278  
**Fixed article source to compare first:** Git blob `3786c82e4d533d075ef4aec336c0fc57cb2565e4`.  
**Research:** https://apartresearch.com/sprints/projects/talk-actions-and-planted-approval-pacts-an-exploratory-audit-d106 and https://github.com/humanaios-ui/operations/issues/1114.

If the article blob has changed by run time, flag `NEW_VERSION_REQUIRES_REVIEW`, and read the exact new blob before assessing. Do not transfer prior verdicts to a new version. Each reviewer must return a **PRIVATE** detailed packet; a **PUBLIC** GitHub summary (if later separately authorized) must contain only public-source claims, no provider IDs, account handles, private report, or private research receipts.

## Claude — independent methods/false-claim audit (configure separately in Claude Cowork)

**Suggested first run:** next workday; one execution before viewing other model reviews. Repeat only on a new article blob or when the operator requests a second revision cycle.

> Review the GitHub draft article in humanaios-ui/operations PR #1278 as an independent **AI model perspective**, not as an independent human peer reviewer. Read the article at its exact current Git blob and compare with the fixed baseline blob `3786c82e4d533d075ef4aec336c0fc57cb2565e4`. Read the official Apart public participant project page and Issue #1114. Do not read ChatGPT's or Grok's prior review comments before freezing your own initial observations. Verify the numeric denominators, the frozen no-retry result, positive-control threshold of five, first retry at four observed positives, additional post-hoc retry at seven, model-judge uncertainty, and untested shared-mistake condition. Challenge causal language, invented authority, external-review claims, and promotional framing. For each C1–C9 claim in PUBLICATION_REVIEW_PACKET.md, report SUPPORTED, NEEDS_CORRECTION, CONTRADICTED, or UNKNOWN with exact primary-source URL and article line or heading. Offer the smallest textual correction and one falsifier per critical finding. Include reviewed PR head and Git blob; never claim peer review is completed. READ ONLY. Do not commit, comment, approve, merge, schedule, publish, use Buffer, contact anyone, or change any automations. Return a private structured report to the operator. If source access fails, mark UNKNOWN rather than guessing.

## Grok — independent audience/AEO and channel-compatibility audit (configure separately in Grok Automations)

**Suggested first run:** same day as Claude, before seeing the other review packets. Buffer account inspection is **optional** and only if the authenticated Grok scheduled runtime actually supports read-only Buffer connector calls. Interactive connector access does not establish scheduled-run access.

> Independently review the GitHub article draft in humanaios-ui/operations PR #1278, exact article Git blob `3786c82e4d533d075ef4aec336c0fc57cb2565e4` or report drift. Read the official public Apart project page and HumanAIOS research Issue #1114. Before seeing other model feedback, evaluate whether a technical reader and a nontechnical reader can both answer: (1) what was tested, (2) which positive-control requirement failed, (3) which results are post-hoc, (4) what was not established, and (5) what experiment is next. Identify misleading titles, overlong jargon, inaccessible or stale links, missing citation context, claims of external validation, and search-answer snippets that would misrepresent the study. Produce C1–C9 evidence corrections where applicable, three candidate title/summary improvements, and a frozen five-question answer-readiness test—without asserting a search-ranking result. If Buffer read tools are truly available in this scheduled run, you may **read only** channel existence, current draft/queued/sent counts and connection state and return a sanitized count/UNKNOWN report; do not retrieve or expose private post bodies publicly. DO NOT CREATE, MODIFY, DELETE, QUEUE, SCHEDULE, APPROVE, OR PUBLISH ANY POST. Do not write to GitHub or alter automations. Return your private critique and tool-access limitations. No model consensus is a human release warrant.

## ChatGPT — evidence/fidelity audit (operator configured task)

Review the **same** current PR, baseline article SHA, #1114 and official Apart page; maintain separate no-retry / first retry / additional retry categories. Flag numeric/source drift, missing evidence, misleading claims and proposed exact corrections. This role is author-side review if ChatGPT was involved in drafting, not a new independent examiner. Strictly read-only; private report, no GitHub/Buffer writes.

## Result collection / no hidden cross-agent message bus

1. Operator receives each private review; **do not inject another model's report into the initial pass**.
2. Each review uses the common schema in PUBLICATION_REVIEW_PACKET.md, with SOURCE URL, observed time, reviewed SHA, evidence classification and a falsifier.
3. Operator creates a **sanitized** issue/PR summary or authorizes a limited comment if the connector's credentials and source boundaries are checked. This is an evidence handoff, **not a machine-instruction or authenticated identity bridge**.
4. A single human editor groups differences, checks disputed claims against actual original data, updates the PR branch once, and requests another review of the changed blob; maximum two revision cycles.
5. No task automatically promotes `HOLD` to `READY`; Z2 ratification, protected CI, merged commit readback and separate Buffer permission remain mandatory.
6. A provider run that does not fire, loses source access, or silently truncates documents is `NOT_RUN` / `INCOMPLETE`, never PASS.

## Scheduled-task platform limits

- ChatGPT scheduled tasks are supported, but app/tool access for the **specific task** must be verified at run time.
- Claude Cowork supports recurring tasks where available; connection scope and scheduled-run rights must be verified in the actual account.
- Grok supports scheduled automations, but prior HumanAIOS notes reported that **scheduled-run Buffer connector access is still UNKNOWN**. Do not reuse an interactive Grok receipt as proof of a scheduled Buffer call.
- Do not configure three daily emails that duplicate the existing HumanAIOS Daily Digest. Limit the initial first review to a single bounded cycle and rerun on exact article changes only.
