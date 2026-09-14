# Z1 Inbox — Conversion Index

Rendered from `z1-inbox/INDEX.yaml` (SSOT). **Do not hand-edit — edit the index** and run `python3 .z1-control/render.py`. CI runs `--check`, so the two cannot disagree.

A **candidate** asks Z2 for a decision. A **record** reports, receipts or hands off and asks for nothing. Z2's routine window is **2 days** from submission (CLAUDE.md); `decision_due` is derived from that, not hand-set. Signing is **Night** — `.z1-control/validate.py` refuses any other signature.

**42 candidates** — ⏳ awaiting Z2 38 · ✅ ratified 4 · **21 records**

## Awaiting Z2 (38)

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
| 2026-09-15 | **Q-CGBG-BASELINE-01** | Adversarial review: CGBG-MARKET-BASELINE-001 (Evidence-Linked Market Observation v0.1) | `z1-inbox/2026-09-13/Q-CGBG-BASELINE-01.md` |
| 2026-09-15 | **Q-CGBG-PILOT-01** | Adversarial review: CGBG Pilot Offer (AI Research Capacity) | `z1-inbox/2026-09-13/Q-CGBG-PILOT-01.md` |
| 2026-09-15 | **Q-DOCREVIEW-01** | The 39 overdue document reviews — lifecycle, not re-dating | `z1-inbox/2026-09-13/Q-DOCREVIEW-01.md` |
| 2026-09-15 | **Q-DOCREVIEW-02** | Findings from the first real document review pass (11 reviewed, 28 unreachable) | `z1-inbox/2026-09-13/Q-DOCREVIEW-02.md` |
| 2026-09-15 | **Q-GOVGATE-01** | The Z2 gate never ran; z1-inbox conversion mechanism | `z1-inbox/2026-09-13/Q-GOVGATE-01.md` |
| 2026-09-15 | **Q-NF-ADAPTER-01** | molt_cycle.py + specimen_intake_evaluator.py onto the real NF ledger | `z1-inbox/2026-09-13/Q-NF-ADAPTER-01.md` |
| 2026-09-15 | **Q-RBE-01** | Resource-based operations v0.1 — units, ledger, census, priced queue | `z1-inbox/2026-09-13/Q-RBE-01.md` |
| 2026-09-15 | **Q-REGISTRY-AUDIT-01** | ZONE_REGISTRY.md reconciliation — classify 13 missing repos (planned, never created) | `z1-inbox/2026-09-13/Q-REGISTRY-AUDIT-01.md` |
| 2026-09-15 | **Q-REGISTRY-AUDIT-02** | ZONE_REGISTRY.md reconciliation — register 7 active repos missing from registry | `z1-inbox/2026-09-13/Q-REGISTRY-AUDIT-02.md` |
| 2026-09-15 | **Q-REGISTRY-AUDIT-03** | ZONE_REGISTRY.md reconciliation — implement + deploy CI gate | `z1-inbox/2026-09-13/Q-REGISTRY-AUDIT-03.md` |
| 2026-09-15 | **Q-RFM-01** | REGISTERED.md failure-mode map (RFM taxonomy) + executable scanner | `z1-inbox/2026-09-13/Q-RFM-01.md` |
| 2026-09-15 | **Q-TOOLCONTROL-01** | Tool manifest & document-control registry | `z1-inbox/2026-09-13/Q-TOOLCONTROL-01.md` |
| 2026-09-15 | **Q-TOOLCONTROL-02** | Tool category vocabulary & backlog clearance | `z1-inbox/2026-09-13/Q-TOOLCONTROL-02.md` |
| 2026-09-15 | **Q-TOOLCONTROL-03** | Turning the gate on itself — every blocking rule must be able to fail | `z1-inbox/2026-09-13/Q-TOOLCONTROL-03.md` |
| 2026-09-16 | **Q-BOARD-RULING-02** | Board ruling d2 — TLA_TOOLS_SHA256 — set the repository variable, or drop it as a gate? | `z1-inbox/2026-09-14/Q-BOARD-RULING-02.md` |
| 2026-09-16 | **Q-BOARD-RULING-03** | Board ruling d3 — z2_budget_p2 — set the Phase 2 envelope, or drop it as a gate? | `z1-inbox/2026-09-14/Q-BOARD-RULING-03.md` |
| 2026-09-16 | **Q-BOARD-RULING-05** | Board ruling d5 — GRBS ↔ Empirica — what is the formal relationship? | `z1-inbox/2026-09-14/Q-BOARD-RULING-05.md` |
| 2026-09-16 | **Q-BOARD-RULING-06** | Board ruling d6 — First job-posting batch — where does it come from? | `z1-inbox/2026-09-14/Q-BOARD-RULING-06.md` |
| 2026-09-16 | **Q-BOARD-RULING-07** | Board ruling d7 — Branch protection — turn off admin bypass on main, or keep it and register every bypass as an IC event? | `z1-inbox/2026-09-14/Q-BOARD-RULING-07.md` |
| 2026-09-16 | **Q-BOARD-RULING-08** | Board ruling d8 — c08f86c history — accept that the PII literals stay in history, or rewrite history? | `z1-inbox/2026-09-14/Q-BOARD-RULING-08.md` |
| 2026-09-16 | **Q-BOARD-RULING-09** | Board ruling d9 — B1 — is the platform contract id / feedback / task count covered by the contractor agreement? | `z1-inbox/2026-09-14/Q-BOARD-RULING-09.md` |
| 2026-09-16 | **Q-BOARD-RULING-10** | Board ruling d10 — Option B — ratify the six-pair co-run as a Molt candidate (4-week window, revert if ≥3 pairs r<0.3)? | `z1-inbox/2026-09-14/Q-BOARD-RULING-10.md` |
| 2026-09-16 | **Q-BOARD-RULING-11** | Board ruling d11 — Option A — file the 'orthogonal gap layer' positioning as DRAFT.md until Option B data exists? | `z1-inbox/2026-09-14/Q-BOARD-RULING-11.md` |
| 2026-09-16 | **Q-BOARD-RULING-12** | Board ruling d12 — H-CAL-01 — queue the mechanism study as a Molt candidate (8-week window) parallel to Option B? | `z1-inbox/2026-09-14/Q-BOARD-RULING-12.md` |
| 2026-09-16 | **Q-BOARD-RULING-13** | Board ruling d13 — Option C — require an evidence-tier tag on every public ACAT claim for the six unmapped dimensions? | `z1-inbox/2026-09-14/Q-BOARD-RULING-13.md` |
| 2026-09-16 | **Q-BOARD-RULING-14** | Board ruling d14 — LPCS — independent check (a), convergence specimen (b), destination (c), or none? | `z1-inbox/2026-09-14/Q-BOARD-RULING-14.md` |
| 2026-09-16 | **Q-BOARD-RULING-15** | Board ruling d15 — FALS-43 — batch ruling on the 43 hypotheses without written falsifiers? | `z1-inbox/2026-09-14/Q-BOARD-RULING-15.md` |
| 2026-09-16 | **Q-BOARD-RULING-16** | Board ruling d16 — docs/ triage — rule by hash over DOC_TRIAGE_2026-09-08.md: archive the 53 as listed, edit the list, or hold? | `z1-inbox/2026-09-14/Q-BOARD-RULING-16.md` |
| 2026-09-16 | **Q-BOOT-FINDINGS-SCAN-01** | Registry candidate block — post-merge findings scan over Q-BOOT-STATE-MACHINE-01, cross-walked against a live REGISTERED.md fetch | `z1-inbox/2026-09-14/Q-BOOT-FINDINGS-SCAN-01.md` |
| 2026-09-16 | **Q-BOOT-STATE-MACHINE-01** | Adversarial review of the boot state machine prototype — 17 findings mapped to the 12 ACAT dimensions, plus a corrected implementation | `z1-inbox/2026-09-14/Q-BOOT-STATE-MACHINE-01-ADVERSARIAL-REVIEW.md` |
| 2026-09-16 | **Q-IC-BOARD-SEALS-01** | IC candidate — the Intent-OS board's seals outlived the commits the 09-10 history reset removed (IC-030 class) | `z1-inbox/2026-09-14/IC-CAND-BOARD-STALE-SEALS.md` |

