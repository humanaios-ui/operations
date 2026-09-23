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
| `constants.json` | active resource constants carry `measurement_window_days`, “90 days”, “4 weeks of capacity”, and similar time predicates | `INVALID_INTERNAL_DEADLINE` where these trigger/revert control state from elapsed time | migrate resource/governance constant evaluation to observation-count / state-change predicates; preserve timestamps as evidence only |
| `priority_queue_engine.py` | impact/resource modes; no deadline term in queue score; readiness depends on blockers/pricing | ALIGNED | preserve; add temporal purity tests around work admission rather than a second scheduler |
| `CANDIDATE_BLOCK_TEMPLATE.md` | still uses scalar `estimated_effort_units`; optional bare `regulatory_deadline` timestamp | DRIFT | replace scalar cost with canonical `RESOURCE_UNITS.yaml` cost vector; replace bare timestamp with complete external regulatory constraint contract |
| `PRIORITY_QUEUE.md` | explicitly resource-impact ranked; regulatory exception policy | ALIGNED | strengthen as global gate; pin #378 |
| `BOOT_PROCESS_MAP.md` | removes 48h/window_end and uses resource depletion | ALIGNED | retain; verify no disguised timebox enters cycle semantics |
| `ZONE_REGISTRY.md` | resource caps per cycle; says no arbitrary window | ALIGNED / REVIEW | define cycle as allocation/accounting epoch, not day/week; capacity refills only by observed/allocation state, not calendar rollover |
| `document-registry.yaml` | review intervals (`30/90/180` days), seeded `review_due` dates, “overdue” state | `INVALID_INTERNAL_DEADLINE` | replace calendar review enforcement with event/evidence freshness predicates; review dates may remain historical/observational only |
| `.doc-control/review.py` | mechanically derives next `review_due` from days and can fail checks on time-based registry state | `INVALID_INTERNAL_DEADLINE` | redesign review gate around source drift / dependency change / explicit evidence invalidation; no merge failure solely because N days passed |
| `ui/intent-os-humanaios-v3_3.html` | generic `Deadlines — moves that die on a date`; project mechanism uses “date to check” / “date you'll know by” | `INVALID_INTERNAL_DEADLINE` | replace with `External Constraints`; replace date-driven gates with state/evidence predicates |
| `src/humanaios_operations/deadline_checker.py` | checks funding deadlines/opportunities | `REVIEW_REQUIRED` | distinguish external eligibility windows from regulatory authority; external commercial/funding windows may be context but do not become priority overrides |
| `PHASE2_SETUP.md` | daily deadline alert workflow | `REVIEW_REQUIRED` | distinguish informational external-window monitoring from internal work scheduling; remove agent urgency if not regulatory |
| `PHASE1_README.md` | “Timeline Fit” weighted into opportunity ranking | `INVALID_INTERNAL_DEADLINE` unless required by regulatory authority | replace with resource/eligibility/constraint fit; dates do not create priority by themselves |
| `.github/workflows/*` scheduled/cron jobs | clock-triggered automation may exist | `REVIEW_REQUIRED` | classify each scheduled job; technical maintenance may be `TECHNICAL_SAFETY`; internal work orchestration by clock is prohibited |
| historical dispatch/checklist records | dates and EOD deadlines in prior artifacts | `HISTORICAL_RECORD` where archival only | preserve as evidence; do not treat as active control surface |

## Second pass — molt and decision-routing surfaces (Q-MOLT-TEMPORAL-PURITY-01)

These were missed by the first pass because the active-control-surface list did
not include `MOLT_STATE.md`, and because the surfaces below are root `.md` files
rather than the `.json`/`.yaml` shapes `tests/test_temporal_dissolution_gate.py`
scans by suffix. The omission is itself a finding: a file that decides whether a
ratified constant change is kept or reverted is a control surface by any reading.

