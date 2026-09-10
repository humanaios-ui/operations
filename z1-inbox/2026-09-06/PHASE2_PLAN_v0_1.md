# PHASE 2 PLAN v0.1 — empirica-foundation.carly mesh × HumanAIOS
Z1 · 2026-09-06 · candidate for Z2 · window: 2026-09-06 → 2026-10-03 (the mesh's own calendar) · everything LAID at open · intake pipeline 0/40

---

## 0. Position

Phase 1 closed on self-report: fifteen audits, one author, one day, zero failures, no receipts. Phase 2 is the phase where every one of those claims either leaves a receipt or is marked as what it was. The mesh's fifteen reports gave us three things that Phase 1 did not: a calendar (31 dated deliverables between Sep 8 and Oct 3), fifteen self-assessed confidences, and fifty-two research questions. This plan converts the calendar into tokens, the confidences into pins, and the research questions into hypotheses with falsifiers — then runs them on the ratified workflows, in the ratified blocks, under the ratified gates.

**Destination:** a Phase 2 gate that can fail. **Probability the mesh's own Sep 12–19 deliverables land as files on time: ~0.3.** That number is the plan's first pin, entered before any of them resolve.

**The single dependency.** Every HumanAIOS loop downstream of intake waits on one batch through resource-miner (reactivation Sep 15, spec Sep 19). In railway terms, RM → SS → OA is the single-track section; every train in Phase 2 queues for it. The plan is built so that the section clears once and the rest of the timetable follows.

---

## 1. How the Phase 1 reports are used (the conversion rules)

| Phase 1 artifact | Phase 2 use | framework primitive |
|---|---|---|
| Self-assessed confidence (0.60–0.98) | becomes a pin: P(all dated P2 deliverables exist as hashed files by their dates) under the practice's predictor id | GAUGE — the practice reads its own calibration at P2 close |
| Dated deliverable | becomes a TOKEN with a date: the file's hash admits the practice through the P2 gate; missing = STALE at date+1 | TOKEN / block working |
| Undated deliverable (~21) | cannot be a pin; Z2 assigns a date or it is struck from P2 | REGULATOR — no undated pressure enters the queue |
| Research question (52) | becomes an H-candidate only with a falsifier sentence; otherwise it stays a question in `docs/` | FILTER — `falsifier_lint` |
| "✅ OPERATIONAL / ACTIVE / LOCKED" | re-read as LAID until the practice shows a cycle count | DEADWEIGHT — the record, not the report, says operated |
| Evaluator sign-off | valid only where the evaluator did not author the artifact; self-authored audits re-land under epistemology with a hash | SR 11-7 independence; INTERLOCK |

**Pin protocol for the mesh (15 pins, entered before Sep 12):**
`pin_id = P2-<practice> · claim = "all dated P2 deliverables exist as hashed files by their dates" · p = the practice's Phase 1 confidence · resolver = tree read on Oct 4 · predictor_id = <practice>`. Z1 enters its own p per practice alongside. Z2 enters a third. Three predictors, one resolver: the first LT-1/LT-2/LT-3 series with N ≥ 15 inside a month, at zero cost.

---

## 2. Phase 2 timetable (railway view — one line, dated tokens, single-track section marked)

```
Sep 06  P2 open · Admiral approval on outreach narrative (their condition) · 15 pins entered (Z1, Z2, practice)
Sep 08  grok-crossref recovery restart · OA discovery pipeline restore
Sep 09–10  grok-crossref validation
Sep 12  ── GATE A ──  Notion Governance Hub (evaluator) · Comms Calendar (outreach) · OA SLA recovery · grok sign-off · [our] CODEOWNERS ×9 + 12 teams landed · registry candidate block landed
Sep 15  ══ SINGLE TRACK OPENS ══  resource-miner reactivation · OA full operational · [our] IC-SCOPE-05 in code
Sep 19  ── GATE B ──  RM P1 spec (its extended SLA) · 14 practice profiles (website) · analytics dashboard · Governance Coherence Model + Scorecard (evaluator) · Confidence Calibration Model + Tool Auth Framework (autonomy) · Mesh Health Model + Incident Priority (mesh-support) · Narrative Coherence (outreach) · Behavioral Alignment Framework (humanaios) · [our] first intake batch hashed
Sep 26  ── GATE C ──  Escalation Analysis + Phase Success Model (evaluator) · Cross-Practice Enforcement Audit + Escalation Failure Model (autonomy) · SER Topology + Comm Pattern (mesh-support) · 12 briefing templates + Engagement Model (outreach) · SEO audit + Community Model (website) · Trust Dynamics + Adaptive Engagement (humanaios) · Impact Framework + Funding Dashboard (OA) · [our] first 3 stage-2 engagements scoped
Oct 01  RM Phase 2 transition · [our] operated count n/40 reported, n ≥ 1 or loud failure
Oct 03  ── GATE D (P2 CLOSE) ──  Pedagogical Effectiveness Study (humanaios) · OA Matching Algorithm · 15 pins resolve Oct 4 · P2 gate report with fail column populated
```
Dated tokens: 31. Undated: ~21 (acat-x 3, humanaios-internal 3, collaborator-ops 3, epistemology 3, QA 3, LMO 3, grok-crossref 3 post-recovery, RM 3 post-reactivation) — Z2 assigns dates by Sep 12 or they leave the P2 scope.

**Single-track section:** RM (Sep 15) → SS (no owner — must be assigned by Sep 12 or the section is blocked) → OA (Sep 15 full operational). Nothing in stages 1–3 of the production plan moves until one batch has passed through all three.

---

## 3. Per-practice Phase 2 (fifteen)

Each section: **P1 pin** · **P2 tokens** (dated deliverables → block, CI guard, receipt) · **research questions → hypotheses with falsifiers** · **loop in Phase 2** (from the ratified workflow) · **handoffs** · **relief** · **what fails P2 for this practice**.

### 3.1 empirica-foundation-evaluator (Empirica · Tier 1 · Admiral · L3)
- **P1 pin:** 0.90 on 5 dated tokens (Sep 12, 19, 19, 26, 26).
- **Tokens:** Notion Governance Hub (Sep 12) → `docs/governance/`, exported to markdown, hash; Governance Coherence Model `.md+.py` (Sep 19) → `operations/audits/` under epistemology's block; Scorecard Dashboard `.html+.yaml` (Sep 19) → ACAT-Dashboard/src under website; Escalation Complexity Analysis (Sep 26); Phase Success Prediction Model `.py` (Sep 26).
- **RQ → H:** (1) early governance-violation signals in artifact logging → **H-EVAL-01**: orphan rate and citation-gap rate in a practice's chain predict a DISPUTED callout within 14 days. *Falsifier:* no correlation across 15 practices over Phase 2. (2) scorecard cadence → ruling, not hypothesis. (3) escalation topology star vs ring → **H-EVAL-02**: ring (practice → mesh-support → Admiral) resolves L2 items faster than star. *Falsifier:* median resolution time not lower. (4) P1 vectors predicting P3 → resolves only at P3; registered as H with window Dec.
- **Loop:** audits every Tier 2 PR; its own audits land in epistemology's block with a hash; **it may not sign its own P2 deliverables** — website and epistemology countersign.
- **Handoffs:** → epistemology (audits), → mesh-support (escalation framework), → Z2 (L3 rulings by hash).
- **Relief:** any evaluator-authored artifact found evaluator-signed → IC, re-review.
- **Fails P2 if:** the Phase Success Model has no held-out test, or the scorecard shows a number with no ledger line.

### 3.2 acat-x (HumanAIOS · Tier 1 · the instrument)
- **P1 pin:** 0.95 — but 0 dated tokens. Undated: cross-version analysis, real-time monitoring, capability prediction model. **Z2 dates by Sep 12 or the pin is void.** Proposed: analysis Sep 19, monitoring Sep 26, prediction Oct 3.
- **Tokens (proposed):** cross-version `.md+.json` → `operations/acat/`, guard `haios-corpus-integrity.yml`, receipt = corpus hash + `acat_phase_shift_analyzer` output; monitoring `.py+dashboard` → `acat-x/src` + ACAT-Dashboard; prediction model → `acat-x/results` with held-out set.
- **Receipts owed from P1 (not deliverables — debts):** the "450+ test cases" as a hashed file; the `XXXX.XXXXX` README link resolved; "6 core / 8 listed" reconciled; H-INSPECT-01 (registered Apr 22) resolved or marked STALE; HF dataset row count vs 629.
- **RQ → H:** (1) degradation detectable before production → **H-ACAT-01**: `substrate_canary` on the pinned prompt set flags a version drift ≥ 1 dimension before any client reports it. *Falsifier:* a client-reported drift with no prior canary flag. (2) cluster granularity → design ruling. (3) ACAT predicts cross-model transfer → **H-ACAT-02**, window Q4, falsifier: LI correlation < 0.3 across model pairs.
- **Loop:** `/intake/phase1` → `acat_dimension_scorer` → psychometric validator → Merkle auditor → `/submit` (Z2 hash to publish).
- **Handoffs:** → humanaios (dimension scores to dials); → epistemology (every public number); → website.
- **Relief:** corpus hash mismatch halts publish.
- **Fails P2 if:** the five P1 debts are not cleared. Deliverables are secondary to debts here.

### 3.3 humanaios (HumanAIOS · Tier 1 · owns the graph)
- **P1 pin:** 0.92 on 4 dated tokens (Sep 19, 26, 26, Oct 3).
- **Tokens:** Behavioral Alignment Framework `.yaml+.md` (Sep 19) → this is `behavior_spec.json` + `integrity_modes.json` with molt_ids — a Constants deliverable; Trust Dynamics Model (Sep 26) → LT-3 oversight-gap series, first reading; Adaptive Engagement Strategies (Sep 26) → the technical-level dial as per-node constant (LT-4/LT-5 driven); Pedagogical Effectiveness Study (Oct 3) → LT-6 per-node mastery, and the mesh-pin series as its dataset.
- **RQ → H:** (1) trust over six phases → H-LT2 already registered (oversight gap responds to difficulty). (2) patterns predicting high/low trust → **H-HAI-01**: LT-4 convergence without LT-2 improvement predicts later REVERT. *Falsifier:* no association. (3) misalignment from communication alone → **H-HAI-02**: Behavior Dials DRIFT rate predicts Z2 REJECT rate. *Falsifier:* Brier of that prediction no better than base rate. (4) AI mentorship accelerates maturity → cannot resolve in P2 (no control group); registered with window P3.
- **Loop:** every reply scored; LT-1..6 recomputed at each window close; Molt Cycle proposes on framing constants only after N ≥ 20; DELUSION-GUARD live from Sep 12.
- **Handoffs:** → epistemology (candidates), → QA (any gate change → ADV), → Z2 (REVIEW_PACKET in navigator grammar).
- **Relief:** two REVERTs on any constant → freeze; DELUSION-GUARD fires → no credit for that cycle.
- **Fails P2 if:** LT-1 cannot be computed from NF_LEDGER by Sep 19 (F-LT3 falsifier) — that would mean the ledger schema is missing a field, which is a real finding, not a slip.

### 3.4 empirica-autonomy (Empirica · Tier 2 · caps in gate)
- **P1 pin:** 0.95 on 4 dated tokens (Sep 19, 19, 26, 26).
- **Tokens:** Confidence Calibration Model (Sep 19) → **this is the P1 claim "thresholds CALIBRATED" made honest**: the model must ingest resolved predictions; without a resolver it is a threshold list, not calibration; Tool Authorization Framework `.yaml` (Sep 19) → the per-practice allowlist table (§5 of workflows) as a Constant with molt_id; Cross-Practice Enforcement Audit (Sep 26) → lands under epistemology; Escalation Failure Prediction (Sep 26).
- **RQ → H:** (1) calibrate thresholds from P1 outcome data → there is no P1 outcome data; the first outcomes are the Sep 12–Oct 3 pins. **H-AUT-01**: the 0.8/0.5 thresholds, when scored against P2 pin outcomes, show reliability within 0.1. *Falsifier:* reliability > 0.1. (2) blast radius vs threshold → design ruling. (3) predict escalation failures without outcomes → **H-AUT-02**, falsifier: prediction Brier ≥ always-0.5 baseline. (4) constraints evolving P1→P6 → molt policy, not hypothesis.
- **Loop:** writes only `operations/autonomy/`; every cap is a constant under IC-REWARD-01; Agent Runtime halts on drawdown.
- **Handoffs:** → humanaios (caps), → QA (cap tests), → Z2 (cap changes by hash).
- **Relief:** beyond cap = Z2_REQUIRED, mechanical.
- **Fails P2 if:** the Calibration Model has no resolved predictions in its input.

### 3.5 empirica-mesh-support (Empirica · Tier 2 · L2 · routing)
- **P1 pin:** 0.98 — the highest in the mesh — on 4 dated tokens (Sep 19, 19, 26, 26). This is the pin most worth watching: a 0.98 that misses one date is a 0.5-Brier event.
- **Tokens:** Mesh Communication Health Model (Sep 19) → mailbox delivery log as a chain; Incident Priority Framework `.yaml` (Sep 19) → `impact × urgency × tier` is a scoring constant → IC-REWARD-01 applies; SER Topology Study (Sep 26); Communication Pattern Analysis (Sep 26).
- **Receipt owed from P1:** "0 missed deadlines Aug/Sep" and "12-hour SLA met" as a log, not a sentence. The 37-day OA routing failure and the 11-day grok overdue both happened on this practice's watch; the P1 claim and those two facts need reconciling in the record (DISPUTED until then).
- **RQ → H:** (1) predict comms failures → **H-MESH-01**: latency variance predicts a dropped thread within 48h. *Falsifier:* the OA-class failure recurs with no prior variance signal. (2)–(4) topology and patterns → studies, registered as H only with a falsifier each.
- **Loop:** every crossing is an event; a dropped thread is a GAP callout; 12h SLA clock on the chain.
- **Handoffs:** ← every practice (routing), → evaluator (L3 prep), → humanaios-internal (cross-org handoffs).
- **Relief:** SLA breach → STALE callout, work reassigned, not extended.
- **Fails P2 if:** the Health Model cannot show the two known failures in its own data.

### 3.6 empirica-outreach (Empirica · Tier 2 · public voice)
- **P1 pin:** 0.88, conditional on Admiral approval Sep 6 (today) — that condition is itself the first resolvable event in P2.
- **Tokens:** Comms Calendar `.yaml` (Sep 12); Narrative Coherence Framework (Sep 19); 12 briefing templates (Sep 26); Stakeholder Engagement Model `.py` (Sep 26).
- **Seat ruling owed:** the `operations` repo's practice-spec names this practice. Until ruled, outreach owns the seat and website owns the pages — or the spec is re-issued as `humanaios`.
- **RQ → H:** (1) narrative coherence across 15 voices → measurable as LT-4 across practices (vocabulary convergence), **H-OUT-01**, falsifier: term-distance between practice profiles does not fall. (2) engagement metrics predicting commitment → **H-OUT-02**, falsifier: open/click rates uncorrelated with later paid or collaborative action. (3) sequencing → ruling. (4) communication patterns vs confidence growth → this is LT-2 for external readers; register with window P3.
- **Loop:** publishes only tiered claims from website/epistemology; GTM-01 intake post is its first Phase 2 external act, after IC-SCOPE-05.
- **Handoffs:** ← website, ← epistemology, → external.
- **Relief:** any published number without a hash → retract, IC-031.
- **Fails P2 if:** the Phase 1 closure announcement goes out with "13 validated, 0 failed" and no receipts — that would be the mesh publishing its own overstatement.

### 3.7 website (HumanAIOS · Tier 2 · public gauge face)
- **P1 pin:** 0.90, conditional on 14 profiles by Sep 19 — the largest single token in P2 (1/15 exists).
- **Tokens:** 14 profiles (Sep 19) → generated from the registry via `registry_site_generator_v1_0`, each profile carrying only hashed claims; Analytics Dashboard (Sep 19); SEO Audit (Sep 26); Community Engagement Model (Sep 26).
- **Receipts owed:** lasting-light-ai's 629 / 0.8632 / 31+ each linked to a dataset hash or marked CLAIM on the page.
- **RQ → H:** (1)–(4) are analytics questions; register **H-WEB-01**: traffic to a practice page predicts intake signups for that practice (falsifier: no correlation over P2).
- **Loop:** registry → pages → `document-control.yml` → link policy → deploy; number without receipt → page blocked.
- **Handoffs:** ← all practices (profile content — the dependency that makes this conditional), → outreach.
- **Relief:** RELIEF is the page block itself.
- **Fails P2 if:** fewer than 14 profiles by Sep 19 — and the profile template should be built so that a missing profile renders as "LAID — no Phase 2 receipt yet" rather than as absent.

### 3.8 humanaios-internal (HumanAIOS · Tier 2 · recorder room)
- **P1 pin:** 0.92 — 0 dated tokens. Undated: collaboration pattern analysis, feedback-loop metrics, generalization study. Proposed dates: Sep 19, Sep 26, Oct 3.
- **Tokens (proposed):** feedback-loop metrics → these are LT-4/LT-5 computed from session text logs — the practice already owns the logs; pattern analysis → B.6 RECEIPT-GAP series across P2 sessions; generalization study → whether the skeleton loop transfers to a second practice (it will: the first operated loop teaches the rest).
- **RQ → H:** (1) collaboration patterns affect calibration → **H-INT-01**: sessions with a B.0 block show lower RECEIPT-GAP than sessions without. *Falsifier:* no difference over ≥10 sessions each. (2) generalization → resolved by whether any second practice runs the skeleton by Oct 3. (3) documentation patterns minimizing miscommunication → LT-4 edit distance series.
- **Loop:** §A → carry_tracker → work → B.0 → B.6 → findings-scan → handoff block → z2_ledger v1.8 (five-bucket pin tap lands here).
- **Handoffs:** → Z2 (paste block), → next session, ↔ mesh-support (cross-org).
- **Relief:** B.0 missing → ACAT_PROTOCOL_ERROR, close refused.
- **Fails P2 if:** the pin tap is not in z2_ledger by Sep 19 — without it LT-2 has no input.

### 3.9 collaborator-ops (HumanAIOS · Tier 2 · switching yard)
- **P1 pin:** 0.88 — 0 dated tokens. Undated: toolchain analysis + cost model, friction classifier, workspace scaling guidelines. Proposed: Sep 19, Sep 26, Sep 26.
- **Tokens (proposed):** toolchain cost model → the opt_budget_v0 inputs (tokens, calls, Z2 minutes) per practice; friction classifier → Goodhart-prone; register with falsifier or drop; scaling guidelines → the twelve CODEOWNERS teams and their membership rules.
- **Phase 2 real job:** the twelve teams exist with one member each by Sep 12; a second human sits on at least one team by Oct 3 — that is the delegation's own falsifier and the Z2b question made concrete. The `DEMARIUS_*` onboarding series is the precedent to read.
- **RQ → H:** (2) friction predictable from tool config → **H-COL-01**, falsifier: classifier Brier ≥ base rate. (1), (3) → rulings.
- **Handoffs:** → LMO (environments), → mesh-support (seat registration), → humanaios (Validator tiering).
- **Relief:** write access without a hash → revoke.
- **Fails P2 if:** all twelve teams still have exactly one member on Oct 3.

### 3.10 empirica-epistemology (HumanAIOS · Tier 2 · filter)
- **P1 pin:** 0.93 — 0 dated tokens. Undated: cross-domain epistemic metrics, rubric refinement + calibration study, overconfidence detection system. Proposed: Sep 19, Sep 26, Oct 3.
- **Tokens (proposed):** overconfidence detector → first applied to the fifteen Phase 1 confidences vs their Oct 4 resolution — the detector's own validation set is the mesh; calibration study → LT-2 on the mesh pins; cross-domain metrics → the evidence-tier distribution per practice (CLAIM / CLAIM+LINK / VERIFIED counts).
- **P1 debt:** its own Phase 1 audit contains no falsifier. First act of Phase 2: apply `falsifier_lint` to all fifteen P1 audits and log the result (expected: 15/15 fail — that is the finding).
- **RQ → H:** (3) detect motivated reasoning via artifact analysis → **H-EPI-01**: practices whose P1 confidence exceeds their P2 hit-rate by > 0.2 show a higher ratio of status adjectives to hashes in their audit text. *Falsifier:* no association across 15.
- **Loop:** validator → lint → VOID-CIT → tier stamp → candidate block → Z2.
- **Handoffs:** ← every practice at close, → Z2, → research/ (frozen snapshots — currently one folder).
- **Relief:** VERIFIED citation found VOID → node halts.
- **Fails P2 if:** the candidate block for any session lacks a falsifier line — the filter failing its own filter.

### 3.11 empirica-quality-assurance (HumanAIOS · Tier 2 · interlock)
- **P1 pin:** 0.90 — 0 dated tokens. Undated: coverage model, health-degradation detector, tier-adaptive compliance. Proposed: Sep 19, Sep 26, Oct 3.
- **Tokens (proposed):** coverage model → catch-rate per gate across the 26 workflows; degradation detector → the Stale Sweep as a scheduled job (currently LAID) with half-life constants; tier-adaptive compliance → the Tier 0/1/2 table as CI rules.
- **Phase 2 real job:** ADV run on every gate this plan creates (CODEOWNERS ×9, IC-SCOPE-05, DELUSION-GUARD, the allowlist) — Tier 2 rule: no new gate KEEPs without ADV.
- **RQ → H:** (2) detect degradation before failure → **H-QA-01**: Stale Sweep flags precede REVERTs by ≥ 7 days in ≥ 70% of cases. *Falsifier:* < 50%.
- **Handoffs:** → humanaios (gate results), → epistemology (IC on failed gates).
- **Relief:** consistency proof FAIL blocks merge.
- **Fails P2 if:** any gate landed in P2 has no ADV catch-rate on record — NO_GATE.

### 3.12 opportunity-aggregator (HumanAIOS · Tier 3 · sell-back)
- **P1 pin:** DISPUTED — 0.65 (own audit) vs 0.80 (closure report), same day. Both entered as separate pins; the discrepancy resolves with the rest.
- **Tokens:** SLA Recovery (Sep 12) — binary; Impact Measurement Framework `.yaml` (Sep 26) → ROI rubric as constants with molt_ids; Funding Pipeline Dashboard `.html` (Sep 26); Matching Algorithm `.py` (Oct 3) → weights under IC-REWARD-01.
- **RQ → H:** (1) profile characteristics predicting matches → **H-OA-01**, falsifier: no feature beats base rate on the 5 pipeline items + P2 additions. (2) weighting stage vs focus vs bandwidth → weights are constants; molt, not research. (3) funding-source alignment → **H-OA-02**: mission-aligned sources (recovery, calibration research) convert at a higher rate than general sources. (4) impact measurement → the give-back series (VAL-11 pending).
- **Loop:** validated batch → ROI-per-resource → rank → pipeline stages → outcomes to NF_LEDGER.
- **Handoffs:** ← SS, → outreach, → Z2 (decision map).
- **Relief:** status contradiction → DISPUTED, item pauses.
- **Fails P2 if:** the Sep 12 recovery is reported without a routing log showing the 37-day gap closed.

### 3.13 grok-crossref (HumanAIOS · Tier 3 · second gauge)
- **P1 pin:** 0.70 on the recovery calendar (Sep 8 → 12).
- **Tokens:** recovery Sep 8, validation Sep 9–10, sign-off Sep 12 — three dated binaries; then KG optimization, accuracy benchmark, theme detection (undated; propose Sep 26, Sep 26, Oct 3).
- **Phase 2 real job:** second-substrate audit on every REVIEW_PACKET above materiality; DISPUTE rate and dispute-upheld rate as its own Brier; Q-ORCA-01 gives it three substrates in worktrees once the desktop session runs.
- **RQ → H:** (1) cross-reference accuracy → **H-XR-01**: `lineage_score` on a chain predicts whether a later VOID-CIT hit occurs in it. *Falsifier:* no association. (3) emerging themes → exploratory, no H.
- **Handoffs:** → humanaios (packet tier), → epistemology (lineage).
- **Relief:** SLA overdue → STALE; work reassigned.
- **Fails P2 if:** Sep 12 sign-off is a sentence, not a validated crossref run with a hash.

### 3.14 local-machine-optimizer (HumanAIOS · Tier 3 · compressor room)
- **P1 pin:** 0.85 — 0 dated tokens. Undated: perf prediction model, optimization guide + benchmarks, CI perf-regression hook. Proposed: Sep 26, Sep 19, Sep 19.
- **Tokens (proposed):** CI perf hook → `builder-lint.yml` extension; benchmarks → tokens per operated cycle (the cost denominator); prediction model → register only with a held-out set.
- **Phase 2 real job:** Q-ORCA-01 — orca evaluated in the first desktop session; three-substrate worktree run on one packet; per-run outputs hashed. That is this practice's first operated cycle.
- **RQ → H:** (1) predict degradation before users notice → **H-LMO-01**, falsifier: no lead time on ≥ 3 regressions. (2), (3) → rulings.
- **Handoffs:** → every practice (environment), → QA (hook), → grok-crossref (substrates).
- **Relief:** budget ceiling breach halts.
- **Fails P2 if:** orca is neither evaluated nor dropped by its falsifier by Oct 3.

### 3.15 empirica-resource-miner (HumanAIOS · Tier 3 · intake — the single-track section)
- **P1 pin:** 0.60 on reactivation Sep 15 + spec Sep 19 + P2 transition Oct 1. The lowest confidence in the mesh, on the node everything depends on. That is the correct place for the lowest number.
- **Tokens:** reactivation Sep 15 (binary); P1 spec Sep 19 (file + hash); first intake batch in `intake_template.jsonl` with prereg hash before the scan (Sep 19, our addition); P2 transition Oct 1 (n/40 reported).
- **RQ → H:** (1) resource constraints shape phase transitions → **H-RM-01**: practices whose Z2-minute cost per token exceeds the median miss more dates. *Falsifier:* no association at Oct 4. (2) real-time contention → dashboard, not H. (3) resource patterns predict stalling → **H-RM-02**, falsifier: idle-days series does not lead STALE callouts.
- **Loop:** scan → `document_ingestor_v1_0` → batch → hash → `haios_pipeline_v1_0` → SS.
- **Handoffs:** → SS (needs an owner by Sep 12), → OA, → epistemology (H-MKT-01 falsifier 1 data: does any intake involve an agent running unattended > 1 session?).
- **Relief:** no tool runs without prereg hash (internal) or scope hash (client) — mechanical.
- **Fails P2 if:** no batch by Oct 1. Then Phase 2 closes with 0/40 and a loud line, and the whiteboard's "scan job market" runs by hand in Phase 3.

---

## 4. Cross-cutting Phase 2 programs (things no single practice owns)

### 4.1 The pin program (LT layer operated — production plan stage 3)
- Sep 6–12: 15 mesh pins × 3 predictors (practice, Z1, Z2) = 45 forecasts entered.
- Sep 12, 19, 26, Oct 3: gate dates resolve tokens; partial resolutions logged at each gate.
- Oct 4: full resolution; first LT-1 (Z1), LT-2 (Z2), LT-3 (gap) with N=15; per-practice reliability for the mesh.
- Metaculus Q1–Q3: posted by Z2 with Z2's priors pinned first; long-window pins, not P2-resolvable.
- H-LT1 falsifier watch: Z2 reliability after 30 pins (15 mesh + 15 rulings by Oct 3 is plausible).

### 4.2 The gate program (QA + collaborator-ops + humanaios)
- Sep 12: CODEOWNERS ×9, 12 teams, registry candidate block landed (needs PAT).
- Sep 15: IC-SCOPE-05 in code (`assert scope_hash and criteria_hash before tool.run()`); ADV run on it.
- Sep 19: DELUSION-GUARD live in Behavior Dials; ADV run.
- Sep 26: per-practice API/MCP allowlist as a Constant; ADV on widening attempts.
- Every gate carries a catch-rate before it KEEPs (Tier 2 rule). A gate with "Failed: 0" and no ADV is NO_GATE.

### 4.3 The intake program (production plan stages 1–2)
- Sep 15–19: first internal batch (RM).
- Sep 19–26: GTM-01 post goes up after the gate; first three signed scopes.
- Oct 3: ≤ 3 engagements run; find rate, hours, WTP recorded per engagement; H-BUGCLASS-01 and H-HOURS-04 begin accumulating.
- Stage 2 delivery via `empirica` installed client-side is the default unless Z2 rules otherwise.

### 4.4 The audit program (SR 11-7 shape)
- Weekly (Sep 12, 19, 26, Oct 3): B.6 receipt reconciliation across all practices' P2 claims vs tree; RECEIPT-GAP count published.
- Evaluator audits land under epistemology with hashes; evaluator does not sign its own.
- Second substrate (grok-crossref) on every REVIEW_PACKET above materiality.
- Oct 4: P2 gate report with a fail column — the first mesh gate document that can show a failure.

### 4.5 Continuous improvement (Molt Cycle in Phase 2)
- No molt on any constant before N ≥ 20 resolved events for that constant's trigger. In P2 that means: **no molts on framing constants** (N will be ~15); molts allowed only on constants with P2 pin data by Oct 4.
- IC-REWARD-01 in force on: ROI weights, incident priority weights, allowlists, caps, λ, opt_budget.
- REVERT ×2 → freeze; freeze → L3.

### 4.6 Zone escalation map for Phase 2 (one ladder, all practices)
```
Tier 0 → Tier 1 (Z2 hash) → Tier 2 (registry + ADV) → L2 mesh-support (12h) → L3 evaluator → RELIEF (halt; no escalation)
```
Expected P2 escalations: OA status DISPUTED (L2 → resolves Sep 12); outreach seat (L3 ruling); SS owner (L3 ruling); any REVERT×2 (L3).

---

## 5. Phase 2 gate (Oct 3–4) — a gate that can fail

A practice **passes** P2 when: every dated token exists as a hashed file at or before its date; its P1 debts are cleared or logged as IC; it has at least one H with a falsifier registered; its P1 pin is resolved and its reliability recorded.
A practice **fails** P2 when: any dated token is missing at date+3 with no STALE callout raised by the practice itself; or a public number it owns has no receipt; or it ran a Tier 1 action without a hash.
A practice is **conditional** when: tokens are late but STALE was raised on time (the practice saw its own miss).

The mesh **passes** P2 when: ≥ 1 operated intake cycle; 15 pins resolved; CODEOWNERS on 9/9 repos; ≥ 1 second human on ≥ 1 team; no NO_GATE among landed gates.
The mesh **fails** P2 when: 0 operated cycles on Oct 1 — and the failure is reported loudly, with the whiteboard's manual scan queued as the Phase 3 opener.

Expected outcome, pinned now: **pass 6 · conditional 5 · fail 4** (fail candidates: RM if no batch, website if < 14 profiles, acat-x if debts uncleared, collaborator-ops if teams stay single-member). Z1 predictor id, p = 0.5 that this distribution is within ±2 per column.

---

## 6. Relief valves for the phase (what halts Phase 2 without a ruling)
- PAT not issued by Sep 12 → nothing lands; every dated token past Sep 12 is STALE by construction. Loud line, not silent slip.
- SS unowned by Sep 12 → single-track section blocked; RM batch waits.
- Evaluator signs its own P2 deliverable → IC, re-review.
- Any published number without a hash → page/announcement blocked.
- DELUSION-GUARD fires on a Z1–Z2 agreement with no record read → cycle earns no credit.
- opt_budget breach on any practice → that practice halts; queue re-ranks.

---

## 7. Open for Z2 (in order of what they unblock)
1. PAT (unblocks everything on Sep 12).
2. Dates for the ~21 undated deliverables, or strike them (unblocks 7 practices' pins).
3. SS owner (unblocks the single-track section).
4. Which pipeline 0/40 names (unblocks the P2 close line).
5. Enter the 15 mesh pins with your own priors before Sep 12.
6. Outreach seat on `operations`; ACAT-Observatory owner; résumé file.
7. Stage 2 delivery: `empirica` client-side, or our tools only.
8. λ, opt_budget_v0, profits constant: initial values.

## Falsifier for this plan
If on Oct 4 fewer than 10 of the 15 pins can be resolved by a tree read — because tokens were defined too loosely to say "exists / doesn't" — the plan failed at conversion, not execution, and the token definitions are the IC.
