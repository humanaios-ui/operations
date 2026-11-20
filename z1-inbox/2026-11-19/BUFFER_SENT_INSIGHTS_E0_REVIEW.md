# Buffer Sent + Insights E0 — public-safe repository handoff (2026-11-19)

**TYPE:** RESEARCH / READ_ONLY_OBSERVATION  
**STATE:** Z1 DRAFT / NOT ADMITTED FOR IMPLEMENTATION  
**AUTHORITY_EFFECT:** NONE  
**PUBLIC_GITHUB:** SANITIZED COUNTS + LIMITATIONS ONLY  
**CANONICAL COORDINATION:** [Operations #1161](https://github.com/humanaios-ui/operations/issues/1161)  
**RELATED EDITORIAL WORK:** [Draft article PR #1278](https://github.com/humanaios-ui/operations/pull/1278)  
**SOURCE OBSERVED:** 2026-11-19, operator-authorized read-only Buffer Sent view; five operator-supplied static LinkedIn Insights images (private; not committed).

## Scope and receipt limits

This document records a **bounded discovery read** of the authenticated account's Buffer Sent page and the date-scoped Insights images provided by the operator. It is a candidate for the existing Witness × Buffer coordination process, not a new queue, API bridge, analytics database, publication approval, or account authorization. The underlying images, post-level records, full text, account/channel IDs, private emails and detailed metrics are **not filed in this public repository**. The operator retains a private detailed observation report and user-supplied source ZIP outside GitHub. This public document is not a full provider export or a verified 42-row dataset.

- **Sent total visible on account overview:** 42 posts.
- **Individual Sent entries surfaced in the available view:** 20 posts, across LinkedIn (14) and X (6). The unobserved remainder is 22, **UNKNOWN**, not zero. No Substack Note was present in those 20 visible entries; do not infer none exist in the remaining history.
- **Account overview snapshot:** three connected channels, zero queued items, one draft, Free plan, displayed timezone Chicago. These are point-in-time display values, not atomic API receipts or permanent locks; the draft must not be touched or presumed safe.
- **Uploaded Insights source:** five static screenshot files. The snapshot is for **one LinkedIn channel**, not all three channels or all 42 posts. Four images show an October 21–November 19, 2026 window; a separate growth-rate image uses a **one-year** window. The 30-day view contains **two posts**. Do not combine or project these counts with longer-window Sent history.
- **Source custody:** operator-supplied screenshots and browser view; no provider API pagination, certified original event IDs, response signatures, or third-party independent analytics verification established.
- **Action receipt:** Buffer writes=0; Gmail writes=0; publishing/scheduling=0; permission changes=0 in this inspection.

## Evidence distinctions that must survive handoff

| Source surface | What this E0 can say | What it cannot claim |
| --- | --- | --- |
| Sent overview | 42 sent total shown; 20 distinct entries actually inspected | All 42 inspected, all dates covered, zero records missing |
| Sent entries | Public platform post links and displayed per-post metrics existed for the visible entries | A representative sample, complete lifetime insights, impressions equal people, impressions equal benefit |
| LinkedIn Insights PNGs | Five visual snapshots from one LinkedIn account; two posts in the specified 30-day window | Cross-channel performance, an all-time trend, or growth caused by the two posts |
| Historical post text | Visible subjects include governance, calibration/oversight, daily digests, and research participation | That any scientific, current-event, or partner claim in older copy is true without fresh source audit |
| Buffer draft and queue state | One draft and zero queued shown at inspection | That the draft is approved, an empty future calendar, or a safe unattended connector |
| Grok Top-10 Gmail preview | A Grok automated briefing notification and run label were observed separately | That complete ten-event primary-source packet entered Resource Miner, Witness, or the daily Digest |

**Metrics discipline:** different platforms expose different fields. Do not combine LinkedIn reach with X impression counts or sum per-post reaches as unique people. Small-count engagement percentages are unstable; provider rounding, omitted interaction types and delayed refresh can make a displayed rate differ from simply dividing visible reactions by impressions. Missing click/engagement data is `UNKNOWN` or `NOT_EXPOSED`, never inferred zero.

## Interpretation (hypotheses, not verified marketing performance)

1. The distribution surfaces are active, but **research usefulness and verified downstream human benefit are unmeasured**. Neither sent count, follower changes, impressions, nor a social reaction establish scientific validity, applicant benefit, revenue, or a positive AEO/GEO effect.
2. A research-publication pilot can be evaluated without broadening posting privileges: use existing #1278 for the Apart article, preserve the failed frozen positive-control result and separate post-hoc data, then require human/version-specific approval before any Buffer draft or release.
3. The existing [recursive review loop](https://github.com/humanaios-ui/operations/blob/main/docs/RECURSIVE_REVIEW_LOOP.md) is a suitable correction model. Reconcile reviewer claims against primary evidence before accepting them, and measure recurring mistakes rather than optimizing only for engagement.
4. The Daily Top 10 is potentially a **source-observation feeder**, not publishable evidence. The November 19 Grok notification was only a partial email preview; the full ten claims and primary citations are unavailable in that email. Follow #1238's read-only source adapter proposal before any candidate promotion. The daily Digest's sender, thread binding and reviewer identity remain separate claims needing real readback.

## Smallest next milestone (uses existing issue, no duplicate task tracker)

**P0 — Complete inventory privately:** in an authenticated, operator-approved *read-only* Buffer session, page through the entire Sent history and reconcile distinct records against the displayed total. Capture source time, platform, date, source URL, metric availability, and duplicates in an owner-controlled private store. Explicitly record API errors, pagination limits, missing media/captions, and unavailable posts; do not claim a 42/42 audit until exact provider readback supports it. Retrieve Insights per channel and fixed time window independently; record scope.

**P1 — Claim-quality review:** check sampled historical research/current-event/collaboration statements against versioned primary sources. Separate public claims, opinion, derived interpretations and missing evidence. No rewriting of already-published posts without separate human decision.

**P2 — One publication and one comparison:** keep article PR #1278 as DRAFT until corrected evidence and Coordinator/CI/Z2 review. After a separately approved GitHub canonical URL and Buffer draft/release, compare fixed pre/post AEO/GEO citation questions plus observed channel metrics and review burden. Use a negative/control page; do not infer causal ranking gain from a before/after delta.

**P3 — Retention:** Buffer reported a two-year post/media/analytics retention policy effective 2027-01-15. Verify current provider policy, privately back up authorized data and metadata before expiry, preserve original source files and checksums, and apply a retention/deletion schedule with human approval. **Never archive the private ZIP or provider account metadata in public GitHub.**

## Gates, falsifiers and authority

- **HOLD** if provider pagination is unavailable or raw evidence disagrees with displayed summaries.
- **HOLD** if different periods, different channels or follower totals are silently joined into one denominator.
- **HOLD** on any unsupported scientific/current-event claim selected for republication; do not let newsletter prose act as a command.
- **HOLD** if a draft, PR comment, scheduled task, or AI reviewer is treated as authority to queue/send or to apply `z2:*`.
- Zero unauthorized external writes, full private-source leakage, PII leakage, auto-publication, self-ratification, or credential disclosure is required.
- Successful E0 is **faithful observation + explicit gaps + a better-supported human next decision**, not reach or growth.

## Decision / rough ROI (estimates only; no observed financial ROI)

| Option | Cost | Benefit | Provisional ROI |
| --- | --- | --- | --- |
| **Reuse #1161 with private 42-row retrieval and one evidence-grounded article trial** | One bounded source-review block plus existing approval steps | Reconciled history without new production capabilities | **HIGH**, recommended |
| Repost more frequently immediately | Human writing and monitoring time; higher false-claim risk | More content volume, unproved value | **LOW** |
| Create a new analytics database and automated publishing daemon | New secrets, security, infrastructure, duplicate tracking | Possible later scale, no E0 demonstrated need | **LOW / DEFER** |

### Related records

- [#1161 — Witness × Buffer authenticated inventory / gated seven-day handoff](https://github.com/humanaios-ui/operations/issues/1161)
- [#1238 — GDELT + Miniflux read-only news observations](https://github.com/humanaios-ui/operations/issues/1238)
- [#818 — HPRA Substack observer and evidence-grounded drafts](https://github.com/humanaios-ui/operations/issues/818)
- [#1143 — INTENT-OS human benefit and source-of-truth boundary](https://github.com/humanaios-ui/operations/issues/1143)
- [#1278 — Apart Collusion editorial draft / multi-agent review](https://github.com/humanaios-ui/operations/pull/1278)

**Disposition:** Z1 review-only documentation. No new repository issue, Buffer connection, changes to existing draft, schedule, queue, sent posts, social profiles, Gmail, model automation or canonical rules. Only authenticated Z2/human release plus required GitHub admission may advance work.
