# TEMPORAL_CONTROL_AUDIT.md

**Gate:** Q-TEMPORAL-DISSOLUTION-01 / #378  
**Scope:** initial active-control-surface inventory; not exhaustive  
**Purpose:** distinguish legitimate clocks from internal calendar control

## Classification vocabulary

- `REGULATORY_EXTERNAL` — externally imposed regulatory/legal/compliance time constraint; requires complete evidence + Z2 ratification contract.
- `TECHNICAL_SAFETY` — technical timeout/backoff/lease/TTL/reclamation mechanism; no human-work priority authority.
- `OBSERVATIONAL` — timestamp/duration for provenance/telemetry; no scheduling authority.
- `HISTORICAL_RECORD` — archival record of an earlier deadline/date; no current scheduling authority.
- `INVALID_INTERNAL_DEADLINE` — internal due date/window/urgency/escalation driven by elapsed time.
- `REVIEW_REQUIRED` — classification cannot be established from current evidence.

## Initial findings

| Surface | Observed temporal behavior | Initial class | Required action |
|---|---|---|---|
| `PRIORITY_QUEUE.md` | explicitly resource-impact ranked; regulatory exception policy | ALIGNED | strengthen as global gate; pin #378 |
| `BOOT_PROCESS_MAP.md` | removes 48h/window_end and uses resource depletion | ALIGNED | retain; verify no disguised timebox enters cycle semantics |
| `ZONE_REGISTRY.md` | resource caps per cycle; says no arbitrary window | ALIGNED / REVIEW | redefine cycle explicitly as allocation epoch, not day/week |
| `ui/intent-os-humanaios-v3_3.html` | generic `Deadlines — moves that die on a date`; project mechanism uses “date to check” / “date you'll know by” | `INVALID_INTERNAL_DEADLINE` | replace with `External Constraints`; replace date-driven gates with state/evidence predicates |
| `src/humanaios_operations/deadline_checker.py` | checks funding deadlines/opportunities | `REVIEW_REQUIRED` | determine whether source dates are external eligibility/regulatory windows or internal scheduling; external commercial/funding windows may be context but do not become regulatory priority overrides unless authority contract applies |
| `PHASE2_SETUP.md` | daily deadline alert workflow | `REVIEW_REQUIRED` | distinguish informational external-window monitoring from internal work scheduling; remove agent urgency if not regulatory |
| `PHASE1_README.md` | “Timeline Fit” weighted into opportunity ranking | `INVALID_INTERNAL_DEADLINE` unless externally mandated | replace with resource/eligibility/constraint fit; dates do not create priority by themselves |
| `.github/workflows/*` scheduled/cron jobs | clock-triggered automation may exist | `REVIEW_REQUIRED` | classify each scheduled job; technical maintenance may be `TECHNICAL_SAFETY`; internal work orchestration by clock is prohibited |
| historical dispatch/checklist records | dates and EOD deadlines in prior artifacts | `HISTORICAL_RECORD` where archival only | preserve as evidence; do not treat as active control surface |

## Important distinction: external opportunity window vs regulatory deadline

An external grant/application/funding closing date is a real external constraint, but it is **not automatically a regulatory deadline** and therefore does not automatically override resource-impact ordering.

It may be represented as contextual/eligibility data. Priority override remains restricted to validated `REGULATORY_EXTERNAL` constraints unless Z2 later establishes a separate explicitly governed class.

## Active remediation target

The gate is not complete while any active control surface can:

- make internal work urgent because a date approaches;
- mark work late/overdue solely from elapsed time;
- auto-escalate or expire internal work from a clock;
- order work by arbitrary calendar window;
- define “cycle” as a hidden day/week/hour timebox.

## Next audit pass

Search and classify active occurrences of:

```text
deadline
due / overdue
window_end
start_after
respond_within
complete_within
cron / schedule
EOD / today / tomorrow
24h / 48h / N days
```

Every active occurrence must either be removed or carry a permitted temporal classification with evidence appropriate to that class.
