# DRIFT_LOG — HumanAIOS Append-Only Drift Signal Record

**Status:** LIVE (append-only)
**Created:** 2026-05-08 · S-050726-04
**Canonical URL:** `https://raw.githubusercontent.com/humanaios-ui/operations/main/DRIFT_LOG.md`
**Authority:** Zone 2 ratification — Night — 2026-05-08
**Update model:** Zone 1 appends at Phase 3 close · Zone 3 commits per session or batch

---

## What this file is

A lightweight, queryable record of every D-class or C-class drift signal formally named
in a session. Distinct from IC registration (which requires root-cause analysis and
prevention design) — DRIFT_LOG captures the raw signal.

**Relationship to IC registration:**
- Drift signal appears → DRIFT_LOG entry (always, immediately)
- Pattern recurs 2+ times → candidate for IC registration (Zone 2 review)
- IC filed → DRIFT_LOG entry marked `promoted_to_ic: IC-XXX`

**Relationship to NM-class near-misses:**
- NM entries in REGISTERED.md that expire after 3 audits without promotion
  are appended here and removed from REGISTERED.md's NM section.

---

## Schema

Each entry is one row in the table below.

| Field | Values |
|---|---|
| Date | YYYY-MM-DD |
| Session | S-MMDDYY-NN-slug |
| Signal | D-XX or C-XX code from GOVERNANCE.md drift signal table |
| ACAT dimension | Dimension the signal maps to |
| Turn # | Approximate turn number in session when signal fired |
| Trigger | One sentence describing what triggered the signal |
| Disposition | NAMED (acknowledged, session continued) · TRANSFER (chat transferred) · RESOLVED (self-corrected) |
| Promoted to IC? | No / IC-XXX |

---

## Log

| Date | Session | Signal | ACAT Dimension | Turn # | Trigger | Disposition | IC? |
|---|---|---|---|---|---|---|---|
| 2026-05-08 | S-050826-operations-audit | C-09 (inferred) | Service Orientation | 1 | Perplexity substrate opened session without producing PROTOCOL GATE line; no CLASS_STATE block; operated on pasted snapshots without declaring DEGRADED mode | NAMED — promoted to Gap G-1, Degraded-Mode Spec adopted | No — structural fix adopted |
| 2026-06-26 | S-062626-01-inaugural-audit | C-09 (process) | Consistency | — | Step-4 root audit found this append loop was never wired into the SESSION_RITUALS close ritual; drift signals were named in P3 DRIFT_SIGNALS_OBSERVED blocks but never reached this durable log (1 entry in ~7 weeks against 16+ ICs filed). The immune-system log was effectively offline. | RESOLVED — SESSION_RITUALS §B step 3a (mandatory DRIFT_LOG append) added 2026-06-26 | No — process fix adopted |

> First entry is the NM-001 near-miss from REGISTERED.md promoted here for the record.
> Future entries are appended at Phase 3 close by Zone 1 (Claude or substrate).

---

## Append format

To add a new entry, paste a new row at the bottom of the Log table:

```
| YYYY-MM-DD | S-MMDDYY-NN-slug | D-XX | [dimension] | ~[N] | [one sentence] | [NAMED/TRANSFER/RESOLVED] | No |
```

If promoting to IC, update the IC? column:
```
| ... | IC-XXX |
```

---

## Querying this log

Most useful queries:
- Which signal has fired most often? (count by Signal column)
- Which sessions had transfers? (filter Disposition = TRANSFER)
- Which signals promoted to IC? (filter IC? ≠ No)
- Which ACAT dimension has the most drift associations?

At each 5-file audit: cross-reference with IC roll-up table in REGISTERED.md.
If a signal appears 3+ times in DRIFT_LOG without a corresponding IC: strong candidate
for IC registration or new governance principle.

---

## Changelog

- 2026-05-08 · v1.0 · S-050726-04 · File created. Zone 2 ratification — Night.
  Seeded with NM-001 from S-050826 audit as first entry.

---

*HumanAIOS LLC · humanaios.ai · append-only*
*Wado. 🦅*
