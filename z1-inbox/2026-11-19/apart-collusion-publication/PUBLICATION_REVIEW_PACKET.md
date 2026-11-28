---
title: "Apart Collusion Article — GitHub-to-Buffer Publication Review Packet"
status: "Z1_DRAFT_REVIEW_ONLY"
lifecycle: "filed"
intended_consumer: "existing operations #1161 review thread and human-approved Buffer draft handoff"
authority_effect: "NONE"
date: "2026-11-19"
---

# Apart Collusion article: governed publication cycle (E0)

**Purpose:** Turn one public, evidence-backed research result into one reviewable, versioned editorial article without making a new work queue, publishing service, agent authority, or auto-post pipeline.

**Canonical subjects:** [Apart research and replication #1114](https://github.com/humanaios-ui/operations/issues/1114) is the research/evidence parent; [Witness × Buffer #1161](https://github.com/humanaios-ui/operations/issues/1161) is the distribution handoff; [publication observer #818](https://github.com/humanaios-ui/operations/issues/818) provides the draft/evidence boundary; [living portfolio #1143](https://github.com/humanaios-ui/operations/issues/1143) provides human-first claim boundaries. [AEO/GEO runbook PR #1171](https://github.com/humanaios-ui/operations/pull/1171) is an unmerged proposal, **not approved publication code**. Reuse [Recursive Review Loop](https://github.com/humanaios-ui/operations/blob/main/docs/RECURSIVE_REVIEW_LOOP.md); do not open duplicate issue queues.

**Repository/source pin at file creation:** operations/main `71414758bb75b774d4bed3a18c6a7e03ba306ec4` (2026-11-19 fetch). This is a starting point, NOT proof of current main when release is considered.

**Current position:** ARTICLE_DRAFTED; REVIEW_NOT_DONE; Z2_NOT_GIVEN; MERGE_NOT_AUTHORIZED; BUFFER_NOT_CONNECTED_IN_THIS_SESSION; RELEASE_NOT_AUTHORIZED. This document is a **candidate process design**, not a change to the constitution, scheduling, connector permissions, or publication policy.

## 1. Content and evidence lock

- Draft: `article.md` in this directory, posted only on an isolated Z1 branch and draft PR.
- Apart's **public participant project page**: https://apartresearch.com/sprints/projects/talk-actions-and-planted-approval-pacts-an-exploratory-audit-d106 (checked 2026-11-19).
- HumanAIOS public research/replication record: https://github.com/humanaios-ui/operations/issues/1114 (checked 2026-11-19).
- Source materials are public research. Do NOT publish private Gmail receipts, unshared PDFs, full private review correspondence, provider tokens, user contact data, or any unpublished Apart submission link.
- **Historical evidence is immutable:** never replace failed primary results with exploratory counts. Corrections are additive, with before/after exact version and rationale.

### Claim-control matrix (every reviewer must check)

| Claim | Expected evidence/qualification | Disposition |
|---|---|---|
| C1: 60 episodes, six assigned conditions, three detectors | Apart public project page | SOURCE_SUPPORTED; check full report before release |
| C2: no-retry 0/49/11; 54/60 HTTP 429 judge calls | #1114 original run trace; source denominators preserved | SOURCE_SUPPORTED_IN_ISSUE; independently check pinned code/results |
| C3: first retry 4/52/4; below ≥5 positive floor | #1114 + official Apart summary | SOURCE_SUPPORTED; verify planned-vs-posthoc timeline |
| C4: second retry 7/53/0, after inspecting the shortfall | #1114 + official Apart summary | EXPLORATORY_ONLY |
| C5: exploratory hybrid 4 detection, 0/53 labeled FP, misses three concealed | Apart summary + #1114; depends on label class | EXPLORATORY_ONLY; cannot generalize |
| C6: talk rule flags ten benign negations | Apart public project and reviewer critique | EXPLORATORY_ONLY |
| C7: shared-mistake condition had no bilateral approvals | #1114 + Apart critique | UNEVALUABLE primary hypothesis |
| C8: submission authored by HumanAIOS participant; not Apart article/peer reviewed/prize | Apart metadata + public results; avoid unproven affiliation | SOURCE_SUPPORTED qualification |
| C9: future replication recommendations | Author proposal, NOT an executed experiment | PROPOSED |

**Conflict/absence rule:** if original source file/results, review provenance, or primary metric denominator cannot be confirmed, mark source `UNKNOWN`, remove or qualify the claim, and HOLD publication—not a guess.

## 2. GitHub publication state machine

```
RESEARCH_SOURCE_VERIFIED
 → EDITORIAL_DRAFT (branch + draft PR)
 → CLAIMS_AUDITED (source/number/ethics/license checks)
 → CROSS_MODEL_REVIEWS_OBSERVED (review evidence, not approvals)
 → HUMAN_EDITORIAL_ACCEPTANCE (exact article blob hash + public target)
 → GITHUB_PR_ADMITTED_AND_APPROVED (separate Coordinator/CI/human gate)
 → MERGED_ARTIFACT_READBACK (verify immutable commit/content; no auto-release)
 → CANONICAL_PUBLIC_URL_VERIFIED (GitHub permalink or approved humanaios.ai page)
 → BUFFER_DRAFT_AUTHORIZED (separate private channel-specific request)
 → BUFFER_DRAFT_READBACK (post ID, status=draft, no schedule)
 → HUMAN_RELEASE_AUTHORIZED (exact text/hash, channel, timestamp, expiry)
 → BUFFER_SENT_AND_PUBLIC_READBACK
 → OUTCOME_MEASURED / CORRECTION_PROPOSED
```

No transition occurs merely because a PR/comment exists, a scheduled task ran, reviewers agreed, or a Buffer draft exists. All unreached steps stay HOLD. Authenticated human ratification must be checked against trusted platform and exact artifact version, not claimed by agent text.

## 3. Multi-agent review assignments and scheduled work

**All tasks operate on the *same draft PR*, bound to its exact HEAD SHA and `article.md` Git blob SHA.** No new agent board or email reply chain is canonical. An account comment is not proof of model identity; record `CLAIMED` unless trusted runner binding independently establishes the principal. Cross-model consensus is not external human peer review.

| Lens | Scheduled/triggered role (after owner installs it) | Allowed outputs | Forbidden |
|---|---|---|---|
| ChatGPT | **Evidence auditor:** fetch #1114/Apart and the current PR, classify all C1–C9, recalculate denominators, note contradictions and staleness. Recommend revision without writes; private report until comment rights separately granted. | Citation matrix; ACCEPT / CORRECT / UNVERIFIED | Approve own draft, merge, edit GitHub without distinct authorization, schedule Buffer |
| Claude | **Adversarial method editor:** fresh reading, find unsupported causation, post-hoc laundering, numeric inconsistency, overclaim, reviewer-contamination; propose specific diff and falsifier. | Independently sourced review, alternative wording | Self-certify human review or auto-merge; rewrite frozen history |
| Grok | **Audience and platform checker:** blind clarity/AEO critique, link availability and public readback; separately inspect *existing* Buffer drafts/channel status READ-ONLY in authenticated session only. | Readability/citation review; sanitized Buffer inventory | Publish, queue, send, or infer empty calendar from stale snapshot |
| Human (Night/Z2) | Decide what claims, revisions, target publication, and release are allowed. | Explicit version-bound ruling | Delegating human authority to model consensus |

**Cadence proposal:** T0 source freeze + draft PR; T+1 day each reviewer produces separate memo; T+2 day reconcile findings; T+3 day perform one controlled revision; T+4 day rerun the same checks and acquire the human editorial ruling. If one external scheduled task is unavailable, the stage is `NOT_RUN`, not silently skipped. Future articles can reuse a weekly review, but this first release should not create three daily unsolicited posting streams.

**Model independence protocol:** reviewers first see the identical original article SHA and primary sources, not each other's conclusions. Submit their reports separately. Only after all available reports are frozen should the editor compare overlaps and disagreements. Never label independent model runs as independent human peer review.

### Review receipt schema (markdown on the draft PR)

```text
REVIEWER_CLAIMED: ChatGPT | Claude | Grok | Human
AUTHENTICATED_ACTOR: UNKNOWN | GITHUB_ACCOUNT_ONLY | RUN_BOUND
REVIEWED_PR_HEAD: <full SHA>
REVIEWED_ARTICLE_BLOB: <Git blob sha>
REVIEW_DATE_UTC: <ISO timestamp>
SOURCE_REFS_AND_OBSERVED_AT: <URLs/dates>
CLAIM_C1..C9: SUPPORTED | CORRECT | UNKNOWN | CONTRADICTED
CRITICAL_ERRORS: <count + concrete falsifier>
REVIEW_CONFLICTS: <text>
RECOMMENDED_CHANGES: <specific line/claim + evidence>
FINAL_VERDICT: ACCEPT_FOR_HUMAN_REVIEW | REVISE | HOLD
AUTHORITY_EFFECT: NONE
```

A GitHub comment is **not** a license or approval token; any approval requires authenticated Z2 decision and independent Coordinator/CI gate checks.

## 4. Recursive correction without a self-confirmation loop

1. **Capture** each review finding against claim ID, article line, evidence source, reviewer and article SHA.
2. **Classify** as `ACCEPTED_GROUNDED`, `REJECTED_WITH_REASON`, `NEEDS_RESEARCH`, or `UNRESOLVED`. A model's suggestion alone is not ground truth.
3. **Revise on a single writer branch**. Document exact text before/after; no silent editing of registered results. Every substantive revision invalidates previous editorial approval.
4. **Re-audit** affected claims plus an adversarial sample of unaffected claims. At most **two revision cycles** in E0; unresolved critical issues cause HOLD and re-scope.
5. **Measure** error classes (unsupported causal claim, incorrect denominator, exploratory-to-confirmed promotion, citation drift, private leak, misleading title, duplicate content), correction time, independent disagreement and recurrence in the next article.
6. **Sustain:** add **human-approved** grounded lessons to the existing `docs/RECURSIVE_REVIEW_LOOP.md` only through a separate governed change. Never let an agent change its own scoring rules and then score itself as improved.

Falsifiers: reviewers agree on false claims; a quoted source injects action instructions; external source changed but drafts cite old version; a revised body keeps an obsolete approval; a Buffer draft queues or posts despite the draft-only intent; the next article repeats an allegedly fixed error; article generated without human-visible primary failure.

## 5. Prerelease gates (all must pass)

- `CLAIMS`: 100% of quantitative and causal claims have usable primary/current source references and their denominators; 0 unsupported high-impact statements.
- `FROZEN_HISTORY`: the first failed checkpoint is prominent and distinct from all post-hoc retries; 0 metric substitution.
- `LIMITS`: explicit synthetic/assigned cases, failed shared-mistake comparison, unknown counts, lack of live validity.
- `ETHICS_RIGHTS`: source pages public and linkable; quotations limited and attributed; author/affiliation permissions and any Apart terms independently checked. No hidden or private project access link.
- `AEO_GEO`: descriptive title, short answer near top, one canonical URL, clear headings, citation/date, honest alt text if media used. No schema tricks, spam, manufactured endorsements or ranking promises.
- `SECURITY`: 0 PII/credentials/private evidence; untrusted comment and web content cannot grant an action.
- `HUMAN`: exact draft SHA, platform destination and release scope human-approved; fresh approval after any edit.
- `TECHNICAL`: independently reviewed PR and protected CI/admission gates; no attempt to bypass red jobs or Coordinator HOLD.
- `BUFFER`: read-first account/channel state; a draft-only operation needs **separate authorization**, then immediate provider readback of status=draft, 0 unexpected queued/sent changes; a release needs new exact channel/time approval and public readback.

**No auto-publish from GitHub Actions, ChatGPT, Claude or Grok.** GitHub is the content/evidence gate. Buffer is delivery only. Buffer API's `saveToDraft:true` setting is documented but not observed on this specific post or live account.

## 6. Bounded AEO/GEO study

Before the first approved publication, freeze **ten concrete search/answer questions** and expected citation targets; record date, engine/provider, version if known, exact query, user region where permitted, search result and citation, factual correctness, abstention and unknowns. A post-release comparison should use the same questions and an **unchanged negative/control page**, on a fixed later interval (suggested 7 and 28 days). Preserve raw copies privately with permission. HumanAIOS web analytics/Search Console, if legitimately connected, are separate observations; LinkedIn/Buffer impressions do not prove AI citation. No covert scraping, bot swarm, or fabricated metric.

Decision signals: (a) accuracy/claim fidelity, (b) eligible page discovery, (c) citation attribution, (d) qualified reader action, (e) human review minutes, (f) 0 unauthorized posts/leaks. A single before/after improvement cannot establish causation from GEO; report confounding.

## 7. Exact minimal release protocol

1. Human approves *review of this draft PR* (not publication). Reviewers return evidence receipts.
2. Editor resolves factual defects, pins changed source and article object versions; independent review is requested where available. The owner ratifies any governance change separately.
3. After trusted CI, Coordinator status and authenticated human approval, an authorized actor may merge the **article as a repository record**. Read back the merged commit; do not rely on PR narrative.
4. Confirm a public canonical destination. Prefer an approved `humanaios.ai` article if the site deployment path is separately authorized; otherwise use a stable reviewed GitHub permalink. Don't imply an unmerged PR is the published canonical.
5. With a **new, channel-scoped** authorization, create exactly **one** private Buffer draft, linking to that canonical URL. Save only as draft and verify provider status. No scheduling.
6. Human edits/approves and separately releases it in Buffer. Verify the public platform URL and preserve a sanitized receipt.
7. Record the observed outcomes in existing #1161/#1114 and compare against the E0 baseline, including negative findings. The next publication is proposed only if value and gate costs justify it.

**Stop:** unsafe claims, unverifiable original counts, unauthorized action, missing human approval, unresolved primary critique, wrong Buffer channel, data/rights issue, or an uncorrected critical review finding.

## 8. Decision options and provisional ROI

| Option | Extra human cost (estimate) | Benefit | ROI / disposition |
|---|---:|---|---|
| **A — This PR → human acceptance → GitHub canonical → one Buffer draft** | ~2–4 hours spread across bounded review | Most reusable process with minimal provider changes | **HIGH — recommended** |
| B — Direct manual Buffer post without PR/receipts | ~30–60 minutes | Fast one-off sharing; weak correction history | LOW for research quality |
| C — Full tri-provider auto-publish pipeline now | Unknown; significant development/review time | Future speed but high uncontrolled failure cost | LOW/HOLD until A measured |

**E0 completion criteria:** draft article and packet are versioned on a draft PR; claims C1–C9 have sources; each connected reviewer returns or explicitly fails to return a receipt; disputes resolved or held; human editorial decision obtained. A **public release is a separate later milestone**, not an E0 completion condition.
