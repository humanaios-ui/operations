# Candidate Block: Q-NF-ADAPTER-01 — molt_cycle.py + specimen_intake_evaluator.py onto the real NF ledger

**Z1 Proposer:** Claude (AI agent)
**Date Submitted:** 2026-09-13
**Pinned SHA:** `2a7db73` (main, after PR #305/#307/#308)
**Branch:** `claude/recursive-learning-self-improvement-lc8mjt`
**Queue row:** `Q-NF-SCHEMA-01` (`PRIORITY_QUEUE.md`, score 9, top of READY)
**Status:** AWAITING Z2 RATIFICATION

**Relationship to `Q-NF-SCHEMA-01` (the inbox candidate, `z1-inbox/2026-09-10/
Q-NF-SCHEMA-01-CANDIDATE.md`, filed 2026-09-10, still awaiting Z2):** that block
proposes the full v1.0 rewrite `NF_LEDGER_SCHEMA_v1.md` specifies — a single
flat record per molt, a genesis record, migration of the incumbent ledger. This
block instead implements `PRIORITY_QUEUE.md`'s own, narrower, more recent
(provenance 2026-09-09, fresh clone of main) acceptance criteria for the same
queue row, which are explicit that the incumbent v0.1 ledger is **not**
rewritten. The two are not in conflict — this block's four deliverables are a
strict subset of the 2026-09-10 block's "Technical Deliverables" #2 and #3 (CI
gate enhancement and a `molt_cycle.py` skeleton) — but they propose different
implementations of the same row, and only one should be ratified as *the*
closure of `Q-NF-SCHEMA-01`. Given a new, distinct q_id here rather than
reusing `Q-NF-SCHEMA-01` to avoid a duplicate-key collision in
`z1-inbox/INDEX.yaml` (`.z1-control/validate.py` rejects duplicate `q_id`s).
**Z2 should treat this as choosing between the two proposals for the same row,
not as two independent asks.**

---

## §A Position · Destination · Probability

**Position:** `PRIORITY_QUEUE.md`'s top-scored READY row said `molt_cycle.py` "counts
a row resolved only if `p` and `outcome` are on the same line → reads 0 resolved
from a ledger with 165 events." Verified directly before touching anything:
`python3 molt_cycle.py --read-only --nf ledgers/NF_LEDGER.jsonl` reported
`"nf_resolved": 0` against the real 165-event ledger. Root cause is more specific
than "same line" — `molt_cycle.py`'s `RESOLVE` indexing looked up `entry.get('target')`,
but `tools/nf_ledger_v0_1.py`'s actual `RESOLVE` events carry `token_id`, never
`target`; every resolution silently failed to index.

**Destination:** `molt_cycle.py` reads the ledger through `nf_ledger_v0_1.py`'s own
`project()`/`pin_outcome()` — the functions its `score` command already uses — so
the two tools agree by construction, not by parallel maintenance. A resolved
specimen-intake forecast is now visible to both.

**Probability:** **90%** this closes the row's own falsifier permanently (a
regression would require someone to re-introduce a parallel join instead of calling
`nf_ledger_v0_1.py`). Held below 100% because `tools/nf_ledger_cli_v1_0.py` /
`prs_run.py` (a fourth format, serving a different engine) is explicitly not
reconciled here — a future consumer could still add a fifth format.

---

## What was done

### 1 · `ledgers/NF_EVENT_SCHEMA.md` (new)

