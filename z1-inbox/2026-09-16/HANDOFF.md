# Handoff — 2026-09-16 (Intent-OS test surface: harness, dashboard, pathway, repository index)

**Session:** `session_01CePrSjPSB8Epbpq3Lj8oKj` · **Branch:** `claude/vigilant-newton-ko9pcr` · **Pinned:** `main` at `7ff302d94fb0329266b7106860a04e0c089c61d8`
**Position at close:** board HOLDS (31 MATCH · 5 ABSENT-CONFIRMED · 7 UNCHECKED); harness RED on one pre-existing row (46 PASS · 1 FAIL of 47); 43 candidates in the queue, 39 awaiting Z2.

## Landed this session (main)

- #345 — board re-read at `0749022`; rev bumped to 2026-09-16; seals re-sealed; checker HOLDS.
- #346 — `REPOSITORY_STRUCTURE.md` v1 (from memory; six of its paths did not exist — found by the check written afterwards, fixed on this branch).

## On this branch (awaiting merge)

| file | what |
|---|---|
| `tools/intent_os_test_harness_v1_0.py` | 47 checks in tiers T0–T4; receipt with `git.tree_hash`; `--render`; `--self-test` (25 plants) |
| `ui/intent-os-test-dashboard-v1_0.html` | four panels rendered only from the embedded receipt |
| `docs/INTENT_OS_TEST_PATHWAY.md` | tiers, roles, session order, falsifiers, scale-out |
| `REPOSITORY_STRUCTURE.md` | rewritten from `ls`; every backticked path verified (160 claims, 0 missing) |
| receipt of the last run | embedded in the dashboard; the standalone `outputs/intent_os_test_results.json` is gitignored (d21) |
| `z1-inbox/2026-09-16/Q-INTENTOS-TEST-01.md` | asks d20 · d21 · d22 and registers F-CAND (ACAT tests) |
| `tools-manifest.yaml` · `TOOLS_MANIFEST.md` | harness registered (156 tools) |

## Findings scan

- **F-CAND (in Q-INTENTOS-TEST-01):** four `acat/tests` tests call write endpoints without the
  `X-ACAT-Write-Token` header the S-062726 gate requires → 503; no workflow runs that suite. Proposed
  patch is tests-only; not made here.
- **Observation:** `REPOSITORY_STRUCTURE.md` v1 was merged with six non-existent paths. The lesson is now a
  check (`t4-repo-index`) and a rule in the file's header.
- **Observation:** `mypy` in `quality-baseline.yml` depends on whether `requests` resolves with stubs on
  the runner; green on `main` (run 331), red on a machine with `requests` and no `types-requests`.

## Receipt walk-back (claim → tree)

| claim | where |
|---|---|
| relay answers a signed `/decide` → `/ratify` over a socket and `ratify.py --verify` accepts the result | `outputs/intent_os_test_results.json` → `t2-relay-roundtrip.tail` |
| a board tap survives reload in a browser | same → `t2-browser-persist.tail` |
| every backticked path in the index exists | same → `t4-repo-index.tail` (160 · 0 missing) |
| harness classifications fire on plants | `python3 tools/intent_os_test_harness_v1_0.py --self-test` |
| board HOLDS | `python3 tools/intent_os_board_check_v1_0.py` |

RECEIPT-GAP: none known. The receipt records `git.dirty: true` because it ran on the working tree before
its own commit existed; `git.tree_hash` (dashboard and `outputs/` excluded) is what a reader compares
after rerunning the harness on the commit that carries it.

## Next blockers

1. Z2: d20–d22 and F-CAND (this block); d2, d3, d5–d16 (fourteen board rulings, in the queue since 09-14).
2. Q-INTENTOS-LAUNCH-01 falsifier: a ruling lands through the relay by **2026-09-30**. The relay is proven
   in DRY_RUN over a socket; the live path needs Z2's machine, a scoped PAT, and an ngrok endpoint
   (runbook §4). `--tier T2` first.
3. Scale-out (pathway §5): next zone's `REPOSITORY_STRUCTURE.md` from `ls`, then its registry.

---

# Z2 queue — S-091626-01 (second session on this date)

**Session:** `session_01HUJaTTZR9XMuc4W2Vnz8ar` · **Branch:** `claude/molt-classifier-constitution-3720n1`
**Written:** 2026-09-16 21:33 UTC / 16:33 CDT (`bash_tool` verified per P22) · **Pinned:** `main` at `c558083`

Two sessions closed on 2026-09-16 and `z1-inbox/<date>/HANDOFF.md` is one file per date, so this is
appended under its own heading rather than merged into the Intent-OS handoff above. That handoff is
`session_01CePrSjPSB8Epbpq3Lj8oKj`'s and is left untouched.

*The one-file-per-date convention is documented in `GOVERNANCE_FILES.md:46`, `CLAUDE.md:238` (§B handoff
block) and `BOOT_PROCESS_MAP.md:63` — **not** in `SESSION_RITUALS.md` §B, which defines the close steps
and does not name the handoff surface at all. An earlier revision of this section attributed it to §B,
which would have turned an undocumented convention into a protocol rule by citation. What none of the
three say is what happens when two sessions close on one date: that is **unresolved convention, not a
rule**, and appending under a second heading is this session's choice, not an established practice.*

This section **records what is owed. It decides nothing** — every item below is a Z2 act.

## 1 · Unsigned, and `ratify.py` can sign them today

`ratify.py` 1.2.0 writes the index fields, the `records:` entry and the recomputed counts in one act, so
the manual steps the older output printed are gone. Two commands each, then `render.py` and `validate.py`.