## Decided (4)

| decision | candidate | signed by | on | ruling |
|---|---|---|---|---|
| ✅ ratified | **Q-CYCLE3-FALSIFY-01** | Night | 2026-09-08 | `z1-inbox/2026-09-08/Z2_RULINGS_2026-09-08.md`<br>`cycle-3-falsification-approved-20260908` |
| ✅ ratified | **Q-JESTER-CHECK-01** | Night | 2026-09-08 | `z1-inbox/2026-09-08/Z2_RULINGS_2026-09-08.md`<br>`h-cand-batch-ratified-20260908` |
| ✅ ratified | **Q-WITCH-CASCADE-01** | Night | 2026-09-08 | `z1-inbox/2026-09-08/Z2_RULINGS_2026-09-08.md`<br>`h-cand-batch-ratified-20260908` |
| ✅ ratified | **Q-INTENTOS-LAUNCH-01** | Night | 2026-09-14 | `z1-inbox/2026-09-14/Z2_RULINGS_2026-09-14.md`<br>`9a2a469be2cbbe1d559b78d0b0fd41d286c21d0313bc61482b906b474f5d3309` |

## ⚠️ Falsifier waivers (1) — open for Z2

A candidate with no falsifier. The waiver is the candidate's own claim that it predicts nothing, recorded so it cannot pass silently. Accepting or refusing it is Z2's act.

