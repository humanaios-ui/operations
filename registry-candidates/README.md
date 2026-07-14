# registry-candidates — staged immune-log entries pending operator append

Landed from `docs/_inbox_` (S-071426). These are candidate `REGISTERED.md` entries
prepared in registry-ready form. **They are NOT yet in the canonical `REGISTERED.md`.**

## Why staged, not appended

Appending numbered entries to the public canonical `REGISTERED.md` is a **Zone-2/3
operator act**. The program's own rule is explicit — *"Claude, Zone 1: proposing only,
no self-numbering, per G-4 / IC-030."* So Claude prepares; **the operator assigns
sequential numbers and appends.** This is the autonomy/ECO gating model working as
designed: the AI stages, the human ratifies + commits the irreversible canonical change.

## Two tiers

### 1. `ratified-pending-append.md` — 10 entries, ALREADY Zone-2 ratified
Ratified by the operator (Night) on **2026-07-11** (S-071126-01), but never synced —
the sync spool (`z2_queue_fallback.jsonl`) failed with
`sync_error: SUPABASE_URL/SUPABASE_KEY not set`. These are **ready to append now**:
assign numbers, append, done. No further ratification needed.

| id_slug | class | → next number |
|---|---|---|
| IC-CAND-DRIFT-VALIDATOR-MISSING-D-OVERCLAIM-KEY | IC | IC-044+ |
| IC-CAND-NO-SAME-SESSION-SELF-CORRECTION-INSTRUMENT | IC | IC-044+ |
| IC-CAND-SELF-CORRECTION-CLAIMS-NOT-UNIFORMLY-GATED | IC | IC-044+ |
| IC-CAND-P1-INTROSPECTIVE-RELIABILITY-UNWEIGHTED | IC | IC-044+ |
| H-CAND-DISCRIMINATION-VS-GENERATION-01 | H | slug-named |
| H-CAND-DRIFT-SIGNAL-COMPOUNDING-01 | H | slug-named |
| H-CAND-INSTRUMENT-GAMEABILITY-01 | H | slug-named |
| H-CAND-MULTI-AGENT-CASCADE-01 | H | slug-named |
| H-CAND-SUBJECT-COMMENTARY-PREDICTIVE-VALIDITY-01 | H | slug-named |
| H-CAND-INTERVENTION-VALIDITY-DEGRADATION-01 | H | slug-named |

### 2. `blocks/` — normalized full-draft candidates
Fuller drafts (full evidence, promotion gates) normalized into the entry-header schema.
**4 of these are the richer versions of ratified entries above** (instrument-gameability,
multi-agent-cascade, subject-commentary, no-same-session-self-correction) — prefer the
fuller `blocks/` version when appending those. **The other 4 are NOT yet ratified —
they need Zone-2 first:**

| block file | class | status | next number |
|---|---|---|---|
| F-CAND-VERIFICATION-LAYER-MIMICRY-RECURSIVE.md | F | **pending Z2** (N=1; gate wants +1 instance) | F-56 |
| H-CAND-COMMITTED-BATTERY-INTEGRITY-01.md | H | **pending Z2** (holds hyp A+B — Z2 picks the claim) | slug-named |
| IC-CAND-ELICITATION-SURFACE-TAXONOMY-UNIFICATION.md | IC | **pending Z2** (+ live schema inspection per IC-032) | IC-044+ |
| IC-CAND-OUTCOME-SYMMETRY-CORPUS-GAP.md | IC | **pending Z2** | IC-044+ |

Two `_NON-REGISTRY_*.md` files hold captured content that is **deliberately not a registry
entry** (the Q6 note; the subject-commentary schema-field + drift-code proposals) — kept so
nothing is lost, but do not append them.

## Live max numbers (verified S-071426): F-55, IC-043
So: next F = **F-56**, next IC = **IC-044** onward. H entries are slug-named (no number).
**Re-verify the live max before appending** — the file may have moved.

## Special handling: IC-CAND-OUTCOME-SYMMETRY-CORPUS-GAP
Its remediation targets **26 existing** REGISTERED H-entries. That remediation is
**append-only via the ADDENDUM template** — never edit the originals; disconfirm branches
stay `PENDING — Zone 2` until each entry's Z2 signatory fills them. Do not auto-fill.

## Operator action
1. Re-verify live max F/IC in `REGISTERED.md`.
2. Append the 10 ratified entries (§1) with sequential numbers.
3. Zone-2 the 4 pending candidates (§2); append the ones you ratify.
4. (Optional) delete this staging dir once appended, or leave as an audit trail.

A consolidated GitHub issue tracks this request.