| item | state |
|:--|:--|
| `Q-MOLT-LEDGER-SCAN-01` | `awaiting_z2`, `z2_hash: null` |
| `Q-INTENTOS-TEST-01` | `awaiting_z2`, `z2_hash: null` — d20 · d21 · d22 + F-CAND, from the session above |
| `Q-MERGE-SCOPE-01` | `awaiting_z2`, `z2_hash: null` — registered by #352; its 8-item checklist is live in `Z1_INBOX_INDEX.md` |

## 2 · Ruled in session, held pending signature

**Ruling 4 — `SESSION_RITUALS.md` Section F halt condition 1.** ACCEPT reading (a): F.1 stays general,
with an exception for sources declaring their own ratified halt rule. Replacement text is written out in
`z1-inbox/2026-09-16/Z2_RULINGS_2026-09-16.md`; **`SESSION_RITUALS.md` is untouched** while `z2_hash` is
null, per the `Z2-AMBIGUITY-BSM-D` precedent.

## 3 · Direction given, mechanism not specified

**Ruling 5 — due dates obsolete, ledger moving to resource-based.** This superseded the earlier
instruction to date 21 `PENDING_Z2_DATE` tokens; **no dating act was performed** and the 21 are untouched.
Four things unspecified, the first load-bearing:

1. **The pinned resolver *is* the date.** `ledgers/mesh_pins_090826.json` reads *"tree read of the named
   repo at date+3 (UTC); missing file = NO; final read 2026-10-04."* Removing dates with nothing in their
   place does not make the ledger resource-based — it makes all **58 tokens** unreadable.
2. What the replacement trigger is. `RESOURCE_UNITS.yaml` is not read by `tools/nf_ledger_v0_1.py`.
3. Prospective or retroactive for the **7 RESOLVE rows** already written (Brier `0.2075`). Append-only, so
   retroactive means `DISPUTE` events.
4. What `PENDING_Z2_DATE` exits to — its name is its exit condition.

Changing a ratified pin spec is a molt, Tier 1 minimum.

## 4 · Awaiting, not yet ruled

- **Ruling 6 — `ratify.py` 1.2.0 + `tools/tests/test_ratify_index_write.py`.** `AWAITING Z2`, and it
  **cannot be signed directly**: the rulings file is indexed under `records:`, and `cmd_ratify` resolves a
  `q_id` only from `candidates:`. Needs a new indexed candidate, or an explicit manual mechanism.
- **`Q-MERGE-SCOPE-01`'s eight decisions** — disposition for the scope gap, the four unscoped items,
  prevention (MS-2 now → MS-1-with-scope → MS-3), the IC registration, and whether it extends
  **H-GOV-01**'s `evidence_basis` as the sixth instance.
- **D1 / D2** from `ledgers/PRACTICE_RESOLUTION_MAP.md` — 16 AMBIGUOUS tokens (two candidate targets,
  different verdicts) and 6 UNRESOLVABLE (no target exists). **§B.7 is proposed, pending and unapplied**
  — `Q-MOLT-LEDGER-SCAN-01` carries a `B.7 — Ledger Resolution` step at its lines 259–272 and its
  checklist asks Z2 to accept, edit or reject it. An earlier revision of this section called it
  "unproposed", which was a stale claim from before the practice→repo mapping was written: the rule was
  that §B.7 should not be proposed *until* the mapping existed, the mapping now exists, and the proposal
  went into that block.
- **A fresh occurrence of `IC-050`.** The finding itself is already registered —
  `REGISTERED.md:3373`, *"IC-050 — Blocker Gate Not Enforced (sibling of IC-041)"* — so this is evidence
  extending a registered class, not a new one. An earlier revision said "flagged, not filed", which
  misstated the registry by implying the class was unregistered.

  The occurrence: on `b392739`, `Verify Z2 Ratification Requirements` was `completed / failure` and #348
  merged regardless, having dropped the `records:` entry for the rulings transcript. The gate ran,
  failed, and did not block. **Z2's to decide** whether this extends `IC-050`'s evidence basis; the
  register is append-only and the edit is not Z1's.

## 5 · Tree state at close

- `main` at `c558083`. **`Verify Z2 Ratification Requirements` is green again** — #352 carried the repair
  for the entry #348 dropped. **`audit` is still red on `main`** and has not been looked at.
- Queue: 45 candidates, 41 awaiting Z2, **21 past the 2-day window**; 26 records; no violations.
- Ledger: 58 TOKEN · 106 PIN · 7 RESOLVE · 21 still `PENDING_Z2_DATE`.
- Merged this session: **#343** (molt tier classifier), **#349** (CI suite guard + molt-tier gap
  consumer), **#352** (this candidate block). **#350** is the gap-row sink and has 1 row.

## 6 · Carry-forward for the next session

1. Nothing in §1–§4 is Z1's to settle. Do not infer a ruling from silence.
2. Force-push is **blocked by a repository ruleset** on `claude/molt-classifier-constitution-3720n1`.
   Restarting it after a merged PR needs a merge commit, not a rebase.
3. **Correction — there is no ≥30-PR threshold.** Earlier statements in this session, and the bodies of
   #343 and #349, said the molt-tier falsifier needs "≥30 PRs measured" before it can be evaluated. That
   number appears **nowhere**: not in `MOLT_STATE.md:202–211`, not in `molt-tier-check.yml`. The actual
   contract is `(PRs with measured − claimed > 1) / (total PRs)` over a rolling 30-day window, target
   < 5%, and the workflow's promotion note says only *"once the measured under-claim rate over a rolling
   30-day window is under 5%."* The threshold was invented and then repeated as if specified — an
   IC-031-class overstatement, recorded here rather than quietly dropped.

   What is true: the series has **1 row** (PR #349, on tracking issue #350). A rate over one sample is
   not a useful measurement, but "not yet useful" is a judgement, not a specified gate, and the
   distinction is exactly what the invented number obscured.
