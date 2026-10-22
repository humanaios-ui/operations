# Q-EXTERNAL-ADVISORY-INTAKE-01 — Z1 Candidate (UNRATIFIED)

**Status:** `awaiting_ratification` — draft only. Not indexed, not entered in REGISTERED.md, not in PRIORITY_QUEUE.md.
**Author:** Z1 (Claude)
**Proposed:** 2026-10-22T10:44:14Z
**Source audit:** `z1-inbox/2026-10-22/` companion `Q-HOST-INVENTORY-01.md`; session report `php-exposure-audit-2026-10-22.md` (scratchpad, not in repo)

---

```yaml
candidate_id: "Q-EXTERNAL-ADVISORY-INTAKE-01"
title: "Finding: no intake or callout route for external vulnerability advisories (PHP2Shell passed unrecorded)"

description: |
  PHP2Shell (CVE-2026-109618 and CVE-2026-109619, CVSS v4.0 9.2 each; PHP notice 2026-10-20,
  fixed releases 2026-10-21; exploitation reported by third parties) has no record anywhere in
  the repository: no REGISTERED.md entry, no PRIORITY_QUEUE.md row, no z1-inbox item, no commit.
  - The repo contains no PHP, so the event was not applicable to repo-managed code. Nothing
    logged that either.
  - SECURITY.md is a disclosure intake for reports against this repo. It does not cover
    triage of external CVEs against the stacks the repo names.
  - The CLAUDE.md callout table (GAP, STALE, RECEIPT-GAP, GAUGE, AMBIGUITY, VOID, DRIFT,
    DISPUTED, MOLT, REVERT) has no trigger for an external advisory or active exploitation.
  - CLAUDE.md sets a 24h Admiral window for urgent items, but no trigger routes an external
    RCE into it.
  Result: a 9.2 CVSS RCE with reported exploitation produced zero governance trace.

author: "Z1 (Claude)"
proposed_at: "2026-10-22T10:44:14Z"

scope:
  - "CLAUDE.md (callout table, Decision Routing)"
  - "SECURITY.md (scope section, advisory intake pointer)"
  - "z1-inbox/ (advisory record format)"

resource_cost:
  cost:
    RAT-min: 15
    Z1-ktok: 3
    Z3-hr: 0
    CI-min: 0
  dependencies: ["CLAUDE.md", "SECURITY.md", "Q-HOST-INVENTORY-01"]
  blocking_on: []

impact_prediction:
  resource_impact: 6
  areas_affected:
    - "CLAUDE.md callout routing"
    - "Z2 urgent-decision path (24h window)"
    - "Every stack named in the host inventory"
  positive_outcomes:
    - "External advisories get a logged applicability decision, including 'not applicable'"
    - "Active exploitation routes to Z2 inside the 24h urgent window"
    - "A written record exists for later audit of response time"
  risk_factors:
    - "Alert fatigue if every upstream advisory triggers a callout"
    - "Z1 cannot patch live hosts; the trigger only routes the decision to Z2 and the owner"
    - "Adds a CLAUDE.md change, which is a Z2-ratified file"

proposed_change:
  - "Add callout EXTERNAL-ADVISORY: trigger = a published CVE or vendor advisory naming a runtime, framework, or provider in the host inventory, OR reported active exploitation of one. Route = Z2 (urgent, 24h). Z2 response = ratify applicability decision."
  - "Z1 writes one record per advisory in z1-inbox/<date>/ with: advisory IDs, sources, repo grep result, host-inventory result per entry (VERIFIED / UNVERIFIED-LIVE / NOT-APPLICABLE), and the owner action requested."
  - "A 'not applicable' finding must cite the check run. It may not be silent."
  - "SECURITY.md: one line pointing external-advisory reports at the same record format."

falsifier: |
  This candidate is FALSE if:
  - In the next 3 publicly reported exploited advisories naming a host-inventory stack, any
    of them has no Z1 record in z1-inbox/ within 24h of publication
  - OR a drill (a synthetic advisory injected into a test copy of the trigger text) does not
    produce a Z2 callout within the 24h urgent window
  - OR the new trigger fires on more than 5 advisories in a month that carry no exploitation
    report and no inventory match (alert fatigue, so the trigger is too broad)

evidence:
  - "git log --all -- '*.php' → 0 files; git grep for php2shell / CVE-2026-1096* across REGISTERED.md, PRIORITY_QUEUE.md, z1-inbox/, CLAUDE.md, SESSION_RITUALS.md → no matches"
  - "SECURITY.md lines 1–20 (reporting scope: this repo only)"
  - "CLAUDE.md 'Callout Mandatory Triggers' table (no external-advisory row)"
  - "CLAUDE.md 'Admiral' decision window: 24h or less for urgent items"
  - "Datadog PHP2Shell analysis (securitylabs.datadoghq.com) — facts as fetched 2026-10-22"

z2_decision:
  status: "awaiting_ratification"
  ratified_at: null
  ratification_hash: null
  z2_notes: ""

related_candidates: ["Q-HOST-INVENTORY-01"]
external_constraint:
  type: "EXTERNAL_ADVISORY"
  note: "Advisory timing is set by the upstream vendor, not by the ratification window. Included for routing only; not a regulatory deadline."
links:
  - name: "PHP2Shell analysis (Datadog)"
    url: "https://securitylabs.datadoghq.com/articles/php2shell-critical-vulnerabilities-in-php/"
  - name: "Companion candidate"
    url: "z1-inbox/2026-10-22/Q-HOST-INVENTORY-01.md"
```

---

## Notes for Z2

- Facts on CVE IDs, versions, and dates come from one fetched vendor-analysis article. Sources conflict on CISA's status (one search summary says not observed; another says exploitation confirmed). This draft does not depend on that conflict.
- The proposed change touches CLAUDE.md, a Z2-ratified file. It is a proposal only.
- Ratification does not authorize any change to live hosts.