| candidate | stated reason |
|---|---|
| **Q-FRAMEWORK-MAPPING-01** | the block declares itself Type H, 'no falsifier required — reference architecture'. Recorded as the candidate's own claim, not as an accepted exemption: Z2 accepts or refuses it. |

## Open questions for Z2 (90)

Every unticked item from the `## Z2 Review Checklist` of each candidate still awaiting a decision. Answer them in the block itself — ticking a box here does nothing, because this file is generated.

### Q-ADVREVIEW-CALIB-01 (8)

`z1-inbox/2026-09-12/Q-ADVREVIEW-CALIB-01.md`

- [ ] Falsifiers are testable; the humility one is correctly marked as needing a statistic first
- [ ] Stage 0 is accepted as blocking Stage 1, and the 14-day clock starts at **Stage 0 completion**, not ratification (owner residual #3)
- [ ] Stage 1 output is acknowledged as **declaration-level pure only** until a provenance check exists (owner residual #5)
- [ ] The self-referential limit is acknowledged in the ratification record: this is truth-gap reduction under pressure, not an independent measurement of the mechanism (owner residual #1)
- [ ] `quality-baseline.yml` coverage is confirmed at ratification time, including whether its output can be joined to a dimension without additional attribution logic (owner residual #4)
- [ ] Stage 3 is accepted as requiring a trusted-base evaluator and ratified attack corpus
- [ ] Registrable item 1 is routed with priority — it concerns the authority map's accuracy
- [ ] Out-of-scope boundary on `score_transcript()` is accepted

### Q-BOARD-RULING-02 (1)

`z1-inbox/2026-09-14/Q-BOARD-RULING-02.md`

- [ ] TLA_TOOLS_SHA256 — set the repository variable, or drop it as a gate? — options: set, drop gate, later

### Q-BOARD-RULING-03 (1)

`z1-inbox/2026-09-14/Q-BOARD-RULING-03.md`

- [ ] z2_budget_p2 — set the Phase 2 envelope, or drop it as a gate? — options: set, drop gate, later

### Q-BOARD-RULING-05 (1)

`z1-inbox/2026-09-14/Q-BOARD-RULING-05.md`

- [ ] GRBS ↔ Empirica — what is the formal relationship? — options: rule now, later

### Q-BOARD-RULING-06 (1)

`z1-inbox/2026-09-14/Q-BOARD-RULING-06.md`

- [ ] First job-posting batch — where does it come from? — options: own postings, partner, scrape, later

### Q-BOARD-RULING-07 (1)

`z1-inbox/2026-09-14/Q-BOARD-RULING-07.md`

- [ ] Branch protection — turn off admin bypass on main, or keep it and register every bypass as an IC event? — options: no bypass, bypass + IC, later

### Q-BOARD-RULING-08 (1)

`z1-inbox/2026-09-14/Q-BOARD-RULING-08.md`

- [ ] c08f86c history — accept that the PII literals stay in history, or rewrite history? — options: accept, rewrite, later

### Q-BOARD-RULING-09 (1)

`z1-inbox/2026-09-14/Q-BOARD-RULING-09.md`

- [ ] B1 — is the platform contract id / feedback / task count covered by the contractor agreement? — options: not covered, covered, later

### Q-BOARD-RULING-10 (1)

`z1-inbox/2026-09-14/Q-BOARD-RULING-10.md`

- [ ] Option B — ratify the six-pair co-run as a Molt candidate (4-week window, revert if ≥3 pairs r<0.3)? — options: ratify, edit, reject, later

### Q-BOARD-RULING-11 (1)

`z1-inbox/2026-09-14/Q-BOARD-RULING-11.md`

- [ ] Option A — file the 'orthogonal gap layer' positioning as DRAFT.md until Option B data exists? — options: file as draft, ratify now, later

### Q-BOARD-RULING-12 (1)

`z1-inbox/2026-09-14/Q-BOARD-RULING-12.md`

- [ ] H-CAL-01 — queue the mechanism study as a Molt candidate (8-week window) parallel to Option B? — options: queue, hold, reject

### Q-BOARD-RULING-13 (1)

`z1-inbox/2026-09-14/Q-BOARD-RULING-13.md`

- [ ] Option C — require an evidence-tier tag on every public ACAT claim for the six unmapped dimensions? — options: require, later

### Q-BOARD-RULING-14 (1)

`z1-inbox/2026-09-14/Q-BOARD-RULING-14.md`

- [ ] LPCS — independent check (a), convergence specimen (b), destination (c), or none? — options: (a) check, (b) specimen, (c) destination, none, later

### Q-BOARD-RULING-15 (1)

`z1-inbox/2026-09-14/Q-BOARD-RULING-15.md`

- [ ] FALS-43 — batch ruling on the 43 hypotheses without written falsifiers? — options: rule now, later

### Q-BOARD-RULING-16 (1)

`z1-inbox/2026-09-14/Q-BOARD-RULING-16.md`

- [ ] docs/ triage — rule by hash over DOC_TRIAGE_2026-09-08.md: archive the 53 as listed, edit the list, or hold? — options: archive as listed, edit list, later

### Q-CGBG-BASELINE-01 (6)

`z1-inbox/2026-09-13/Q-CGBG-BASELINE-01.md`

- [ ] Confirm or refute the filename/description mismatch flagged in finding 1 before any field tied to that evidence candidate is upgraded.
- [ ] Decide whether "NONE" and "PROHIBITED" should be added to §2's enumerated states, or the two matrix rows restated using the existing seven (finding 3).
- [ ] Decide whether "$X/project" should be downgraded to "reported figure, unit unverified" pending confirmation of what "project" denotes (finding 2).
- [ ] Decide whether the source engagement record should be captured/hashed/dated now, before it can be edited or removed (finding 4).
- [ ] Name (or explicitly decline to name) a third party who could ever move a claim to INDEPENDENTLY_CORROBORATED (finding 5).
- [ ] Decide whether the future Treatment exchange runs under the Pilot Offer as published or a revised version addressing `Q-CGBG-PILOT-01` (finding 6).

### Q-CGBG-PILOT-01 (8)

`z1-inbox/2026-09-13/Q-CGBG-PILOT-01.md`

- [ ] Set an actual expiration date/time for the offer (finding 1 — currently the field is broken).
- [ ] Decide a settlement floor and/or explicit Provider refusal right for inadequate reciprocal resources (finding 2).
- [ ] Decide delivery sequencing — who goes first, and what recourse exists if the counterparty doesn't reciprocate (finding 3).
- [ ] Define the "5 hours" unit and boundary behavior (finding 4).
- [ ] Add an explicit right to decline a task spec that's out of scope, infeasible, unlawful, or unsafe (finding 5).
- [ ] Decide whether to publish an acceptance-latency SLA (finding 6) — optional given this is a one-off pilot, not a recurring program.
- [ ] Decide whether evidence/verification should be strengthened from "where applicable" / "permitted" to a firmer commitment (finding 7).
- [ ] Findings 8–10 — acknowledge or explicitly accept as out of scope for a single-pilot experiment.

### Q-DOCREVIEW-01 (9)

`z1-inbox/2026-09-13/Q-DOCREVIEW-01.md`

- [ ] **Decision A — the backlog.** A1 pull queue / A2 retire first / A3 accept as-is. Z1 recommends **A2 then A1**. The staggered-schedule option is withdrawn: it invented an end date, which is the error this correction names.
- [ ] **Decision A3 specifically:** are the nine `HAIOS-COLLAB-*` point-in-time reports live documents or historical records? If records, `retired` is the truthful disposition.
- [ ] **Decision B — owners.** 0 of 46 assigned. A cadence with no assignee produces a queue nobody is late on.
- [ ] `review_policy: {draft: 30, review: 90, approved: 180}` — accept or set real intervals.
- [ ] Overdue stays **advisory** while derivation-mismatch becomes **blocking** — confirm that split is the intended one.
- [ ] `governance-triage.yml` cadence (Mondays 07:00 UTC) and the issue-per-queue shape.
- [ ] **Item 8:** `review_due` and "overdue" are deadline words for what is staleness. Renaming them touches 41 entries and a pre-existing tool — routed, not taken.
- [ ] The 5 documents with **no** `review_due` — leave them, or declare them off-cadence. Under a resource-based reading a missing date is not a defect: it simply means no staleness reference exists yet, which `--record` supplies on first review. They are outside `review_baseline:` for the same reason: there is no seeded date to freeze.
- [ ] `review_baseline:` is accepted as the frozen record of the seeded dates, and changing an entry is understood to be a ratified re-dating rather than an edit.

### Q-GOVGATE-01 (10)

`z1-inbox/2026-09-13/Q-GOVGATE-01.md`

- [ ] **Item 1 (priority): the Z2 gate has never run.** 122 zero-job runs. Every "CI enforces" claim in CLAUDE.md that routes through this workflow has been unenforced since 2026-09-10. Confirm the IC and whether other CI assurances need the same audit.
- [ ] **Item 2:** four further dead workflows, repairs not attempted here — direct Z3, or accept as a separate work item.
- [ ] **Item 3:** `Q-FRAMEWORK-MAPPING-01`'s self-declared falsifier exemption — accept the waiver, or require a falsifier before ratification.
- [ ] **Item 4:** the **5 candidates past the 48h window** (3d, 3d, 1d, 1d, 1d). CLAUDE.md routes a closed window to Admiral re-read.
- [ ] **Item 5:** the four Z1-assigned `q_id`s — accept or rename.
- [ ] **Item 6:** `IC-030-REPIN-01.md` filed as a record and `CYCLE_3_FALSIFICATION_REPORT.md` as a candidate — confirm both readings.
- [ ] `decision_window_days: 2` matches CLAUDE.md's 48h. Note CLAUDE.md says 48h while `seeds/INDEX.md` line 175 says **72h** for escalation — an **AMBIGUITY** callout, unresolved here, and the reason the window is a declared field rather than a constant in code.
- [ ] The coverage rule is accepted as merge-blocking from day one.
- [ ] `ratifiers: [Night]` is the correct and complete list — it is now pinned in `KNOWN_RATIFIERS` in `.z1-control/validate.py`, so changing it is a code review.
- [ ] **Item 7 (rank first): no path in this repo has a valid code owner.** Verified, not suspected — `@carly-r-anderson` and `@sab-backup` are not GitHub logins, and the repo has one collaborator. The #306 mitigation for this exact problem is itself inert. Every no-self-grant rule in the system — including this PR's — is advisory in practice until a Zone 3 fix lands. Decide: real logins as collaborators, or `@humanaios-ui` in the file.

### Q-IC-BOARD-SEALS-01 (3)

`z1-inbox/2026-09-14/IC-CAND-BOARD-STALE-SEALS.md`

- [ ] Register IC-BOARD-SEALS-01 in REGISTERED.md as an IC (class memory-vs-fetch), or fold it into IC-030 as a recurrence
- [ ] Accept, edit or reject prevention (1): an advisory `board-check` CI job on pushes to main touching sealed paths
- [ ] Accept, edit or reject prevention (2): the checker as a §A session-open line in CLAUDE.md

### Q-NF-ADAPTER-01 (5)

`z1-inbox/2026-09-13/Q-NF-ADAPTER-01.md`

- [ ] **This block is accepted as `Q-NF-SCHEMA-01`'s closure instead of the 2026-09-10 `Q-NF-SCHEMA-01` candidate's fuller rewrite** — the two propose different implementations of the same queue row; ratifying this one should also resolve (accept/reject/defer) the older one rather than leaving both open
- [ ] `ledgers/NF_EVENT_SCHEMA.md` is accepted as the operative spec for this row's scope (incumbent format, no rewrite of the 165 events on main)
- [ ] The specimen-intake `reverted → NO/YES` mapping is accepted as adequate for now, pending a real predictor-Brier field if that gap matters later
- [ ] The `tools/molt_cycle.py` duplicate is routed (delete, rename, or merge) — not decided here
- [ ] `tools/nf_ledger_cli_v1_0.py` / `prs_run.py` reconciliation remains open, unaffected by this row closing

### Q-NF-SCHEMA-01 (6)

`z1-inbox/2026-09-10/Q-NF-SCHEMA-01-CANDIDATE.md`

- [ ] Falsifier is testable and unambiguous
- [ ] Four incompatibilities actually resolved (review each mapping above)
- [ ] Hash chain prevents tampering (review CI gate spec in schema)
- [ ] Brier calculation is mathematically sound (review formula)
- [ ] Schema extends without breaking existing records (review migration path)
- [ ] Molt Cycle integration is viable (review pseudocode in schema)

### Q-TOOLCONTROL-01 (8)

`z1-inbox/2026-09-13/Q-TOOLCONTROL-01.md`

- [ ] Item 3 (root `CODEOWNERS` shadowed by `.github/CODEOWNERS`) is routed with priority — it means the doc-control ownership ratified earlier has never actually been enforced, and `CLAUDE.md` reproduces the inert excerpt
- [ ] Item 4: `message_calibration_v1_0.py` Zone 2 — ratify with a hash, or direct Z3 to correct the declaration to Zone 1
- [ ] Item 5: scope and data classification for `HAIOS-MCP-001` (rentahuman) and `HAIOS-MCP-002` (supabase, live project ref) — owner call, blocking their approval
- [ ] Item 6: 39 overdue document reviews — set new `review_due` dates or accept the backlog
- [ ] The coverage rule is accepted as merge-blocking from day one (the 30-day falsifier tests exactly whether that friction holds)
- [ ] The `--strict` promotion path is accepted as the mechanism for the 86 uncategorized tools, with no date committed yet
- [ ] Replacing the 2026-07-14 `TOOLS_MANIFEST.md` narrative with a generated index is accepted
- [ ] `builder_markers` is accepted as explicitly subordinate to `builder_compliance_scanner_v1.0.py`

### Q-TOOLCONTROL-02 (7)

`z1-inbox/2026-09-13/Q-TOOLCONTROL-02.md`

- [ ] The 16-term vocabulary is accepted, and `calibration_tool` is accepted as a distinct role rather than a subdivision of `diagnostic_tool`
- [ ] The ratchet principle is accepted as policy: a finding becomes blocking only at zero
- [ ] Normalizing six tools' `TOOL_CATEGORY` constants in source is accepted (behaviour unchanged)
- [ ] The `builder-lint` self-selected-corpus finding is routed — the `≥ 0.90` gate cannot see a tool that never declares itself
- [ ] Leaving 19 tools without Builder markers is accepted, rather than stub smoke tests
- [ ] Status and owner for 136 tools remain open owner work, deliberately untouched here
- [ ] Q-TOOLCONTROL-01's four items are still open and unaffected by this pass

### Q-TOOLCONTROL-03 (6)

`z1-inbox/2026-09-13/Q-TOOLCONTROL-03.md`

- [ ] The coverage requirement is accepted as blocking: a blocking rule without a demonstration fails CI
- [ ] Bringing `.tool-control/` and `.doc-control/` inside the registry is accepted
- [ ] The decision **not** to ship the filename-echo lint is accepted, on the measured 14/14 false-positive rate
- [ ] The `agent_self_only` finding is routed — a gate verified only by its author's own tests is not verified in this repo's own sense of the word
- [ ] Document-control's per-condition coverage is accepted as named follow-up, not silently owed
- [ ] The three open items from Q-TOOLCONTROL-01 (Zone 2 claim, MCP scope, overdue reviews) and the status/owner queue are unaffected by this pass

## Records (21)

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
| `z1-inbox/2026-09-13/HANDOFF.md` | Handoff — 2026-09-13 (registry audit Phase 0) |
| `z1-inbox/2026-09-13/MANIFEST.md` | Manifest — 2026-09-13 drop (registry audit) |
| `z1-inbox/2026-09-13/Z2_RULING_RESOURCE_UNITS_HEADER.md` | Z2 ruling — RESOURCE_UNITS.yaml header ratified; hash remains unsigned by Z2 |
| `z1-inbox/2026-09-13/Z2_RULING_ZONE2_RATIFY_TOOL.md` | Z2 ruling — .z1-control/ratify.py Zone 2 ratified (Night, 2026-09-13) |
| `z1-inbox/2026-09-14/HANDOFF.md` | Handoff — 2026-09-14 (Intent-OS board re-read, checker, relay fixes) |
| `z1-inbox/2026-09-14/Z2_RULINGS_2026-09-14.md` | Z2 rulings 2026-09-14 — signatures issued by .z1-control/ratify.py (Q-INTENTOS-LAUNCH-01 ACCEPT) |
| `z1-inbox/2026-09-14/Z2_RULING_INTENTOS_LAUNCH.md` | Z2 ruling — d17 local only · d18 z1-inbox + INDEX.yaml · d19 freeze path · temporary tokens revoked (Night, 2026-09-14) |
| `z1-inbox/2026-09-14/Z3-DEPLOYMENT-Q-FRAMEWORK-AUDIT-DEPLOY-01.md` | Z3 deployment log — Q-FRAMEWORK-AUDIT-DEPLOY-01 (12 repos, per-repo framework audit) |

---

**Converting an inbox item to a Z2 decision:** add it to `z1-inbox/INDEX.yaml` under `candidates:` with `status: awaiting_z2` and a falsifier in the block itself, run `python3 .z1-control/render.py`, and commit both. An undecided candidate carries no signature fields at all.

Z2 records the decision by setting `status`, `ratified_by`, `ratified_at`, a `z2_ruling` that resolves to a file **indexed under `records:`**, and a `z2_hash` that **appears in that ruling**. All five are required: the validator refuses a signature from anyone outside `ratifiers:`, and refuses a hash the cited ruling does not carry.
