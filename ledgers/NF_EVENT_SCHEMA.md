# NF_EVENT_SCHEMA — the incumbent NF_LEDGER event format (v0.1, unified)

**Status:** DOCUMENTATION of an already-deployed format (Q-NF-SCHEMA-01)
**Implementation:** `tools/nf_ledger_v0_1.py` (canonical read/write/verify) —
unchanged by this document
**Relationship to `NF_LEDGER_SCHEMA_v1.md`:** that document specifies a heavier,
not-yet-built v1.0 record shape (single flat record per molt, genesis record,
embedded `anti_cascade_check`). This document instead describes the event-sourced
format `tools/nf_ledger_v0_1.py` already writes and 165 real events on
`ledgers/NF_LEDGER.jsonl` already use. `PRIORITY_QUEUE.md`'s `Q-NF-SCHEMA-01` row
(provenance: operated 2026-09-09, fresh clone of main) is explicit that the v0.1
ledger already on main is the incumbent and is **not rewritten** — this document is
the operative spec for that narrower scope. `NF_LEDGER_SCHEMA_v1.md`'s own "Migration
Path" section already marks the full single-record migration "Not in scope for
Q-NF-SCHEMA-01."

---

## Why this exists as a document now

Before this change, four tools each assumed a different shape for "the NF ledger":

1. `tools/nf_ledger_v0_1.py` — the real, event-sourced, hash-chained writer/reader
   below. In production use for the mesh-pins ledger (`ledgers/NF_LEDGER.jsonl`, 165
   events) and the CI-predict ledger (`ledgers/CI_PREDICT_LEDGER.jsonl`).
2. `molt_cycle.py` — read `RESOLVE` events by an `entry.get('target')` field, but
   `nf_ledger_v0_1.py`'s actual `RESOLVE` events carry `token_id`, never `target`.
   Every resolution silently failed to index: `molt_cycle.py --read-only --nf
   ledgers/NF_LEDGER.jsonl` reported `nf_resolved: 0` against a ledger with 165
   events, and would keep reporting 0 after every token in it resolved.
3. `specimen_intake_evaluator.py`'s `_nf_write()` wrote to an in-memory Python list,
   never persisted to any file, hash chain, or the other two tools at all.
4. `tools/nf_ledger_cli_v1_0.py` (backing `prs_run.py`) emits `entry_type` /
   `hypothesis_id` / `prediction_value` rows and explicitly refuses, in its own
   module docstring, to pick a canonical path or reconcile with the others —
   naming this row as the reason.

This document fixes (1) as the one real format; `molt_cycle.py` and
`specimen_intake_evaluator.py` are rewired in the same change to read/write it via
`tools/nf_ledger_v0_1.py`'s own functions rather than re-implementing the join.
`tools/nf_ledger_cli_v1_0.py` / `prs_run.py` reconciliation remains open — it backs a
different engine (the preregistered study runner) and is not touched here.

---

## Event types

Every line of `ledgers/NF_LEDGER.jsonl` (or any ledger built with this tool, e.g.
`ledgers/CI_PREDICT_LEDGER.jsonl`) is one JSON object, one of six `type`s:

### `OPEN`
Ledger-open marker. One per `build` invocation.

| field | meaning |
|---|---|
| `ledger` | ledger name, e.g. `"NF_LEDGER"` |
| `version` | `"v0.1"` |
| `window`, `source_plan`, `registered_sha`, `main_sha`, `resolver` | provenance of the plan the ledger was built from |

### `TOKEN`
A trackable claim: "this deliverable exists as a hashed file in the tree by this
date."

| field | meaning |
|---|---|
| `token_id` | stable id, referenced by `PIN.target` and `RESOLVE.token_id` |
| `practice` | owning practice/grouping id |
| `title` | human-readable description |
| `date` | the claimed delivery date |
| `date_source` | `"PRACTICE"` (self-dated, immediately scoreable) or Z1-proposed (pending Z2) |
| `state` | `"DATED"` if `date_source == "PRACTICE"`, else `"PENDING_Z2_DATE"` |
| `owner_add` | bool, provenance flag |

A token starting `PENDING_Z2_DATE` cannot be scored until a `DATE` event (below)
lands for it, signed by Z2.

### `PIN`
A forecast: predictor `p` states a probability `p` (must be in `[0,1]`, refused
otherwise — build/resolve time, RT-01 lesson) that a target resolves `YES`.

