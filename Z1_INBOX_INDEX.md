# Z1 Inbox — Conversion Index

Rendered from `z1-inbox/INDEX.yaml` (SSOT). **Do not hand-edit — edit the index** and run `python3 .z1-control/render.py`. CI runs `--check`, so the two cannot disagree.

A **candidate** asks Z2 for a decision. A **record** reports, receipts or hands off and asks for nothing. Z2's routine window is **2 days** from submission (CLAUDE.md); `decision_due` is derived from that, not hand-set. Signing is **Night** — `.z1-control/validate.py` refuses any other signature.

**91 candidates** — ⏳ awaiting Z2 82 · ✅ ratified 9 · **42 records**

## Awaiting Z2 (82)

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
| 2026-09-16 | **Q-BOARD-RULING-15** | Board ruling d15 — FALS-43 — batch ruling on the 43 hypotheses without written falsifiers? | `z1-inbox/2026-09-14/Q-BOARD-RULING-15.md` |
| 2026-09-16 | **Q-BOARD-RULING-16** | Board ruling d16 — docs/ triage — rule by hash over DOC_TRIAGE_2026-09-08.md: archive the 53 as listed, edit the list, or hold? | `z1-inbox/2026-09-14/Q-BOARD-RULING-16.md` |
| 2026-09-16 | **Q-BOOT-FINDINGS-SCAN-01** | Registry candidate block — post-merge findings scan over Q-BOOT-STATE-MACHINE-01, cross-walked against a live REGISTERED.md fetch | `z1-inbox/2026-09-14/Q-BOOT-FINDINGS-SCAN-01.md` |
| 2026-09-16 | **Q-BOOT-STATE-MACHINE-01** | Adversarial review of the boot state machine prototype — 17 findings mapped to the 12 ACAT dimensions, plus a corrected implementation | `z1-inbox/2026-09-14/Q-BOOT-STATE-MACHINE-01-ADVERSARIAL-REVIEW.md` |
| 2026-09-16 | **Q-IC-BOARD-SEALS-01** | IC candidate — the Intent-OS board's seals outlived the commits the 09-10 history reset removed (IC-030 class) | `z1-inbox/2026-09-14/IC-CAND-BOARD-STALE-SEALS.md` |
| 2026-09-19 | **Q-INTENTOS-BUS-01** | Agent bus policy — d27 model endpoint none/local/hosted · d28 issue mirror · d29 smoke contract in the manifest · d30 squash-merge read pointer | `z1-inbox/2026-09-17/Q-INTENTOS-BUS-01.md` |
| 2026-09-19 | **Q-INTENTOS-REFRESH-01** | Automated Intent-OS refresh — re-seal what a job may, file what a human must; d23 enable · d24 rev by job · d25 local copies · KNOWN_RED list | `z1-inbox/2026-09-17/Q-INTENTOS-REFRESH-01.md` |
| 2026-09-20 | **Q-BOARD-PUBLISH-01** | Board ruling d31 — board surface — serve the board from a login-gated Cloudflare Worker (Access, allow-listed identities), replacing d17's local-only? | `z1-inbox/2026-09-18/Q-BOARD-PUBLISH-01.md` |
| 2026-09-20 | **Q-IC-RATIFY-BYPASS-01** | IC candidate — a by-hand signature path (ratify.py --apply) stayed executable for board rulings after the merge-is-ratification ruling; guarded in #409 (a Tier 2 gate change) | `z1-inbox/2026-09-18/IC-CAND-RATIFY-MANUAL-BYPASS.md` |
| 2026-09-21 | **Q-BOARD-RULING-20** | Board ruling d20 — Test harness as §A step 3 | `z1-inbox/2026-09-19/Q-BOARD-RULING-20.md` |
| 2026-09-21 | **Q-BOARD-RULING-21** | Board ruling d21 — Dashboard: commit the rendered receipt | `z1-inbox/2026-09-19/Q-BOARD-RULING-21.md` |
| 2026-09-21 | **Q-BOARD-RULING-22** | Board ruling d22 — Scale-out order for the test surface | `z1-inbox/2026-09-19/Q-BOARD-RULING-22.md` |
| 2026-09-21 | **Q-BOARD-RULING-23** | Board ruling d23 — Refresh job: enable the PR/issue half | `z1-inbox/2026-09-19/Q-BOARD-RULING-23.md` |
| 2026-09-21 | **Q-BOARD-RULING-24** | Board ruling d24 — May a job advance the board's rev? | `z1-inbox/2026-09-19/Q-BOARD-RULING-24.md` |
| 2026-09-21 | **Q-BOARD-RULING-25** | Board ruling d25 — Local copies: re-download or a release asset | `z1-inbox/2026-09-19/Q-BOARD-RULING-25.md` |
| 2026-09-21 | **Q-BOARD-RULING-26** | Board ruling d26 — Resource-based grounding of the refresh job | `z1-inbox/2026-09-19/Q-BOARD-RULING-26.md` |
| 2026-09-21 | **Q-BOARD-RULING-27** | Board ruling d27 — Model endpoint policy for the bus | `z1-inbox/2026-09-19/Q-BOARD-RULING-27.md` |
| 2026-09-21 | **Q-BOARD-RULING-28** | Board ruling d28 — Issue mirror for REQ- records | `z1-inbox/2026-09-19/Q-BOARD-RULING-28.md` |
| 2026-09-21 | **Q-BOARD-RULING-29** | Board ruling d29 — The smoke contract in the manifest | `z1-inbox/2026-09-19/Q-BOARD-RULING-29.md` |
| 2026-09-21 | **Q-BOARD-RULING-30** | Board ruling d30 — Squash-merge read pointer | `z1-inbox/2026-09-19/Q-BOARD-RULING-30.md` |
| 2026-09-21 | **Q-BOARD-RULING-32** | Board ruling d32 — KNOWN_RED list in the refresh job | `z1-inbox/2026-09-19/Q-BOARD-RULING-32.md` |
| 2026-09-21 | **Q-BOARD-RULING-33** | Board ruling d33 — board filename: rename to intent-os-board.html with a redirect from the old path (successor to d19's freeze), keep the frozen path, or later | `z1-inbox/2026-09-19/Q-BOARD-RULING-33.md` |
| 2026-09-21 | **Q-INTENT-OS-WITNESS-LEDGER-01** | Intent-OS witness ledger — human-machine decision attribution ledger | `z1-inbox/2026-09-19/Q-INTENT-OS-WITNESS-LEDGER-01.md` |
| 2026-09-21 | **Q-INTENTOS-PAGES-GATE-01** | Gates for the board's page set — intent_os_pages --check as a pre-merge step (G1), the d33 rename-hold test pre-merge (G2), the runbook card sealed or not (G3): a Tier 2 proposal | `z1-inbox/2026-09-19/Q-INTENTOS-PAGES-GATE-01.md` |
| 2026-09-21 | **Q-PHASE-2-BOARD-MOLT-01** | Z2 Board Decisions & Molt Events Ingestion | `z1-inbox/2026-09-19/Q-PHASE-2-BOARD-MOLT-01.md` |
| 2026-09-21 | **Q-RESEARCH-OPS-LOOP-AND-AUDITOR-01** | Research→Governance→Operations Loop + Automated Repository Auditor — three tools: research_to_candidates.py, apply_findings.py, repository_auditor.py (Tier 2 molt) | `z1-inbox/2026-09-19/Q-RESEARCH-OPS-LOOP-AND-AUDITOR-01.md` |
| 2026-09-22 | **Q-TOOL-MANIFEST-DRIFT-PREVENTION-01** | Tool manifest drift prevention — validation gate (Tier 0 infrastructure) | `z1-inbox/2026-09-20/Q-TOOL-MANIFEST-DRIFT-PREVENTION-01.md` |
| 2026-09-23 | **Q-AGENT-CHECKIN-CALIBRATION-01** | Calibration at check-in (H-ACAT gap) + Copilot/Claude graph and review comparison | `z1-inbox/2026-09-21/Q-AGENT-CHECKIN-CALIBRATION-01.md` |
| 2026-09-23 | **Q-CORPUS-STATS-RECONCILE-01** | July corpus audit still unresolved — SEED.md publishes figures the audit found unreproducible | `z1-inbox/2026-09-21/Q-CORPUS-STATS-RECONCILE-01.md` |
| 2026-09-23 | **Q-DATA-SSOT-REGENERATION-01** | Regenerate the data SSOT — contaminated v0.1 corpus retained as lesson artifact, not corrected figures | `z1-inbox/2026-09-21/Q-DATA-SSOT-REGENERATION-01.md` |
| 2026-09-23 | **Q-DEFERRAL-RULE-01** | A deferral needs an ending condition, not just a better home | `z1-inbox/2026-09-21/Q-DEFERRAL-RULE-01.md` |
| 2026-09-23 | **Q-EXTERNAL-JESTER-01** | The ratified Jester's independence rule is the wrong rule, and we can now measure that | `z1-inbox/2026-09-21/Q-EXTERNAL-JESTER-01.md` |
| 2026-09-23 | **Q-GATE-PATHS-TEST-LOGIC-01** | A gate's logic measures Tier 0 while its workflow wrapper measures Tier 2 | `z1-inbox/2026-09-21/Q-GATE-PATHS-TEST-LOGIC-01.md` |
| 2026-09-23 | **Q-GOVDRIFT-01** | Derived-artifact convention, and four items only Z2 can close | `z1-inbox/2026-09-21/Q-GOVDRIFT-01.md` |
| 2026-09-23 | **Q-GRAPH-CONVERGENCE-01** | Grade agreement between agent-authored graphs by source disjointness, not similarity | `z1-inbox/2026-09-21/Q-GRAPH-CONVERGENCE-01.md` |
| 2026-09-23 | **Q-INTENT-GRAPH-01** | Shared intent substrate — typed graph for vision/mission/principles/objectives with a conflict validator | `z1-inbox/2026-09-21/Q-INTENT-GRAPH-01.md` |
| 2026-09-23 | **Q-MOLT-TEMPORAL-PURITY-01** | Molt closure is a state predicate, not a clock — MOLT_STATE.md window semantics vs Q-TEMPORAL-DISSOLUTION-01 | `z1-inbox/2026-09-21/Q-MOLT-TEMPORAL-PURITY-01.md` |
| 2026-09-23 | **Q-SEED-TRL-PROPAGATION-01** | Ratified TRL correction never reached SEED.md — identity anchor still states TRL 2–3 | `z1-inbox/2026-09-21/Q-SEED-TRL-PROPAGATION-01.md` |
| 2026-09-23 | **Q-SMAG-CALIBRATION-SCHEMA-CONFORMANCE-01** | Calibration profile data violates WITNESS_STATE_V0_1 schema contract | `z1-inbox/2026-09-21/Q-SMAG-CALIBRATION-SCHEMA-CONFORMANCE-01.md` |
| 2026-09-23 | **Q-SMAG-Z3-TASK-SEQUENCING-01** | Z3 executor task sequencing and dependency graph undefined for s1/s2/s3 | `z1-inbox/2026-09-21/Q-SMAG-Z3-TASK-SEQUENCING-01.md` |
| 2026-09-24 | **Q-A11-ORDERING-INERT-01** | A11 still enforces a property no grade depends on | `z1-inbox/2026-09-22/Q-A11-ORDERING-INERT-01.md` |
| 2026-09-24 | **Q-ACCOUNT-HUB-01** | HumanAIOS Account Hub & Project Manager Cockpit | `z1-inbox/2026-09-22/ACCOUNT-HUB-PROPOSAL.md` |
| 2026-09-24 | **Q-MESH-LOCAL-COORDINATION-01** | Local mesh coordination layer in operations/mesh/ for humanaios, website, grok-crossref | `z1-inbox/2026-09-22/Q-MESH-LOCAL-COORDINATION-01.md` |
| 2026-09-24 | **Q-P19-GATE-INERT-01** | The principle-compliance gate reported green without opening a file | `z1-inbox/2026-09-22/Q-P19-GATE-INERT-01.md` |
| 2026-09-24 | **Q-REFERENT-DECAY-01** | Five artifacts whose link to their referent died while the artifact stayed alive | `z1-inbox/2026-09-22/Q-REFERENT-DECAY-01.md` |
| 2026-09-24 | **Q-Z2-BLOCK-UNFILLABLE-01** | The candidate template promises z2_decision is auto-filled; nothing fills it, and the signature makes filling it later impossible | `z1-inbox/2026-09-22/Q-Z2-BLOCK-UNFILLABLE-01.md` |
| 2026-09-25 | **Q-BUZZ-COLLAB-EVAL-01** | Buzz as HumanAIOS Coordination Layer — Phase 0 evaluation (Z1/Z2/Z3 governance on self-hosted Nostr relay) | `z1-inbox/2026-09-23/Q-BUZZ-COLLAB-EVAL-01.md` |
| 2026-09-25 | **Q-Z2RATIF-MECH-32** | Z2 Ratification Mechanism Undocumented — governance workflow clarity gap | `z1-inbox/2026-09-23/IC-032-Z2-RATIFICATION-MECHANISM.md` |
| 2026-09-25 | **Q-SA-WINDOW-DESIGN-E-PLUS-A-01** ⚠️ falsifier waived | Falsifiable Self-Assessment Window — Design E + A | `z1-inbox/2026-09-23/falsifiable_self_assessment.md` |
| 2026-09-25 | **Q-Z2-PHASE-2A-INTERROGATION-COMPLETE-01** ⚠️ falsifier waived | Phase 2a interrogation approvals + Design E/A ratification record awaiting canonical signature | `z1-inbox/2026-09-23/interrogation_approvals.md` |
| 2026-09-26 | **Q-MAIL-EVIDENCE-LEDGER-01** | Pseudonymous Git-backed Mail Evidence Ledger — private evidence, deterministic privacy projection, public engineering receipts | `z1-inbox/2026-09-24/Q-MAIL-EVIDENCE-LEDGER-01.md` |

## Decided (9)

| decision | candidate | signed by | on | ruling |
|---|---|---|---|---|
| ✅ ratified | **Q-CYCLE3-FALSIFY-01** | Night | 2026-09-08 | `z1-inbox/2026-09-08/Z2_RULINGS_2026-09-08.md`<br>`cycle-3-falsification-approved-20260908` |
| ✅ ratified | **Q-JESTER-CHECK-01** | Night | 2026-09-08 | `z1-inbox/2026-09-08/Z2_RULINGS_2026-09-08.md`<br>`h-cand-batch-ratified-20260908` |
| ✅ ratified | **Q-WITCH-CASCADE-01** | Night | 2026-09-08 | `z1-inbox/2026-09-08/Z2_RULINGS_2026-09-08.md`<br>`h-cand-batch-ratified-20260908` |
| ✅ ratified | **Q-INTENTOS-LAUNCH-01** | Night | 2026-09-14 | `z1-inbox/2026-09-14/Z2_RULINGS_2026-09-14.md`<br>`9a2a469be2cbbe1d559b78d0b0fd41d286c21d0313bc61482b906b474f5d3309` |
| ✅ ratified | **Q-INTENTOS-TEST-01** | Night | 2026-09-16 | `z1-inbox/2026-09-16/Z2_RULINGS_2026-09-16.md`<br>`eb568ab4a65efbae21927c646b18be459a0c8de8353d59fe8b4cc451f3ed36ae` |
| ✅ ratified | **Q-MERGE-SCOPE-01** | Night | 2026-09-16 | `z1-inbox/2026-09-16/Z2_RULINGS_2026-09-16.md`<br>`f04b05d31dad3138c47b3875b2104776b3f4a80a65c5d1a376ec50f867dac53a` |
| ✅ ratified | **Q-MOLT-LEDGER-SCAN-01** | Night | 2026-09-16 | `z1-inbox/2026-09-16/Z2_RULINGS_2026-09-16.md`<br>`44276df7c921d87cc388922155eace549f1f57b71134f65422d9be1770859eb2` |
| ✅ ratified | **Q-BOARD-RULING-02** | Night | 2026-09-18 | `z1-inbox/2026-09-18/Z2_RULINGS_2026-09-18.md`<br>`b80131eba24815480dfd83630cfbdd69672fb017bf4e264e081a9a05326f3c6a` |
| ✅ ratified | **Q-BOARD-RULING-14** | Night | 2026-09-18 | `z1-inbox/2026-09-18/Z2_RULINGS_2026-09-18.md`<br>`27c98b653cefe16826fe3b2b76fcfdc822cb87b00a5ce81dc7c256112a7f51eb` |

## ⚠️ Falsifier waivers (3) — open for Z2

A candidate with no falsifier. The waiver is the candidate's own claim that it predicts nothing, recorded so it cannot pass silently. Accepting or refusing it is Z2's act.

| candidate | stated reason |
|---|---|
| **Q-FRAMEWORK-MAPPING-01** | the block declares itself Type H, 'no falsifier required — reference architecture'. Recorded as the candidate's own claim, not as an accepted exemption: Z2 accepts or refuses it. |
| **Q-SA-WINDOW-DESIGN-E-PLUS-A-01** | As filed, this candidate makes falsifiable claims but contains no explicit ## Falsifier or falsifier: field. Indexed to expose the omission; Z2 must either require an explicit falsifier or consciously accept the waiver before ratification. |
| **Q-Z2-PHASE-2A-INTERROGATION-COMPLETE-01** | As filed, this document records a human Z2 decision and implementation authorization but contains no explicit ## Falsifier or falsifier: field. Indexed as awaiting canonical signature so the decision cannot be treated as mechanically ratified by prose alone. |

## Open questions for Z2 (137)

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

### Q-BOARD-PUBLISH-01 (4)

`z1-inbox/2026-09-18/Q-BOARD-PUBLISH-01.md`

- [ ] Board surface — serve the board from a login-gated Cloudflare Worker, replacing d17's local-only? — options: serve behind login, stay local, later
- [ ] The allow-list is identities (email / GitHub login), one per member — no shared password — and it is enforced twice: by the Access policy in front, and by the Worker itself (`ACCESS_ALLOWED_EMAILS`), so a policy widened by mistake still gets `403` from the Worker
- [ ] The Access policy is receipted in the tree (`z1-inbox/<date>/ACCESS_POLICY_RECEIPT_<date>.md`, runbook §5): application, AUD, rule type, identity count and the hash of the list — so a later widening is detectable without publishing addresses
- [ ] The relay's own gate and HMAC stay as they are; the Worker adds a login in front of the page, not a new path into the relay

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

### Q-BOARD-RULING-15 (1)

`z1-inbox/2026-09-14/Q-BOARD-RULING-15.md`

- [ ] FALS-43 — batch ruling on the 43 hypotheses without written falsifiers? — options: rule now, later

### Q-BOARD-RULING-16 (1)

`z1-inbox/2026-09-14/Q-BOARD-RULING-16.md`

- [ ] docs/ triage — rule by hash over DOC_TRIAGE_2026-09-08.md: archive the 53 as listed, edit the list, or hold? — options: archive as listed, edit list, later

### Q-BOARD-RULING-20 (2)

`z1-inbox/2026-09-19/Q-BOARD-RULING-20.md`

- [ ] Test harness as §A step 3 — options: adopt as §A step 3, keep advisory, later
- [ ] The parent block `Q-INTENTOS-TEST-01` keeps its own status; this block records the choice for d20 only

### Q-BOARD-RULING-21 (2)

`z1-inbox/2026-09-19/Q-BOARD-RULING-21.md`

- [ ] Dashboard: commit the rendered receipt — options: commit the rendered dashboard, render locally per session, later
- [ ] The parent block `Q-INTENTOS-TEST-01` keeps its own status; this block records the choice for d21 only

### Q-BOARD-RULING-22 (2)

`z1-inbox/2026-09-19/Q-BOARD-RULING-22.md`

- [ ] Scale-out order for the test surface — options: registry order (Z-001 first), name the first repo, later
- [ ] The parent block `Q-INTENTOS-TEST-01` keeps its own status; this block records the choice for d22 only

### Q-BOARD-RULING-23 (2)

`z1-inbox/2026-09-19/Q-BOARD-RULING-23.md`

- [ ] Refresh job: enable the PR/issue half — options: enable auto-PR, report-only, later
- [ ] The parent block `Q-INTENTOS-REFRESH-01` keeps its own status; this block records the choice for d23 only

### Q-BOARD-RULING-24 (2)

`z1-inbox/2026-09-19/Q-BOARD-RULING-24.md`

- [ ] May a job advance the board's rev? — options: a job may advance rev, reserve rev for human re-reads, later
- [ ] The parent block `Q-INTENTOS-REFRESH-01` keeps its own status; this block records the choice for d24 only

### Q-BOARD-RULING-25 (2)

`z1-inbox/2026-09-19/Q-BOARD-RULING-25.md`

- [ ] Local copies: re-download or a release asset — options: re-download from the repository, rolling release asset, later
- [ ] The parent block `Q-INTENTOS-REFRESH-01` keeps its own status; this block records the choice for d25 only

### Q-BOARD-RULING-26 (2)

`z1-inbox/2026-09-19/Q-BOARD-RULING-26.md`

- [ ] Resource-based grounding of the refresh job — options: confirm the reading, name a regulatory time-frame, later
- [ ] The parent block `Q-INTENTOS-REFRESH-01` keeps its own status; this block records the choice for d26 only

### Q-BOARD-RULING-27 (2)

`z1-inbox/2026-09-19/Q-BOARD-RULING-27.md`

- [ ] Model endpoint policy for the bus — options: none, local, hosted, later
- [ ] The parent block `Q-INTENTOS-BUS-01` keeps its own status; this block records the choice for d27 only

### Q-BOARD-RULING-28 (2)

`z1-inbox/2026-09-19/Q-BOARD-RULING-28.md`

- [ ] Issue mirror for REQ- records — options: mirror to issues, git-only, later
- [ ] The parent block `Q-INTENTOS-BUS-01` keeps its own status; this block records the choice for d28 only

### Q-BOARD-RULING-29 (2)

`z1-inbox/2026-09-19/Q-BOARD-RULING-29.md`

- [ ] The smoke contract in the manifest — options: flag means carries, keep the text match, later
- [ ] The parent block `Q-INTENTOS-BUS-01` keeps its own status; this block records the choice for d29 only

### Q-BOARD-RULING-30 (2)

`z1-inbox/2026-09-19/Q-BOARD-RULING-30.md`

- [ ] Squash-merge read pointer — options: mechanical pointer move, keep NEEDS-HUMAN, later
- [ ] The parent block `Q-INTENTOS-BUS-01` keeps its own status; this block records the choice for d30 only

### Q-BOARD-RULING-32 (2)

`z1-inbox/2026-09-19/Q-BOARD-RULING-32.md`

- [ ] KNOWN_RED list in the refresh job — options: accept the list, require empty, later
- [ ] The parent block `Q-INTENTOS-REFRESH-01` keeps its own status; this block records the choice for d32 only

### Q-BOARD-RULING-33 (3)

`z1-inbox/2026-09-19/Q-BOARD-RULING-33.md`

- [ ] Board filename — rename to `intent-os-board.html` with a redirect from the old path, keep the frozen path, or later
- [ ] The move is one commit: rename, every reference, the Worker redirect, the runbook, the re-seal — nothing lands piecemeal
- [ ] Conditioned on d31: the executing PR opens only after d31's ruling PR has merged, and carries the Worker redirect exactly when d31 ruled `serve behind login`; it stays held while d31 is `later`

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

### Q-IC-RATIFY-BYPASS-01 (3)

`z1-inbox/2026-09-18/IC-CAND-RATIFY-MANUAL-BYPASS.md`

- [ ] Register IC-RATIFY-BYPASS-01 as stated (or edit the class / duration)
- [ ] Accept the guard as the correction — a Tier 2 gate change carried in #409 — or ask instead for the alternative the review named: a Z2 ruling that keeps a by-hand exception and says how its review and provenance requirement is met
- [ ] Accept, edit or refuse the prevention (a cross-tool self-test case)

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

### Q-PHASE-2-BOARD-MOLT-01 (6)

`z1-inbox/2026-09-19/Q-PHASE-2-BOARD-MOLT-01.md`

- [ ] **Falsifier acceptable?** (data persistence + 5-min SLA)
- [ ] **Molt tier matches claim?** (0 claimed = 0 measured, no constants changed)
- [ ] **Governance compliance?** (Temporal dissolution, RLS, audit trail)
- [ ] **Risk acceptable?** (mitigations sufficient?)
- [ ] **Deployment feasible?** (Night can execute 6-step guide?)
- [ ] **Ready to ratify?** (Sign with sha256 hash)

### Q-RESEARCH-OPS-LOOP-AND-AUDITOR-01 (9)

`z1-inbox/2026-09-19/Q-RESEARCH-OPS-LOOP-AND-AUDITOR-01.md`

- [ ] Research findings currently stall; this loop solves a real bottleneck
- [ ] The three tools are well-specified and non-overlapping in purpose
- [ ] findings-manifest.yaml format is clear enough for reliable encoding of operations
- [ ] Gate conditions are strong enough to prevent bad implementations from merging
- [ ] Falsifiers are mechanical, testable, not subjective (all event-based)
- [ ] Predictions are pre-registered and falsifiable within 90 days
- [ ] The auditor sources (GitHub, arXiv, OSPO) are trustworthy; filtering logic won't spam the board
- [ ] This is a genuine Tier 2 molt (changes how work flows; requires validation cycle and ratification)
- [ ] Once adopted, the system scales: every research finding and external best practice feeds into governance automatically

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

## Records (42)

No decision requested. Listed so the coverage rule cannot be satisfied by silence.

| file | what it is |
|---|---|
| `z1-inbox/2026-09-22/HANDOFF.md` | Session Close Handoff — OI-BRIDGE-01 v0.2 Specification & IC-063 Mitigation |
| `z1-inbox/PHASE-2-IMPLEMENTATION-PLAN.md` | Phase 2 Account Hub API Integrations & Cockpit Enhancement — implementation plan |
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
| `z1-inbox/2026-09-14/Z2_RULING_AMBIGUITY_BSM_D.md` | Z2 ruling — AMBIGUITY-BSM-D: Z2-GOVARCH-02 supersedes SESSION_RITUALS §A.1; amend to WGS-primary / halt-only-if-both-fail (Night, 2026-09-14) |
| `z1-inbox/2026-09-14/Z2_RULING_INTENTOS_LAUNCH.md` | Z2 ruling — d17 local only · d18 z1-inbox + INDEX.yaml · d19 freeze path · temporary tokens revoked (Night, 2026-09-14) |
| `z1-inbox/2026-09-14/Z3-DEPLOYMENT-Q-FRAMEWORK-AUDIT-DEPLOY-01.md` | Z3 deployment log — Q-FRAMEWORK-AUDIT-DEPLOY-01 (12 repos, per-repo framework audit) |
| `z1-inbox/2026-09-16/HANDOFF.md` | Handoff — 2026-09-16 (two sessions: Intent-OS test surface · Z2 queue at close of S-091626-01) |
| `z1-inbox/2026-09-16/HOLOGRAPHIC_HYPOTHESIS_PROTOCOL.md` | Holographic self-representation hypothesis testing protocol (Phase 2 integration mocks, Phase 3 live services, Phase 4 verdict analysis) |
| `z1-inbox/2026-09-16/PHASE2_HANDOFF.md` | Phase 2 Handoff — Holographic integration tests complete, CI green, ready for Z2 review and Phase 3 authorization |
| `z1-inbox/2026-09-16/PHASE3_EXECUTION_CHECKLIST.md` | Phase 3 execution checklist (infrastructure complete; awaiting credential deployment) |
| `z1-inbox/2026-09-16/PHASE3_LAUNCH.md` | Phase 3 launch — holographic live service testing (Z2 authorization received; awaiting credential configuration) |
| `z1-inbox/2026-09-16/Z2_RULINGS_2026-09-16.md` | Z2 rulings — 2026-09-16 (six): PR #343 ACCEPT, Q-MOLT-LEDGER-SCAN-01 ACCEPT, SESSION_RITUALS v6.4.2 bump ACCEPT (applied), Section F.1 ACCEPT reading (a), ledger → resource-based DIRECTION_GIVEN, ratify.py 1.2.0 awaiting Z2 (Night, 2026-09-16) |
| `z1-inbox/2026-09-17/HANDOFF.md` | Handoff — 2026-09-17 (Intent-OS refresh: the mechanism for automated updates) |
| `z1-inbox/2026-09-17/REQ-20260917-01.md` | Agent request REQ-20260917-01 — Wire the decision relay live so the board can rule and request from a browser |
| `z1-inbox/2026-09-18/Z2_RULINGS_2026-09-18.md` | Z2 rulings 2026-09-18 — signatures issued by .z1-control/ratify.py and tools/intent_os_reconcile_v1_0.py |
| `z1-inbox/2026-09-18/Z2_RULING_MERGE_IS_RATIFICATION.md` | Z2 ruling — the merge is the ratification: the hash echo is retired, a ruling's PR changes one file, the merger and the merge date sign it, a job on main records it (Night, 2026-09-18) |
| `z1-inbox/2026-09-19/BROKER-TRACK-STATUS-2026-09-19.md` | Broker Track status report (2026-09-19) |
| `z1-inbox/2026-09-19/PHASE-1-IMPLEMENTATION-STATUS.md` | Phase 1 implementation status report (2026-09-19) |
| `z1-inbox/2026-09-19/PHASE-1B-GRANT-MATCHING-SPEC.md` | Phase 1B Grant Matching Engine specification |
| `z1-inbox/2026-09-19/PHASE-1B-IMPLEMENTATION-STATUS.md` | Phase 1B implementation status report |
| `z1-inbox/2026-09-19/PHASE-2B-SPECIFICATION.md` | Phase 2B specification |
| `z1-inbox/2026-09-21/Z2_RATIFY_SMAG_BLOCKERS.md` | Z2 Ratification: SMAG Calibration & Sequencing Blockers |
| `z1-inbox/2026-09-22/MEASUREMENT-SCOPE-AUDIT.md` | Measurement Scope Audit — Blockchain Trading Pilot (Z-012) |
| `z1-inbox/2026-09-23/BUZZ_INTEGRATION_SPEC.md` | Buzz Integration Specification — Technical mapping of HumanAIOS Z1/Z2/Z3 governance to Buzz affordances |

---

**Converting an inbox item to a Z2 decision:** add it to `z1-inbox/INDEX.yaml` under `candidates:` with `status: awaiting_z2` and a falsifier in the block itself, run `python3 .z1-control/render.py`, and commit both. An undecided candidate carries no signature fields at all.

Z2 records the decision by setting `status`, `ratified_by`, `ratified_at`, a `z2_ruling` that resolves to a file **indexed under `records:`**, and a `z2_hash` that **appears in that ruling**. All five are required: the validator refuses a signature from anyone outside `ratifiers:`, and refuses a hash the cited ruling does not carry.
