# TEMPORAL_CONTROL_AUDIT.md

**Gate:** Q-TEMPORAL-DISSOLUTION-01 / #378  
**Scope:** initial active-control-surface inventory; not exhaustive  
**Purpose:** distinguish legitimate clocks from internal calendar control while preserving the canonical RBE-OPS resource model

## Canonical RBE baseline

The repository already contains an implemented resource-economics stack:

- `docs/RESOURCE_BASED_ECONOMICS.md`
- `RESOURCE_UNITS.yaml` (ratified v0.1 unit SSOT)
- `ledgers/RESOURCE_LEDGER.jsonl`
- `tools/resource_ledger_v0_1.py`
- `tools/resource_census_v0_1.py`
- `priority_queue_engine.py`
- `test_resource_economics.py`

Q-TEMPORAL-DISSOLUTION-01 therefore does **not** create a parallel resource economy. It audits and removes hidden calendar authority from this existing architecture and from downstream control surfaces.

## Classification vocabulary

- `REGULATORY_EXTERNAL` — externally imposed regulatory/legal/compliance time constraint; requires complete evidence + Z2 ratification contract.
- `TECHNICAL_SAFETY` — technical timeout/backoff/lease/TTL/reclamation mechanism; no human-work priority authority.
- `OBSERVATIONAL` — timestamp/duration/measurement normalization for provenance or analysis; no scheduling authority.
- `HISTORICAL_RECORD` — archival record of an earlier deadline/date; no current scheduling authority.
- `INVALID_INTERNAL_DEADLINE` — internal due date/window/urgency/escalation/refill driven by elapsed time.
- `REVIEW_REQUIRED` — classification cannot be established from current evidence.

## Initial findings

| Surface | Observed temporal behavior | Initial class | Required action |
|---|---|---|---|
| `docs/RESOURCE_BASED_ECONOMICS.md` | correct non-commensurable resource allocation; some examples use calendar windows/cadences | ALIGNED + REVIEW | retain RBE allocation; ensure windows are measurement metadata, not scheduling authority |
| `RESOURCE_UNITS.yaml` | ratified SSOT; includes `period: week/month/day`, `review_cadence_days`, PRICE windows, `STALE-day`, half-life concepts | MIXED / REVIEW REQUIRED | versioned migration required where time passage changes capacity, validity, priority, assurance, or refill; do not silently rewrite ratified v0.1 |
| `priority_queue_engine.py` | impact/resource modes; no deadline term in queue score; readiness depends on blockers/pricing | ALIGNED | preserve; add temporal purity tests around work admission rather than a second scheduler |
| `CANDIDATE_BLOCK_TEMPLATE.md` | still uses scalar `estimated_effort_units`; optional bare `regulatory_deadline` timestamp | DRIFT | replace scalar cost with canonical `RESOURCE_UNITS.yaml` cost vector; replace bare timestamp with complete external regulatory constraint contract |
| `PRIORITY_QUEUE.md` | explicitly resource-impact ranked; regulatory exception policy | ALIGNED | strengthen as global gate; pin #378 |
| `BOOT_PROCESS_MAP.md` | removes 48h/window_end and uses resource depletion | ALIGNED | retain; verify no disguised timebox enters cycle semantics |
| `ZONE_REGISTRY.md` | resource caps per cycle; says no arbitrary window | ALIGNED / REVIEW | define cycle as allocation/accounting epoch, not day/week; capacity refills only by observed/allocation state, not calendar rollover |
| `ui/intent-os-humanaios-v3_3.html` | generic `Deadlines — moves that die on a date`; project mechanism uses “date to check” / “date you'll know by” | `INVALID_INTERNAL_DEADLINE` | replace with `External Constraints`; replace date-driven gates with state/evidence predicates |
| `src/humanaios_operations/deadline_checker.py` | checks funding deadlines/opportunities | `REVIEW_REQUIRED` | distinguish external eligibility windows from regulatory authority; external commercial/funding windows may be context but do not become priority overrides |
| `PHASE2_SETUP.md` | daily deadline alert workflow | `REVIEW_REQUIRED` | distinguish informational external-window monitoring from internal work scheduling; remove agent urgency if not regulatory |
| `PHASE1_README.md` | “Timeline Fit” weighted into opportunity ranking | `INVALID_INTERNAL_DEADLINE` unless required by regulatory authority | replace with resource/eligibility/constraint fit; dates do not create priority by themselves |
| `.github/workflows/*` scheduled/cron jobs | clock-triggered automation may exist | `REVIEW_REQUIRED` | classify each scheduled job; technical maintenance may be `TECHNICAL_SAFETY`; internal work orchestration by clock is prohibited |
| historical dispatch/checklist records | dates and EOD deadlines in prior artifacts | `HISTORICAL_RECORD` where archival only | preserve as evidence; do not treat as active control surface |

## RBE v0.1 temporal semantics requiring explicit review

### Rate periods

`RAT-min per week`, `CI-min per month`, `Z3-hr per week`, and similar units may remain as **observational rate normalization**. They must not mean “capacity automatically refills when the week/month changes.” Resource availability must be measured or explicitly allocated.

### `RUN-day`

`RUN-day` is a capital stock denominated in duration. It is not an internal due date. Resource depletion may halt work because the resource is gone; agents may not convert a low balance into calendar urgency that overrides the resource allocator.

### `review_cadence_days` / half-life / `STALE-day`

These are the highest-risk conflict with the new directive. If mere passage of N days automatically degrades authority, assurance, priority, or validity, the mechanism is an internal calendar control. The successor should prefer event/state freshness predicates (source changed, evidence invalidated, dependency moved, verification no longer reproducible). Because the registry is ratified, any change requires a versioned candidate and new Z2 ratification.

### PRICE event windows

A PRICE event may record the observation set/window over which a marginal rate was measured. That is measurement metadata. Calendar expiry alone must not automatically inject a new priority or rate; replacement requires new measured evidence and the governed PRICE path.

## Important distinction: external opportunity window vs regulatory deadline

An external grant/application/funding closing date is a real external constraint, but it is **not automatically a regulatory deadline** and therefore does not automatically override resource-based ordering.

It may be represented as contextual/eligibility data. Priority override remains restricted to validated `REGULATORY_EXTERNAL` constraints unless Z2 later ratifies another explicit exception class.

## Active remediation target

The gate is not complete while any active control surface can:

- make internal work urgent because a date approaches;
- mark work late/overdue solely from elapsed time;
- auto-escalate or expire internal work from a clock;
- replenish execution capacity solely at a calendar boundary;
- order work by arbitrary calendar window;
- define “cycle” as a hidden day/week/hour timebox;
- degrade governance authority solely from age where an evidence/state predicate can be used instead.

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
review_cadence_days
measurement_window_days
half_life_days
STALE-day
period: week/month/day
EOD / today / tomorrow
24h / 48h / N days
```

Every active occurrence must either be removed or carry a permitted temporal classification with evidence appropriate to that class.