| field | meaning |
|---|---|
| `pin_id` | unique id for this forecast, conventionally `f"{target}:{predictor}"` |
| `target` | the `token_id` (or a practice-level id) this forecast is about |
| `predictor` | who made the forecast (`"Z1"`, `"Z2"`, or another named predictor) |
| `claim` | human-readable statement of what resolving `YES` means |
| `p` | float in `[0,1]`, or `null` if not yet entered (e.g. an owed Z2 prior) |
| `tokens` | (practice-level pins only) list of `token_id`s the practice pin aggregates |
| `scoreable` | whether every prerequisite for scoring is currently met |

A pin whose `target` names a single token resolves via that token's own
`RESOLVE`. A pin whose `tokens` names several resolves `YES` only if *every* one of
those tokens resolved `YES` (`pin_outcome()` below); if any is still
`PENDING_Z2_DATE` at scoring time, the pin is `VOID`, not scored.

### `DATE`
Z2 assigns a date to a Z1-proposed (`PENDING_Z2_DATE`) token, moving it to `DATED`
and making pins that target it scoreable.

| field | meaning |
|---|---|
| `token_id` | the token being dated |
| `date` | `YYYY-MM-DD` |
| `z2_hash` | Z2's ratification hash for this date |

Refused unless `--by Z2 --hash <hash>` is supplied — a date on a Z1-proposed token
is a Z2 act.

### `RESOLVE`
Records the observed outcome of a token, by tree read.

| field | meaning |
|---|---|
| `token_id` | the token being resolved |
| `outcome` | `"YES"` or `"NO"` |
| `source` | sha or path of the tree read that grounds this outcome — **required**, refused without it |

Refused if the token is still `PENDING_Z2_DATE` (cannot resolve an undated event) or
already `RESOLVED` (append a `DISPUTE` event instead, not implemented here).

### `STRIKE`
Marks a token as struck (withdrawn/void), excluding it from `pin_outcome()`'s
aggregation over a practice pin's tokens.

---

## State projection: `project(evs)`

`nf_ledger_v0_1.project()` folds the event stream into two dicts:

- `tokens[token_id]` → the token's current fields plus `resolved` (`None` until a
  `RESOLVE` lands, then `"YES"`/`"NO"`) and `state`.
- `pins[pin_id]` → the pin's fields as last written (pins are not mutated after
  creation in this schema).

## Outcome resolution: `pin_outcome(pin, tokens)`

Returns one of four values — **any consumer of this ledger must handle all four**,
not just the resolved case:

| return | meaning |
|---|---|
| `1.0` | every relevant token resolved `YES` |
| `0.0` | at least one relevant token resolved `NO` |
| `None` | still unresolved — some relevant token has no `RESOLVE` yet |
| `"VOID"` | a relevant token is still `PENDING_Z2_DATE`, or every relevant token was `STRUCK` (a pin's `tokens` list, if empty, falls back to `[target]` — it does **not** by itself make the pin `VOID`) |

A resolved pin (outcome `1.0` or `0.0`) with a non-null `p` is scoreable: its
squared error `(p - outcome)**2` contributes to that predictor's Brier score
(`cmd_score`). `None` and `"VOID"` pins are excluded from Brier — they are not
zero-scored, they are absent from the denominator.

---

## Hash chain

Each event, in append order, carries `prev_hash` (the previous event's `hash`, or
`"0"*64` for the first) and `hash = sha256(canon(event_without_hash_field))` where
`canon()` is `json.dumps(..., sort_keys=True, separators=(",", ":"))`. `verify()`
recomputes both the hash and the `prev_hash` link for every event and also checks
`seq` is strictly sequential; any edit, reorder, or gap breaks the chain. The ledger
is append-only: corrections are new events (a `DATE`, a later `RESOLVE`-equivalent),
never an edit to a prior line.

---

## What this unifies

| Consumer | Before | After |
|---|---|---|
| `molt_cycle.py` | Own `pins_by_target`/`resolves_by_target` join keyed on a `target` field `RESOLVE` events don't have; always 0 resolved | Delegates to `nf_ledger_v0_1.project()` + `pin_outcome()` |
| `specimen_intake_evaluator.py` | `_nf_write()` appended to an in-memory list only | Also appends real `TOKEN`+`PIN` (at issue) and `RESOLVE` (at resolution) events via `nf_ledger_v0_1.append()`, when constructed with an `nf_ledger_path` |

`tools/nf_ledger_cli_v1_0.py` / `prs_run.py` and the fuller `NF_LEDGER_SCHEMA_v1.md`
single-record design remain open reconciliation work, not addressed here.
