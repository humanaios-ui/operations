# Z2 batch packet, batches 1-3 of the awaiting-Z2 queue (Z1 DRAFT, review only)

**Status:** Z1 proposal. `authority_effect = NONE`. Not a ratification, closure, label change or index edit. Only Night signs Z2 hashes (`python3 .z1-control/ratify.py <Q-ID> --decision ACCEPT|EDIT|REJECT --by Night --apply`).
**Pinned to:** `origin/main` at `cebb1846d923` (2026-11-12). Fetched fresh; the local clone is shallow, so PR merge facts below come from the GitHub API, not from local history.
**Scope:** the first three of eight proposed batches from the read-only queue triage requested in issue 1125 (queue snapshot: 100 awaiting in `z1-inbox/INDEX.yaml`, 100 past the 2-day window). Batches 4-8 are not in this packet.
**How to read it:** `[V]` = I read the primary record in this session; `[I]` = inferred from an INDEX note or title, candidate file not read. Where an earlier triage said `[V]` and I could not reproduce it, the row says so.

## Batch 1: records that may already be decided (confirm, then mark)
| q_id | What I checked | Result | Proposed action for Night |
|---|---|---|---|
| Q-PHASE-2-BOARD-MOLT-01 | `REGISTERED.md` lines 4978-4983 | [V] Ratification hash present: `decision=ACCEPT`, `by=Night`, `at=2026-09-19T22:38:15Z`, `commit=260e85a`. `INDEX.yaml` still says `awaiting_z2`. | Confirm the hash is yours and mark the index entry ratified. No new decision. |
| Q-INTENT-OS-WITNESS-LEDGER-01 | `REGISTERED.md` 4479-4546; `CLAUDE.md` appended events | [V] Hash present at line 4546 (`carly.r.anderson@gmail.com`, `2026-09-19T19:00:00Z`, `ACCEPT`), and `CLAUDE.md` records the ratification. BUT the entry header at line 4480-4500 still reads `status: CANDIDATE`, `zone2_ratification: null`, and `INDEX.yaml` says `awaiting_z2` (a later INDEX note, for a follow-up candidate, already calls it "already-ratified"). | Confirm, then bring the header and index in line. Records disagree with each other; that is the finding. |
| Q-RBE-01 | `REGISTERED.md` 3516; `INDEX.yaml` entry | NOT CLEAN. The line "Night - 2026-09-13 - Q-RBE-01 acceptance" is the `zone2_ratification` field of a DIFFERENT record (an IC about a global-count gate), not a hash on Q-RBE-01. The candidate asks four things: a hash on `RESOURCE_UNITS.yaml`, a capacity declaration, two constant molts, and a disposition of F-RBE-01/02/03. | Do not close on this evidence. Z1 will map each of the four asks to a ratified record or mark it open. (Resource units are ratified elsewhere, which suggests the first ask is met; unchecked.) |

## Batch 1b: umbrella and meta candidates (INDEX notes only) [I]
| q_id | Basis | Proposed action |
|---|---|---|
| Q-INTENTOS-REFRESH-01, Q-INTENTOS-BUS-01 | INDEX notes say they were decomposed into board rulings 23-26, 32 and 27-30; parent ratifies the mechanism only | Night decides whether the parents close once the children are ruled. Z1 will check each child exists as a candidate. |
| Q-TIER-ASSIGNMENT-BATCH-01, Q-Z3-EXECUTOR-ASSIGNMENT-BATCH-01, Q-RBE-OPS-TIER-RANKING-01 | Meta-batches over "90 candidates"; the count is now stale | Ask Z1 for a still-wanted note before retiring; do not retire on age alone. |
| Q-SYSTEM-GRAPH-TEMPORAL-01 | May overlap the 2026-11-11 graph-regeneration ruling (same loop-closing edges); unverified | Night or Z1 compares the two texts first. |

## Batch 2: Tier 0 documentation candidates [I]
Q-FRAMEWORK-MAPPING-01 (a falsifier waiver needs an explicit accept or refuse), Q-FRAMEWORK-MAPPING-INTEGRATION-01, Q-PHASE1-2-ROLLOUT-01, Q-588-CONVERGENCE-MATRIX-01, Q-PRINCIPLES-CROSSWALK-01 (its note says four locked tests come from an external review and are not in the repository, so ACCEPT or HOLD).
**Correction to the earlier triage:** it grouped Q-NF-SCHEMA-01 and Q-NF-ADAPTER-01 as an "ACCEPT pair". PR 313 says the opposite: Q-NF-ADAPTER-01 is a DISTINCT proposal for the same queue row as Q-NF-SCHEMA-01 (a fuller rewrite), and the PR asks Z2 to CHOOSE between them. That is a Night decision, not an accept pair.

## Batch 3: work already on main, record owed (confirm landing, then decide)
Merge state checked via the GitHub API this session:
| q_id | PR | Merge fact [V] | Note |
|---|---|---|---|
| Q-TOOLCONTROL-02 | 306 | merged 2026-09-13 | PR body asks for ratification of the categorization gate rule; also files one F candidate (builder-lint corpus self-selection). |
| Q-NF-ADAPTER-01 | 313 | merged 2026-09-13 | See the correction above: choose between it and Q-NF-SCHEMA-01. |
| Q-INTENTOS-LAUNCH-01 and the board seal checker (IC-BOARD-SEALS-01 candidate) | 323, 325 | both merged 2026-09-14 | 325 records d17-d19 and signs the launch ACCEPT via `ratify.py`; the seals-point-at-reset-commits IC was left "for Z2 to route". |
| Q-IC-RATIFY-BYPASS-01 | 409 | merged 2026-09-19 | Touches `.z1-control/ratify.py`, a Tier 2 gate path; the PR itself carries the registry entry and says a Tier 2 change needs an ADV run before KEEP. |
| Q-A11-ORDERING-INERT-01 | 446 | commit "Block ordering-bought corroboration weight in the convergence grader (#446)" is on main | Title matches; candidate text not read. |
| Q-TOOL-MANIFEST-DRIFT-PREVENTION-01 | 425 | a commit with #425 is on main, but its title is "Workflow dependency graph and evidence-based governance framework" | NOT confirmed to be the drift-prevention change. Z1 should read PR 425 before this row is relied on. |
| Q-TOOLCONTROL-01, Q-TOOLCONTROL-03, Q-P19-GATE-INERT-01, Q-GATE-PATHS-TEST-LOGIC-01 | not checked | - | INDEX notes only. -01 has an 8-item checklist including doc reviews (partial hold). |
"Accept after merge" records a decision that the landed change is the intended one; it is not a re-review. Tier 2 rows (409) deserve a read of the diff before signing.

## What Z1 will do next if Night wants it (nothing below happens without a go-ahead)
1. Read the candidate files behind Batch 1b, 2 and the unconfirmed Batch 3 rows and turn `[I]` into `[V]`.
2. Map Q-RBE-01's four asks to records.
3. Prepare Batch 4-8 packets the same way.

## Falsifier
If a row above marked `[V]` does not match the primary record at `cebb1846d923`, this packet is wrong for that row and should be corrected, not signed. If more than one `[V]` row fails, withdraw the packet.

## Not in this packet
Batches 4-8 (board rulings, escalations, holds, policy calls) and the dependabot, CI-batch and conflicted-PR triage; those are separate and need other evidence.
