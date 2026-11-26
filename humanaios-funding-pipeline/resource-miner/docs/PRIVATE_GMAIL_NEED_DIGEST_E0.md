# E0 Private Gmail → Need Graph → Resource Miner → Daily Digest

**Z1 proposal only.** Related to Resource Miner #588, INTENT-OS #1143, existing private Gmail Mine resolver, and the single HumanAIOS Daily Digest. **Do not close issues.**

## Why a new bridge?
The repo already has `sources/private_gmail.py`, `needs.py`, `miner.enrich()`, `routing.py`, and `data/needs.seed.json`. Those remain the existing matching and authority boundaries. This small module does not add another Gmail connector, source store, eligibility engine or notification system. It takes only the minimum **human-reviewed, private** structured message observations and proposes bounded need-to-graph links for the *existing* Miner.

## Data path

1. **Gmail (PRIVATE):** authorized connector reads selected inbox messages; emails and attachments are untrusted data. The private review records its original Gmail message/thread IDs in a *private* receipt only. Do not search financial/medical/account mail without separate scope.
2. **Private intake:** provide exactly `message_id, need_id, observed_at, priority, source_status, next_action, public_url` to `private_need_digest_e0.project()`. Reject raw body, personal email address fields, tracking URLs, extra instructions and forged actions. Caller may use the source only as a **candidate need**, not proof the human requested it.
3. **Privacy-minimized projection:** HMAC of original Gmail ID uses a secret with at least 32 bytes; never expose the key or original IDs. An ephemeral per-run key is fine for this E0 pilot, but cannot provide stable cross-day deduplication; persistent stable secret custody would require separate security approval.
4. **Existing Need Graph:** only allow listed need IDs. An absent need creates `NEED_GRAPH_REVIEW`, not a silently created graph node. The existing `map_to_needs` and `route_candidate` apply to separately retrieved candidate resources, not to email instructions.
5. **External source verification:** an email-reported funding offer is not a confirmed amount, live deadline, award, applicant eligibility or submitted application. Compare with first-party canonical pages; retain discrepancies as `SOURCE_CONFLICT` and `HOLD_CONFLICT`. A `public_url` is citation data only: this module NEVER fetches a URL.
6. **Private Daily Digest:** read the projection and the original private mapping in private context. Show need, source age, canonical source, conflict, existing record ID, next human action and outcome unknown. No extra daily send.
7. **INTENT-OS:** only a proposed read-only needs/resource view. Do not claim a live INTENT-OS update, create a new mutable database, send emails, create calendar events, apply, pay, admit, merge, deploy or publish.

## Acceptance

- Fifteen local synthetic unit tests passed against the submitted bridge before PR creation; four synthetic tests cover actual Resource Miner Need Graph and routing integration, **exact-head CI execution pending**.
- One human-reviewed, bounded private dry-run screened 10 distinct Gmail messages: 10 candidate needs, 1 canonical need-graph gap, 1 explicit source conflict. Gmail message IDs and private claims are **not** committed. This is an observation of connected inbox evidence, not verified beneficiary return.
- Adversarial cases must fail: raw body, unsafe tracking links, duplicate event, source conflict, unknown need class, forged submission action, key omission, missing timezone.
- Follow-ups requiring separate approval: sustained private Gmail HMAC secret custody; automated read-only connector orchestration; new official source adapters; INTENT-OS UI projection; CI workflow control changes; any human action against external resources.

**Status:** PROPOSED / NO LIVE CONNECTOR IN CODE / AUTHORITY_EFFECT=NONE / ELIGIBILITY_UNASSESSED / BENEFIT_UNVERIFIED.
