---
doc_id: HAIOS-GOV-002
title: External Link Lifecycle Policy
revision: 1
status: approved
owner: "@humanaios-ui/operations"
approved_by: carly
approved_date: 2026-07-29
review_due: 2026-12-31
retention: permanent
---

# External Link Lifecycle Policy

**Approved 2026-07-29** as part of document control activation (A1).

## Policy

When document-control CI detects broken external links (via lychee):

| Scenario | Action | Timeline | Owner |
|----------|--------|----------|-------|
| **Link recently broken** (status 4xx/5xx) | Fix the broken link if the resource is still relevant; otherwise mark document as `superseded` (if the link's content was critical) or update to a working alternative | 1 business day | Document owner (CODEOWNERS) |
| **Link returns DNS/timeout (intermittent CDN/server)** | Retry lychee check; if persistent, file a GitHub issue on the linked resource's repo (if public) or mark for review | 3 days | Document owner |
| **Link still valid but marked as stale** (review_due approaching) | Review document for freshness. If stale, update or mark `superseded`. If still fresh, bump review_due in registry | 1 week before due date | Document owner |
| **Dead link but document is superseded** | Mark as acceptable (don't force a fix for documents already marked `superseded`). Only active approved documents must have live links. | (N/A) | — |

## How This Integrates

- **CI enforcement:** lychee flags broken external links as **warnings** (advisory, does not block merge) in Phase 2. Promotes to **errors** (blocking) in Phase 6 once the corpus is clean.
- **Drift monitor:** Biweekly scan catches accumulated link rot between merges. Issues are filed if novel drift is detected (first time it appeared since last scan).
- **Document review cycle:** review_due dates in the registry remind owners to validate that external links still point to relevant content.

## No silent link removal

External links are never silently deleted. If a link breaks:
1. Attempt repair (find working alternative, update)
2. If irreparable, document the reason in a git note or comment
3. Optionally mark the document itself for review if the broken link was critical

This preserves audit trail and prevents downstream consumers from being surprised by missing citations.