Documents the event format `tools/nf_ledger_v0_1.py` already implements and 165
real events already use — `OPEN`/`TOKEN`/`PIN`/`DATE`/`RESOLVE`/`STRIKE`, the hash
chain, and `pin_outcome()`'s four-way return (`1.0`/`0.0`/`None`/`"VOID"`). This is
the operative spec for this row's narrower scope; `NF_LEDGER_SCHEMA_v1.md` gets a
short cross-reference note (not a rewrite — that document is Z2-authority per
`CLAUDE.md`'s governance-files table) pointing here, since its own "Migration Path"
section already marks the full single-record redesign "Not in scope for
Q-NF-SCHEMA-01."

### 2 · `molt_cycle.py` rewired

`read_nf_ledger()` / `count_resolved()` / `join_pin_resolve_pairs()` now delegate to
`nf_ledger_v0_1.read()`/`project()`/`pin_outcome()` instead of a hand-rolled
`pins_by_target`/`resolves_by_target` join. `calculate_brier_scores()` and the CLI
surface (`--read-only --nf <path>`, `--complete`) are unchanged — same JSON shape,
verified byte-for-byte identical against the real ledger (`pin_targets: 75`,
`nf_resolved: 0`, unchanged — the real ledger has no `RESOLVE` rows yet, so this is
the correct output, not a regression).

### 3 · `specimen_intake_evaluator.py` gets a real sink

`_nf_write()` previously wrote only to an in-memory Python list, never persisted
anywhere. It now optionally (constructor param `nf_ledger_path`, default `None` —
existing callers and `test_specimen_intake_evaluator.py`'s 17 tests are unaffected)
also appends real `TOKEN`+`PIN` events at issue time and `RESOLVE` events at
`resolve_cycle` time, through `nf_ledger_v0_1.append()`, maintaining the hash chain.
`MoltPrediction.prediction_value` is already normalized to `[0,1]` by its own
docstring/design, so it maps onto `PIN.p` with no rescaling.

### 4 · Tests

`test_specimen_intake_nf_ledger.py` (root) and
`tools/tests/test_molt_cycle_nf_read.py` (10 tests total). The former is this row's
literal falsifier, run for real: publish a specimen-intake forecast, resolve it,
and check `nf_ledger_v0_1.py verify`/`score` and `molt_cycle.py`'s rewritten reader
all agree a resolved forecast with a Brier score is visible. The latter exercises
`pin_outcome()`'s three non-trivial outcome classes against `molt_cycle.py`
directly (resolved YES, resolved NO, still-unresolved, `PENDING_Z2_DATE`→VOID) so
future changes can't silently start conflating "no RESOLVE yet" with "VOID."

---

## Registrable item surfaced

**Two files are both named `molt_cycle.py`** — `/molt_cycle.py` (root) and
`/tools/molt_cycle.py` — with unrelated designs, CLIs, and ledger-row assumptions.
Every document that names `molt_cycle.py` as canonical (`NF_LEDGER_SCHEMA_v1.md`,
`Z3_DEPLOYMENT_CHECKLIST.md`'s `from molt_cycle import MoltCycle`,
`system_graph_generator.py`, and this row's own falsifier command) means the root
one; `tools/molt_cycle.py` (landed Phase 0, `e8a501f`) appears stranded from an
earlier design pass and is not referenced by name anywhere outside itself.

This is not just clutter — it is a live import hazard, reproduced while writing
this change's own tests: once `tools/` is added to `sys.path` (needed to reach
`nf_ledger_v0_1.py`), a bare `import molt_cycle` **silently resolves to the `tools/`
copy instead of root's**, with no error — it just has a different `MoltCycle`
class (in fact `tools/molt_cycle.py` has no `MoltCycle` class at all; the failure
mode is an `AttributeError`, not a wrong-but-plausible result, in that direction,
but a *different* consumer expecting `tools/molt_cycle.py`'s CLI would get root's
silently instead). Both new test files load the root module by explicit file path
(`importlib.util.spec_from_file_location`) rather than `import molt_cycle`, to
sidestep this rather than trip over it. **IC candidate**, not resolved here —
whether to delete, rename, or merge `tools/molt_cycle.py` is a separate decision
this row's scope doesn't cover.

---

## Falsifier

**Claim (this row's, from `PRIORITY_QUEUE.md`):** if after the adapter
`molt_cycle --read-only --nf ledgers/NF_LEDGER.jsonl` still reports `nf_resolved: 0`
against a ledger with ≥1 RESOLVE row, the adapter did not close the edge.

**Verified FALSE** (i.e. the row's fix holds): built a synthetic ledger with one
`TOKEN`+`PIN`+`RESOLVE` triple via `nf_ledger_v0_1.append()` directly —
`molt_cycle.py --read-only` reports `nf_resolved: 1`, `brier_overall: 0.09`,
matching `nf_ledger_v0_1.py score`'s own `Brier=0.090` for the same ledger exactly.
Also verified end to end through `specimen_intake_evaluator.py`: publishing and
resolving a real intake cycle with `nf_ledger_path` set produces a ledger where
both tools agree.

---

## Honest limitations, named

- `tools/nf_ledger_cli_v1_0.py` / `prs_run.py` (the fourth format) is untouched —
  it backs a different engine (the preregistered study runner) and its own module
  docstring already defers this reconciliation to this row; that deferral still
  stands after this change.
- The specimen-intake → `TOKEN`+`PIN`+`RESOLVE` mapping is a judgment call: a
  `MoltPrediction`'s `reverted` boolean becomes `RESOLVE.outcome = NO if reverted
  else YES`. This preserves the *direction* of the existing revert-rule semantics
  but is a coarser signal than the prediction's own continuous `brier_score` field
  (which is not written to the real ledger — `nf_ledger_v0_1.py`'s format has no
  slot for a predictor-supplied Brier, only a binary resolution it computes Brier
  from itself).
- `NF_LEDGER_SCHEMA_v1.md`'s heavier v1.0 shape (single record per molt, genesis
  record, embedded `anti_cascade_check`) is unaffected and remains open,
  forward-looking design, not implemented by this row.
- The real `ledgers/NF_LEDGER.jsonl` still has zero `RESOLVE` rows (the two owed
  resolutions — `T-empirica-outreach-01`, `T-grok-crossref-01` — are Z2's, per
  `ledgers/NF_LEDGER_README.md`'s "Owed by Z2" list, not this row's to do); this
  change is proven against synthetic and specimen-intake-generated ledgers, not
  against a resolution landing on the real mesh-pins ledger.

---

## Deliverables

| File | Change |
|---|---|
| `molt_cycle.py` | `read_nf_ledger`/`count_resolved`/`join_pin_resolve_pairs` delegate to `tools/nf_ledger_v0_1.py`'s `project()`/`pin_outcome()`; CLI/JSON output unchanged |
| `specimen_intake_evaluator.py` | `_nf_write()` gains a real, hash-chained sink via `nf_ledger_v0_1.append()`, opt-in via new `nf_ledger_path` constructor param (default `None`, no behavior change unless set) |
| `ledgers/NF_EVENT_SCHEMA.md` (new) | Documents the incumbent event format this row unifies on |
| `NF_LEDGER_SCHEMA_v1.md` | Cross-reference note only |
| `test_specimen_intake_nf_ledger.py` (new) | This row's falsifier, run for real, end to end |
| `tools/tests/test_molt_cycle_nf_read.py` (new) | Direct tests of `molt_cycle.py`'s rewritten reader against synthetic ledgers, all four `pin_outcome()` outcome classes |
| `z1-inbox/2026-09-13/Q-NF-ADAPTER-01.md` | This block |

No existing ledger file changed; `ledgers/NF_LEDGER.jsonl` hash chain verified
identical before and after (`nf_ledger_v0_1.py verify` — head unchanged). All 21
specimen-intake tests plus 10 new tests pass; `tools/repo_health.py --strict`
100/100; `.doc-control/validate.py` and `.tool-control/validate.py` both exit 0
(pre-existing advisory warnings only).

---

## Z2 Review Checklist

- [ ] **This block is accepted as `Q-NF-SCHEMA-01`'s closure instead of the
      2026-09-10 `Q-NF-SCHEMA-01` candidate's fuller rewrite** — the two propose
      different implementations of the same queue row; ratifying this one
      should also resolve (accept/reject/defer) the older one rather than
      leaving both open
- [ ] `ledgers/NF_EVENT_SCHEMA.md` is accepted as the operative spec for this row's
      scope (incumbent format, no rewrite of the 165 events on main)
- [ ] The specimen-intake `reverted → NO/YES` mapping is accepted as adequate for
      now, pending a real predictor-Brier field if that gap matters later
- [ ] The `tools/molt_cycle.py` duplicate is routed (delete, rename, or merge) —
      not decided here
- [ ] `tools/nf_ledger_cli_v1_0.py` / `prs_run.py` reconciliation remains open,
      unaffected by this row closing

---

## Summary

`molt_cycle.py` could not see any of its own telemetry before this change — the
row's own falsifier reproduced live against the real 165-event ledger. It now
reads through the same functions `nf_ledger_v0_1.py score` uses, `specimen_intake_evaluator.py`
gained a real (opt-in) sink instead of an in-memory-only one, and the fix is proven
against both a synthetic ledger and a real specimen-intake publish→resolve cycle.
One duplicate-file hazard was found and routed as a separate IC candidate rather
than fixed here.

**Ratification requested.**