| Surface | Observed temporal behavior | Class | Required action |
|---|---|---|---|
| `MOLT_STATE.md` | `window_start` / `window_end` / `prediction.window_days`; falsifier tested "at window close"; `brier_actual` computed on a date; CI check `window_start < window_end < timestamp`; freeze rule phrased "within 48h" | `INVALID_INTERNAL_DEADLINE` — a molt verdict is a function of the calendar, a K=3 slot frees on a clock, and an unresolved molt past `window_end` is overdue work | migrate to closure-by-observation-set (`measurement_gate` with `min_resolved_observations`, `closes_on`, `invalidated_by`); retain `window_days` as `HISTORICAL_RECORD` normalization; detect stall as `MEASUREMENT_STARVED` across censuses, never as lateness. **Specified in MOLT_STATE.md § Measurement closure; PROPOSED, awaiting Z2 hash.** |
| `MOLT_STATE.md` (control-surface list) | absent from `TEMPORAL_DISSOLUTION_POLICY.md` active surfaces and from `CONTROL_EXACT` in the gate test | scope gap | add to both, so a future reintroduction of window semantics is refused mechanically rather than found by reading |
| `FRAMEWORK_MAPPING.md` | "Stop Condition = Window close date (molt_cycle.py runs auto-close)"; "measure at window close"; loop diagram routes `Z3 run → window close → VERDICT/revert` | `INVALID_INTERNAL_DEADLINE` (documentary) | not rewritten here: the file is an unratified candidate (Q-FRAMEWORK-MAPPING-01). Recorded so the migration lands in one Z2 decision rather than drifting further. Its loop stop-condition must become the `closes_on` predicate. |
| `z1-inbox/INDEX.yaml` | `decision_window_days: 2` | `INVALID_INTERNAL_DEADLINE` | the ratifier's attention is a measured resource (`RAT-min`), not a two-day clock. Replace with a resource/state readiness field, or reclassify explicitly as `OBSERVATIONAL` reporting metadata with no escalation attached |
| `.z1-control/validate.py` | emits, on every run today: `awaiting Z2 for 6d past the 2d window (due 2026-09-15) — CLAUDE.md routes this to Admiral re-read`, across 40 of 60 awaiting candidates | `INVALID_INTERNAL_DEADLINE` — **running**, not latent | a gate manufacturing an escalation path from elapsed time. Forty simultaneous escalations to one ratifier is indistinguishable from no signal. The true statement is a backpressure condition — 60 candidates outstanding against finite `RAT-min` — which should stop Z1 producing further governance work, the opposite of "escalate to Admiral". Replace the due-date warning with a queue-depth/`RAT-min` backpressure report |
| `CLAUDE.md` | "Decision window: 48h for routine decisions; 24h or less for urgent items"; Z1 contest rights expiring "within 48h"; "no decision in 48h" as an escalation trigger | `INVALID_INTERNAL_DEADLINE` | `BOOT_PROCESS_MAP.md` already publishes the successors ("Z2 ratifies when capacity permits", "re-propose when resource available"). `CLAUDE.md` is on the active-surface list and still carries the old reading — the two authority documents disagree |
| `molt_cycle.py` / `molt_ledger.py` | anti-cascade rule 1 phrased "no new candidate inside window W"; `molt_ledger.py` derives `window_close_at` as `now + 30 days` (marked `# Stub`) | `INVALID_INTERNAL_DEADLINE` | rule 1 re-reads as "while the prior molt on that constant is unclosed" with no loss of meaning. The 30-day stub must not become the default by being the only implementation |

### Pattern

Five of the six rows are the same defect: a measurement window doing scheduling
work. `RBE_TEMPORAL_MIGRATION_CANDIDATE.md` already fixed this shape once, for
`review_cadence_days` → `min_completed_censuses` + state invalidators. The molt
cycle is the second consumer of that substitution, not a new problem.

The reason it recurred after the fix was published is structural and is tracked
as `Q-INTENT-GRAPH-01`: `BOOT_PROCESS_MAP.md` published the successor reading for
molt windows and `MOLT_STATE.md` was never migrated, because nothing in the tree
recorded that those two files were about the same thing. The contradiction was
only findable by a human reading both and holding them in mind at once. It is now
an `O-MOLT-CYCLE ↔ O-TEMPORAL-GATE` row in `INTENT_GRAPH.yaml`, where
`tools/intent_graph_v1_0.py check` reports it on every run.

## RBE v0.1 temporal semantics requiring explicit review

### Rate periods

`RAT-min per week`, `CI-min per month`, `Z3-hr per week`, and similar units may remain as **observational rate normalization**. They must not mean “capacity automatically refills when the week/month changes.” Resource availability must be measured or explicitly allocated.

### `RUN-day`

`RUN-day` is a capital stock denominated in duration. It is not an internal due date. Resource depletion may halt work because the resource is gone; agents may not convert a low balance into calendar urgency that overrides the resource allocator.

### `review_cadence_days` / half-life / `STALE-day`

These are the highest-risk conflict with the new directive. If mere passage of N days automatically degrades authority, assurance, priority, or validity, the mechanism is an internal calendar control. The successor should prefer event/state freshness predicates (source changed, evidence invalidated, dependency moved, verification no longer reproducible). Because the registry is ratified, any change requires a versioned candidate and new Z2 ratification.

### PRICE event windows

A PRICE event may record the observation set/window over which a marginal rate was measured. That is measurement metadata. Calendar expiry alone must not automatically inject a new priority or rate; replacement requires new measured evidence and the governed PRICE path.

## Document-control finding

The current document-control subsystem is a direct example of the failure mode Q-TEMPORAL-DISSOLUTION-01 is intended to prevent: an internal document can become “overdue” and affect checks solely because a review interval elapsed. A provenance timestamp is useful; a calendar-generated obligation is not.

Candidate successor predicates include:

- canonical source hash changed since last review;
- cited dependency changed or disappeared;
- verification command no longer reproduces the recorded state;
- owner explicitly requests review because authority/scope changed;
- evidence source is superseded or invalidated.

These predicates create work from **state change**, not from a clock.

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
- degrade governance authority solely from age where an evidence/state predicate can be used instead;
- fail a merge solely because an internal review date elapsed.

## Next audit pass

Search and classify active occurrences of:

```text
deadline
due / overdue
review_due
review_interval_days
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
