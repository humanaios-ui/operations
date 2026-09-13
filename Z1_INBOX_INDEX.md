# Z1 Inbox — Conversion Index

Rendered from `z1-inbox/INDEX.yaml` (SSOT). **Do not hand-edit — edit the index** and run `python3 .z1-control/render.py`. CI runs `--check`, so the two cannot disagree.

A **candidate** asks Z2 for a decision. A **record** reports, receipts or hands off and asks for nothing. Z2's routine window is **2 days** from submission (CLAUDE.md); `decision_due` is derived from that, not hand-set. Signing is **Night** — `.z1-control/validate.py` refuses any other signature.

**14 candidates** — ⏳ awaiting Z2 11 · ✅ ratified 3 · **13 records**

## Awaiting Z2 (11)

Earliest due first. Anything dated before today is past the window — `.z1-control/validate.py` flags those on every run, and CLAUDE.md routes a closed window to Admiral re-read.

| decision due | candidate | what it asks | block |
|---|---|---|---|
| 2026-09-10 | **Q-ACAT-BENCHMARK-01** | ACAT ↔ market-benchmark map (H-BM-01..03) | `z1-inbox/2026-09-08/ACAT_BENCHMARK_CANDIDATE_BLOCK.md` |
| 2026-09-10 | **Q-DOC-LIFECYCLE-01** | docs/ lifecycle — disposition for 108 files | `z1-inbox/2026-09-08/DOC_LIFECYCLE_CANDIDATE_BLOCK.md` |
| 2026-09-12 | **Q-FRAMEWORK-MAPPING-01** ⚠️ falsifier waived | Framework Mapping — 5 AI engineering concepts → Z-roles | `z1-inbox/2026-09-10/FRAMEWORK_MAPPING_CANDIDATE.md` |
| 2026-09-12 | **Q-FRAMEWORK-MAPPING-INTEGRATION-01** | Framework Mapping governance integration across 31 repos | `z1-inbox/2026-09-10/FRAMEWORK_MAPPING_FOLLOWUP.md` |
| 2026-09-12 | **Q-NF-SCHEMA-01** | Unify NF_LEDGER schema | `z1-inbox/2026-09-10/Q-NF-SCHEMA-01-CANDIDATE.md` |
| 2026-09-13 | **Q-PHASE1-2-ROLLOUT-01** | Framework Mapping Phase 1–3 rollout plan | `z1-inbox/2026-09-11/PHASE_1_2_ROLLOUT_PLAN.md` |
| 2026-09-14 | **Q-ADVREVIEW-CALIB-01** | Adversarial review as a PR-gated calibration node | `z1-inbox/2026-09-12/Q-ADVREVIEW-CALIB-01.md` |
| 2026-09-15 | **Q-DOCREVIEW-01** | The 39 overdue document reviews — lifecycle, not re-dating | `z1-inbox/2026-09-13/Q-DOCREVIEW-01.md` |
| 2026-09-15 | **Q-GOVGATE-01** | The Z2 gate never ran; z1-inbox conversion mechanism | `z1-inbox/2026-09-13/Q-GOVGATE-01.md` |
| 2026-09-15 | **Q-TOOLCONTROL-01** | Tool manifest & document-control registry | `z1-inbox/2026-09-13/Q-TOOLCONTROL-01.md` |
| 2026-09-15 | **Q-TOOLCONTROL-02** | Tool category vocabulary & backlog clearance | `z1-inbox/2026-09-13/Q-TOOLCONTROL-02.md` |

## Decided (3)

| decision | candidate | signed by | on | ruling |
|---|---|---|---|---|
| ✅ ratified | **Q-CYCLE3-FALSIFY-01** | Night | 2026-09-08 | `z1-inbox/2026-09-08/Z2_RULINGS_2026-09-08.md`<br>`cycle-3-falsification-approved-20260908` |
| ✅ ratified | **Q-JESTER-CHECK-01** | Night | 2026-09-08 | `z1-inbox/2026-09-08/Z2_RULINGS_2026-09-08.md`<br>`h-cand-batch-ratified-20260908` |
| ✅ ratified | **Q-WITCH-CASCADE-01** | Night | 2026-09-08 | `z1-inbox/2026-09-08/Z2_RULINGS_2026-09-08.md`<br>`h-cand-batch-ratified-20260908` |

## ⚠️ Falsifier waivers (1) — open for Z2

A candidate with no falsifier. The waiver is the candidate's own claim that it predicts nothing, recorded so it cannot pass silently. Accepting or refusing it is Z2's act.

| candidate | stated reason |
|---|---|
| **Q-FRAMEWORK-MAPPING-01** | the block declares itself Type H, 'no falsifier required — reference architecture'. Recorded as the candidate's own claim, not as an accepted exemption: Z2 accepts or refuses it. |

## Records (13)

No decision requested. Listed so the coverage rule cannot be satisfied by silence.

| file | what it is |
|---|---|
| `z1-inbox/2026-09-06/HANDOFF.md` | Handoff — 2026-09-06 drop |
| `z1-inbox/2026-09-06/MANIFEST.md` | Manifest — 2026-09-06 drop (sets the inbox append-only convention) |
| `z1-inbox/2026-09-08/CYCLE_1_EXTERNAL_REVIEW.md` | Cycle 1 external review |
| `z1-inbox/2026-09-08/CYCLE_2_ADVERSARIAL_REPORT.md` | Cycle 2 adversarial report |
| `z1-inbox/2026-09-08/CYCLE_3_METADATA.md` | Cycle 3 metadata |
| `z1-inbox/2026-09-08/MERGE_RECEIPT_AND_CYCLE1.md` | Merge receipt 2026-09-08 (#217, #218 verified from origin/main) |
| `z1-inbox/2026-09-08/P_J4_BRIER_EXPLAINED.md` | P_J4 Brier score explainer |
| `z1-inbox/2026-09-08/REGISTRY_ENTRY_TEMPLATE.md` | Template — registry entry for H-CAND blocks |
| `z1-inbox/2026-09-08/Z2_RULINGS_2026-09-08.md` | Z2 rulings 2026-09-08 (three decisions, hashed) |
| `z1-inbox/2026-09-09/HANDOFF.md` | Handoff — 2026-09-09 |
| `z1-inbox/2026-09-09/IC-030-REPIN-01.md` | Q-IC030-REPIN-01 work order (Z1 self-assigned; no Z2 decision requested) |
| `z1-inbox/2026-09-10/HANDOFF.md` | Handoff — 2026-09-10 |
| `z1-inbox/2026-09-10/Q-IC030-REPIN-01-RESULT.md` | Q-IC030-REPIN-01 result — repin + manifest reconciliation (COMPLETE, 3/3) |

---

**Converting an inbox item to a Z2 decision:** add it to `z1-inbox/INDEX.yaml` under `candidates:` with `status: awaiting_z2` and a falsifier in the block itself, run `python3 .z1-control/render.py`, and commit both. An undecided candidate carries no signature fields at all.

Z2 records the decision by setting `status`, `ratified_by`, `ratified_at`, a `z2_ruling` that resolves to a file **indexed under `records:`**, and a `z2_hash` that **appears in that ruling**. All five are required: the validator refuses a signature from anyone outside `ratifiers:`, and refuses a hash the cited ruling does not carry.
