# Apart Swarm Alignment 2026 — two distinct receipt milestones (E0, read-only)

**Status:** SOURCE-BOUND PROPOSAL / NO AUTHORITY EFFECT. Observation: 2026-11-09. Linked issue: [#1114](https://github.com/humanaios-ui/operations/issues/1114), journey specification [#979](https://github.com/humanaios-ui/operations/issues/979), draft sensor [#1155](https://github.com/humanaios-ui/operations/pull/1155). This document contains no private email, mailbox ID, participant address, form-response link, or nonpublic Apart project link.

## Parent source and deduplication

- Provider: Apart Research; canonical sprint: https://apartresearch.com/sprints/swarm-alignment-2026
- Existing November opportunity ID: `OPP-APART-SWARM-20261106`; **not** the October AI Collusion sprint and **not** the separate Apart Fellowship.
- Deadline: 2026-11-08 23:59 Anywhere-on-Earth = **2026-11-09 11:59Z / 05:59 CST**.
- Project title (public-facing): **Claims, Actions, and Verified Outcomes: Two Evidence Tracks for Multi-Agent Oversight**. Category/track: **Track 4, Multi-Agent Oversight and Control**.
- Distinct child opportunities/decisions: (A) hackathon project delivery/judging; (B) optional post-hackathon funding application/judging; (C) promotional Adaption participation benefit. Do **not** dedupe separate receipts into a single award or invent another canonical sprint.

## Receipt A — hackathon paper (provider email)

- A first-party Apart project-confirmation email, observed using the connected Gmail reader, states **submission received successfully**, timestamp **2026-11-09T11:28:02Z**, before the deadline. The message carries the submitted **seven-page PDF attachment**.
- Attachment checked locally: **SHA-256 `1e53b529fc14bab92c077fd15a185f154da181b7587b5e17c261b623cefd7248`**; title matches the project. This is the **submitted attachment**, not the prior local draft (which had different bytes). The submitted revision contains additional explicit host security limitations. Preserve the submitted bytes privately.
- Project lifecycle: `PROJECT_SUBMITTED_RECEIPT` / `PROVIDER_RECEIPT_OBSERVED`; awaiting judging and separate infohazard check. **Do not** infer judged, accepted, won, publicly listed or prize paid. Non-public read-only project link from email must remain PRIVATE.

## Receipt B — follow-on research funding form (separate Notion confirmation)

- Notion acknowledgment email received **2026-11-09T13:22:41Z**: *Thank you for filling out “Funding for your hackathon project”*; says **submission successfully received**.
- The confirmation **does not itself specify the project title, budget amount, recipient, form answers, grant status or requested award**. The human states that it is linked to this submitted project; relationship is therefore **HUMAN_REPORTED_LINK**, pending authenticated form-response readback.
- Proposed distinct status: `FUNDING_REQUEST_SUBMITTED_RECEIPT` / `PROJECT_BINDING_NOT_PROVIDER_VERIFIED`. `ASK_AMOUNT=UNKNOWN`, `FUNDER_SELECTION=UNKNOWN`, `GRANT_AWARD=UNKNOWN`, `DISBURSEMENT=NONE_VERIFIED`.
- Never treat a follow-on **application** or possible public grantmaking.ai listing as an **award**, cash resource, eligible funding or benefit realized. Avoid publishing private Notion response access URLs and any email or payment details.

## Benefit C — Adaption credits (not the funding application)

- The Apart participant email advertises **$500 Adaption platform credits plus three months Premium**, offered separately from any judged award.
- A vendor welcome email stated credits had been **applied**. Dashboard balance, Premium term, redemption and usable quota are **NOT VERIFIED**. Do not record $500 as cash, project grant, award or spent credit. Track in the existing separate benefit case referenced in [#1114](https://github.com/humanaios-ui/operations/issues/1114).

## Resource Miner / Opportunity Journey extraction and promotion boundary

| Resource / action | Evidence now | Permitted projection | Still unknown |
| --- | --- | --- | --- |
| Sprint research submission | Provider receipt + submitted attachment | Project submission receipt observed | Judge acceptance, prize, research approval |
| Follow-on research funding request | Notion receipt + human project linkage | Separate funding form received; link human-reported | Public ask/answers, judged selection, grant disbursement |
| Adaption participation benefit | Apart offer + Adaption vendor assertion | Promoted offer and provider-reported applied | Verified account balance, Premium expiry, realized consumption |

The existing E0 sensor accepts only `PROVIDER_RECEIPT_OBSERVED` as an **unattested** project-submission signal. It cannot yet represent the Notion funding form as a distinct typed child. **Do not forge it into a project submission or silently change the sensor schema**. A future bounded extension needs a separate funding-request state plus source authentication and regression tests.

Private operator tasks: (1) preserve both original provider receipts and submitted PDF in a private evidence vault; (2) verify the actual Notion response fields and matching project identity without publishing the private response link; (3) await real judge/funder decisions; (4) update status using evidence precedence provider decision > receipt > human report > marketing. Maintain `authority_effect=NONE`: no external application, polling, publication, spending, merge, or authorization follows from this intake.
