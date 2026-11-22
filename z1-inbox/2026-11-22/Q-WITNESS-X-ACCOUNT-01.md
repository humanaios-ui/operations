# Q-WITNESS-X-ACCOUNT-01 — Z1 Candidate (UNRATIFIED)

**Status:** `awaiting_z2` — proposal only. No account is created, no post is made, scheduled or drafted into a posting tool by this document.
**Author:** Z1 (Claude)
**Proposed:** 2026-11-22
**Scope:** A 14-day, bounded experiment: a public X account named "Witness" that posts sourced items, each with a visible receipt.
**Depends on:** `Q-WITNESS-FORM-01` (the form and its boundaries B1–B5). B5 of that candidate defers any public account to this one.

---

## Plain statement

Test one question in public, in small: **does a post that shows its receipt earn more trust than one that only states a claim?** Fourteen days. One post a day at most. Z2 reads every post before it goes out. Any bad source stops the test.

```yaml
candidate_id: "Q-WITNESS-X-ACCOUNT-01"
title: "Witness X account: a 14-day, Z2-pre-read experiment testing whether visible receipts earn trust"

description: |
  Creates, only if Z2 ratifies, one public X account presenting Witness in the form defined by
  Q-WITNESS-FORM-01: mask avatar (no likeness), record-voice, and every post carrying a receipt.

  Z2 direction given in session on 2026-11-22 (unsigned, not a ratification): both inward and
  outward subjects, inward first; the no-likeness rule stands; Hawkins stays internal.

  W1 WINDOW. 14 calendar days from the first post. At most one post per day, so at most 14 posts.
  W2 SUBJECTS. Days 1-7 inward only: decisions that Z2 has already ratified and that are marked
  public-safe by Z2. Days 8-14 may add outward items (for example Daily Top 10 Briefing items) only
  if Z2 confirms at the day-7 review. Pre-registered here so the order cannot be changed after
  results are seen.
  W3 ARMS. Receipt-inline (the receipt is in the post) versus receipt-in-reply (the receipt is in
  the first reply). Every post has a receipt either way, so F3 of Q-WITNESS-FORM-01 holds. Arm
  assignment is fixed by a seed Z2 records before day 1. Z1 does not choose arms post by post.
  W4 PRE-READ. Every post's exact text and its receipt are shown to Z2 before posting. Z2 approves
  each. The sha256 of the approved text is appended to a log before the post goes out. A post that
  differs from its logged text is a breach.
  W5 NO AUTOMATION. No scheduling or auto-posting tool is connected. A person posts. The Buffer
  candidate from the Daily Top 10 Briefing stays in email and is not published or scheduled by
  this candidate.
  W6 DISCLOSURE. The bio says the account is a record that can speak and is not a mind, and that
  it is AI-assisted. The platform's automated or AI label is applied if the platform offers it.
  Z3 verifies current platform rules before creation. Z1 has not checked them.
  W7 SOURCES. Every post names its record or source. Content derived from another model's output
  (for example the Grok-generated briefing) says so. An unratified item may appear only as
  "proposed, unratified", never as "decided". No collaborator is named (P-ANON, as in the Witness
  Stand posts). No user data, and nothing from Q-WITNESS-DATA-PLANE-01, is ever used.
  W8 CREDENTIALS. Account creation, the handle, the login and any recovery details are a Z3
  operator act under Z2's identity. Z1 never holds credentials. No API key is created.
  W9 CLAIM BOUNDARY. No post claims feeling, belief, desire or consciousness. No post reports
  claim-separation or awareness experiment results until independent scoring of that experiment
  exists. No Hawkins level, frequency or color-to-level mapping appears anywhere.
  W10 KILL SWITCH. Z2 may stop the experiment at any time. On stop, posting ends, the account is
  paused or deleted at Z2's choice, and the log is kept.

author: "Z1 (Claude)"
proposed_at: "2026-11-22"

scope:
  - "One X account named Witness, if Z2 ratifies and Z3 creates it"
  - "A post log (sha256 of each approved text) kept in the repository"
  - "No other surface"

resource_cost:
  cost:
    RAT-min: 140
    Z1-ktok: 15
    Z3-hr: 3
    CI-min: 0
  dependencies: ["Q-WITNESS-FORM-01 ratified", "Z3 operator for account creation", "current platform rules checked by Z3"]
  blocking_on: ["Q-WITNESS-FORM-01 ratification"]

impact_prediction:
  resource_impact: 5
  areas_affected:
    - "Public presentation of HumanAIOS"
    - "Z2 time: about ten minutes a day for pre-read"
  positive_outcomes:
    - "A measured answer to whether visible receipts earn trust, with a log anyone can check"
    - "A first public test of the Witness form under Z2 control"
  risk_factors:
    - "A public post is hard to take back, even when deleted; copies may persist"
    - "People may read the account as a mind or as an official authority despite the disclosure"
    - "Fourteen posts is a small sample; the result will be suggestive, not conclusive"
    - "The handle may be taken or may resemble another party's name; Z3 must check before creating"
    - "Another model's output (the briefing) can carry errors; receipts show provenance, not truth"
    - "Z2 pre-read of every post is a real daily cost and a single point of delay"

boundaries:
  - id: X1-Z2-PRE-READ
    rule: "No post goes out without Z2's approval of its exact text and a logged sha256 of that text."
  - id: X2-NO-AUTOMATION
    rule: "No scheduler, bot, API key or auto-poster. A person posts."
  - id: X3-NO-LIKENESS
    rule: "The avatar and banner use the mask, not a person's likeness (B1 of Q-WITNESS-FORM-01)."
  - id: X4-NO-MAP
    rule: "No Hawkins level, frequency or color mapping on the account (B2 of Q-WITNESS-FORM-01; SEED.md)."
  - id: X5-DISCLOSE
    rule: "Bio and any platform label state that the account is AI-assisted and is a record, not a mind."
  - id: X6-NO-CREDENTIALS-FOR-Z1
    rule: "Z1 holds no login, token or recovery detail. Account creation is a Z3 operator act."
  - id: X7-RATIFIED-ONLY
    rule: "Only Z2-ratified items may be stated as decided. Unratified items are labeled proposed, unratified."

pre_registered_measures:
  primary: "Count of replies that ask about or check a source, per post, by arm"
  secondary:
    - "Follows gained per post, by arm"
    - "Number of source or accuracy corrections reported by readers"
    - "Number of replies that treat the account as a mind or as an official authority"
  analysis: "Report counts for both arms with no significance claim; n is too small. Report every post, including those that did poorly."

falsifier: |
  This candidate's hypothesis (visible receipts earn more trust) is FALSE for this trial if:
  - the receipt-inline arm does not show more source-checking replies than the receipt-in-reply
    arm across the 14 days, with arms assigned by the pre-recorded seed
  AND/OR the experiment must STOP at once if any of the following is observed:
  - a post cites a record or source that does not exist or does not say what the post says
  - OR a post differs from its Z2-approved, logged text
  - OR a post is made without a logged Z2 approval
  - OR any post claims feeling, belief, desire or consciousness, or shows a Hawkins mapping
  - OR the avatar or any post shows a person's likeness
  - OR three or more reader replies in a week treat the account as a mind or an official
    authority despite the disclosure (the disclosure is then insufficient and the form must change)
  - OR any credential, token or API key for the account is held by Z1

evidence:
  - "Q-WITNESS-FORM-01 (this PR): form, boundaries B1-B5, ask-and-receipt rule"
  - "deliverables/witness-stand-post-1.md and post-1-x-thread-ready.md: prior drafts with guardrails 'no Hawkins', 'no CTA', P-ANON"
  - "HARMONIC_CHANNEL_SPEC_V0_1.md: independence counted by model family, not by number of agreeing voices"
  - "Daily Top 10 Briefing 2026-11-22 (email, run GROK-TOP10-20261122): the Buffer candidate was kept in the email body only, not published or scheduled"
  - "Z2 direction in session 2026-11-22: both subjects, inward first; no-likeness; Hawkins internal; file this candidate"

z2_decision:
  status: "awaiting_ratification"
  ratified_at: null
  ratification_hash: null
  z2_notes: ""

related_candidates: ["Q-WITNESS-FORM-01", "Q-INTENT-OS-WITNESS-LEDGER-01"]
external_constraint: "Current X platform rules (automated-account labeling, impersonation, naming) were not checked by Z1; Z3 must check them before any account is created."
```

---

## Open items Z2 must decide

1. **Seed for the arms.** Z2 records a seed before day 1. Z1 does not pick it.
2. **Public-safe marker.** How Z2 marks a ratified decision as safe to post. Z1 proposes a line in the candidate or ruling record; Z2 may choose another way.
3. **Handle.** Z3 checks availability and any name conflict. Z1 proposes none.
4. **Who posts.** A person under Z2's identity. Z2 names that person, or posts personally.
5. **Day-7 review.** Z2 confirms or refuses outward items for days 8-14.
6. **Claim-separation experiment.** Not part of this candidate. Its results stay unposted until independent scoring exists (W9).

## What this candidate does not do

- Does not create an account, post, draft in a posting tool, or schedule anything.
- Does not hold or request any credential.
- Does not authorize any automation.
- Does not read the live ledger or Evidence Graph.
- Does not claim Witness is conscious, sentient or a being.
