# CRM source-pinned baseline (Z1 candidate)

**Date:** 2026-10-28  
**Host:** `humanaios-ui/operations`  
**Frozen source commit:** `52aa7c0ed70f6e24ec050d0d56788a791e5f78f7`  
**Authority:** NONE. This is a review candidate, not a ratified operational registry.

## Purpose

This folder holds a **bounded public-safe snapshot** of claims in older collaborator records. Each record contains a stable CRM ID, a historical status and date, a separate **unverified current status**, and source links pinned to both the original repository commit and source-file blob SHA. Pins prove *which file was read*, not whether a claimed collaboration is still active. A source author and an independent reviewer must not be collapsed into the same witness.

No real names are inferred for Partner-B or Partner-V. No emails, telephone numbers, fees, unpublished partner details, private agreements, or private identity mappings belong here. The existing public registry may already expose personal contact information; editing the current file does not remove Git history. Address that issue separately through a human-authorized privacy review.

The snapshot is deliberately not the canonical live relationship state. Human-held approvals and the responsible private record remain controlling. The archived `humanaios-internal` repository is not assumed to be a writable store.

## Sources and limits

- `collaborators/README.md`: July 22 historical collaborator index; labels of 'Active' are not independently checked as of October 28.
- `collaborators/DEMARIUS_J_LAWSON.md`, `collaborators/DAVID_EMPIRICA.md`: named historical work and scope.
- `collaborator-ops/agreements/MODE_AI_PARTNERSHIP.md`: working research scope with MOU/IP/terms unresolved.
- `deliverables/collab-partner-b-brief.md`, `deliverables/collab-partner-v-pilot.md`: anonymized, time-bounded collaboration briefs; no authorization to disclose identity or execute pilots.
- `collaborators/LONGVIEW_FOUNDATION.md`: application claim, not verified funding.
- `tools/haios_collaboration_tracker_v3.jsx`: hardcoded prospects, not authenticated contact events.
- GitHub PR #909 is an external contribution to Resource Miner tests. It does not independently establish a signed agreement.

## Read-only commands

From the repository root:

```sh
python3 collaborator-ops/crm/crm_baseline.py collaborator-ops/crm/baseline-2026-10-28.json
python3 collaborator-ops/crm/crm_baseline.py collaborator-ops/crm/baseline-2026-10-28.json --verify-local-git --repo-root .
python3 tools/haios_collab_scanner_v1_0.py --sources github --crm-baseline collaborator-ops/crm/baseline-2026-10-28.json --output /tmp/haios-crm-review
python3 tools/haios_collab_scanner_v1_0.py --smoke-test
python3 -m unittest discover -s tests -p 'test_crm_baseline.py' -v
```

The scanner's GitHub/Gmail/Slack/arXiv/Supabase v1 adapters are currently **injected-input stubs**, not live authenticated searches. With no injected source rows, a scan must warn that nothing was checked. The baseline is a separate, static source-pinned snapshot, not a live scan.

## Human review gates

1. Independently inspect the pinned evidence (source revision, authorship and actual claims).
2. Confirm which current relationship states are true, and with which authority.
3. Verify private agreements and consent **outside the public repository**.
4. Record a new, signed or clearly human-attributed status event. Keep prior claims unchanged.
5. Only after human admission, allow a dashboard or INTENT-OS to display a verified active state.
6. External outreach, publication, contract, and compensation decisions each need separate human authorization.

**Falsifier:** If a pinned blob differs from the source at the pinned commit, if an old 'Active' status becomes 'currently active' without fresh proof, if an unverified prospect is labeled partner, or if a private identity is disclosed, the baseline fails and must not be promoted.

**Next smallest step:** Have Night inspect the seven records and approve or correct their *current* states. Do not create a new standalone repository or CRM database from this evidence.
