# Z2 Decision Ledger

**Append-Only Record of All Governance Decisions**

## Format
- **File:** `RATIFY_EVENTS.jsonl`
- **Structure:** One JSON object per line (JSONL)
- **Authority:** Admiral (Z2 / Night)
- **Last Updated:** 2026-10-22

## Schema

Each line is a JSON object with the following fields:

```json
{
  "event_id": "Q-{PROPOSAL-ID}",
  "timestamp": "ISO8601-timestamp",
  "actor": "Z2 (Night) or Z1 (Claude)",
  "decision": "ACCEPT|EDIT|REJECT|REMEDIATION",
  "scope": "High-level description of what was ratified",
  "detail": "Detailed explanation of the decision",
  "affected_file": "Primary file affected by this decision",
  "hash": "SHA256 hash or proposal ID",
  "status": "RATIFIED|MERGED|PENDING",
  "authority_violation": false
}
```

## Reading
Lines starting with `#` are skipped by readers (for future metadata).
Empty lines are ignored.

## Governance
All entries must be signed by Z2 (Night) before merge.
Changes to this ledger require Z2 ratification.
