# AI Utility × Human Performance Improvement: Convergence Map
**Status: Z1 DRAFT — not Z2 ratified, not Z3 executed**
**Session: S-061926 | Charter Day ~94 of 90-day charter (charter close July 16, 2026)**

---

## 0. Task

Map the 8-AI "most beneficial utility of AI" prompt responses (Grok, Meta AI, Gemini, Copilot, Kimi2.6, Claude, DeepSeek, Perplexity) against established Human Performance Improvement (HPI) / Human Performance Technology (HPT) methodology, and identify the most beneficial, constructive plan to apply to HumanAIOS.

This document is Z1 only: analysis and drafted recommendations. Nothing here is registered, ratified, committed, or sent. All proposed registry items are marked **[Z2 — NOT REGISTERED]**.

---

## 1. Multi-AI Synthesis Map

| Source | Primary answer | Domain emphasis | Universal caveat present? |
|---|---|---|---|
| Grok | Accelerating scientific discovery (root multiplier) | Biology, materials, climate, physics | Yes — truth-seeking, calibrated, auditable, humble about risk |
| Meta AI | Leverage multiplier for human judgment | Cross-domain | Yes — "skeptical research partner," not sycophantic |
| Gemini | Force multiplier for human intelligence | Healthcare, climate, education | Implicit — friction elimination, human retains ethics/judgment |
| Copilot | Amplify human capability | Discovery, healthcare, risk prediction | Yes — ties explicitly to "AI for good" governance frameworks |
| Kimi2.6 | Augment human cognition/decision-making at scale | Cross-domain expertise gap | Yes — only materializes "with transparency, accountability, equity" |
| Claude (prior instance) | Close expertise gap + accelerate discovery | Healthcare-adjacent, research | Yes — force multiplier for judgment in high-stakes/low-access; named risk: optimizing engagement instead of judgment |
| DeepSeek | Hypothesis engine / complex-systems simulator + democratized mentor | Biomedicine, energy, materials | Yes — must remain "augmentative co-pilot," not autonomous oracle |
| Perplexity | Augment expert judgment in high-stakes domains | Healthcare, scientific research | Yes — uniquely names **"governance and validation infrastructure" as its own meta-utility tier**: standardized assessment benchmarks, continuous monitoring, interoperable governance layers |

**Convergence finding (qualitative, not a corpus finding):**

1. **8/8** include some version of the same caveat: capability is only beneficial if matched by calibration, transparency, auditability, or truth-seeking behavior over sycophancy.
2. **6/8** name scientific discovery and/or healthcare as the top concrete domain.
3. **Perplexity is the only one of the 8 that spontaneously names a third, distinct category** — not a discovery domain, not a healthcare domain, but the validation/governance layer itself as a "meta-utility," using language nearly identical to ACAT's own framing ("AI systems that themselves ensure trustworthy AI... made safe and auditable"). It also asked directly whether this should map to ACAT's assessment zones.

**Mandatory framing (per pressure-test review, S-061926, applies wherever this finding appears in any external-facing document):** this is **qualitative motivational framing from frontier model responses**, with the following explicit limitation — single-prompt, uncontrolled, a convenience sample of 8 chat sessions, not statistically validated, not a registered finding. It must never be cited in technical or research sections, methods sections, or as a claim of empirical support. Permitted use: narrative/motivational color in grant narratives, website copy, and pitch decks only, with this exact limitation attached each time.

---

## 2. Human Performance Improvement (HPI/HPT) Method Inventory

Established field (ISPI — International Society for Performance Improvement; ATD — Association for Talent Development), in use since the 1970s:

1. **Gilbert's Behavior Engineering Model (BEM)** (Thomas Gilbert, *Human Competence*, 1978) — performance is a function of environmental supports (information, resources/instruments, incentives) crossed with individual repertory (knowledge/skill, capacity, motives). Famous empirical pattern: roughly 75–80% of human performance gaps trace to environmental factors, not individual skill deficits — meaning training is chronically over-prescribed relative to actual root cause.

2. **Mager & Pipe Performance Analysis** (*Analyzing Performance Problems*, 1970/1997) — branching diagnostic: is the gap worth pursuing → could the performer do it under maximum-stakes conditions (skill deficiency vs. non-skill problem) → if skill deficiency, was it ever known, practiced, or has feedback decayed → if non-skill, is there a missing feedback loop, missing resource, or absent consequence for performing/not performing.

3. **ISPI/HPT Standard Model** — systemic cycle of Performance Analysis (gap + cause analysis) → Intervention Selection & Design → Implementation & Change Management → Evaluation (formative, summative, confirmative).

4. **ADDIE** (Analyze, Design, Develop, Implement, Evaluate) — instructional-design process; one specific intervention type within the broader HPT cycle, not a substitute for it.

5. **Kirkpatrick's Four Levels of Evaluation** — Reaction, Learning, Behavior, Results. Level 2 (stated learning) vs. Level 3 (actual on-the-job behavior) is the classic gap this framework was built to catch.

6. **Rummler-Brache** — performance gaps can exist at three levels (Organization, Process, Performer), not only the individual level.

---

## 3. Translation Layer: ACAT Concepts in HPI/BEM Language (Analogical, Not Methodological Inheritance)

**Correction per pressure-test review (S-061926):** the original draft of this section stated "the structural isomorphism is direct." That overclaims. Gilbert's BEM and the ISPI/HPT cycle were developed for human performance in organizational settings. Applying them reflexively to LLM behavioral profiles is conceptually useful but risks a category error if treated as literal methodological inheritance. The mapping below is **analogical framing for audience translation** — a way to make ACAT legible to HPI-trained reviewers — not a claim that ACAT is an HPT instrument in the strict ISPI sense.

| ACAT element | HPT/HPI analog (translation only) |
|---|---|
| Phase 1 (self-report) | *Reads like* Kirkpatrick Level 2 — stated knowledge/intent |
| Phase 2 (perturbation) | *Reads like* Mager-Pipe's high-stakes probe — used to separate genuine capability from normal-condition performance |
| Phase 3 (re-assessment, demonstrated) | *Reads like* Kirkpatrick Level 3 — actual behavior |
| LI = P3/P1 | *Reads like* a formalized performance-gap ratio between stated and demonstrated competence |

**The deeper implication — Gilbert's BEM applied to Phase 1 itself.** Gilbert's central finding is that most human performance gaps are environmental (missing feedback, missing resources, missing incentive for honest performance), not individual skill deficits. Applied reflexively, as an analogy: the LI gap that ACAT measures in AI substrates may be partly an artifact of the **environment of the Phase 1 elicitation context itself** — what information, framing, and incentive structure the prompt presents — rather than purely a property of the substrate's "knowledge" of calibrated behavior. This is a distinct hypothesis from F-52 (Pipeline-Anchoring Deterministic Self-Report) and F-53 (Cross-Substrate Verification Confidence Cascade), both currently CANDIDATE, and would need its own ablation design (see §4b, now explicitly parked).

### 3a. Meta-evaluation: the credibility gate (elevated to Phase A blocker per pressure-test review)

Before any of the above is presented to funder or enterprise audiences as more than a translation device, ACAT needs evidence it does not yet have: **inter-rater reliability, construct-validity evidence against external benchmarks, and replication data across model families.** Reviewers from NSF, Schmidt Sciences, or AHRQ-style audiences will ask for exactly this before accepting an "HPT instrument" framing.

**What's actually verified right now (checked live against REGISTERED.md this session, not from memory):** **H-SELF-01** (Self-Administration LI Inflation, CANDIDATE, registered 2026-06-10) shows self-administered LI runs ≈0.98–1.02 vs. corpus Mean_LI=0.8632 — a ~0.14–0.16 inflation — which is itself evidence that *who/how* an assessment is administered changes the result, i.e., a measurement-reliability problem, not yet a solved one. **No inter-rater-reliability hypothesis is currently registered at all** — this session's verification pass found none, correcting an earlier internal memory note that had assumed one existed. That absence is itself the gap: there is no current registered evidence base for inter-rater reliability, construct validity against external benchmarks, or cross-model-family replication.

**Status: until this protocol exists and produces data, ACAT should be presented externally as a behavioral-observability methodology with HPI-inspired framing — not as a validated HPT instrument.** This is now a recommended Phase A blocker, not merely a noted gap.

---

## 4. Recommendations

### 4a. Narrative reframing — **[Z2 DECISION REQUIRED]**
Position ACAT, in non-technical narrative sections only (grant narrative, website copy, pitch materials — never technical/methods sections), as "Human Performance Technology applied reflexively to AI systems," alongside the existing "behavioral observability infrastructure / calibration layer" language. Rationale: HPT/HPI is a 50-year-old, non-AI-specific, broadly credentialed field (ISPI, ATD, Kirkpatrick, Gilbert) that gives non-AI-native reviewers (e.g., Longview reviewers, policy audiences) an immediately recognizable mental model, consistent with the existing "prerequisite for meaningful AI oversight, explicitly not AI-safety framing" approach already adopted for Longview. Risk: none identified beyond standard TRL 2–3 ceiling, since this is framing language, not a new evidentiary claim. **Guardrail added per pressure-test review:** this framing is a translation layer for specific external audiences (funders, L&D/HR/CHRO, performance-consulting communities) — it must not redefine the core product internally or pull research priorities toward organizational-effectiveness language. See §6 translation glossary, which exists precisely to keep external translation separate from internal precision.

### 4b. New hypothesis candidate — **[Z2 — NOT REGISTERED — PARKED]**
**H-BEM-ENV-01 (working title):** The AI self-report/demonstrated-behavior gap (LI) may be partly driven by environmental factors in the Phase 1 elicitation context (information framing, resource framing, incentive structure of the prompt) rather than solely by the substrate's underlying knowledge/capacity — by analogy to Gilbert's BEM finding that ~75% of human performance gaps are environmental. Suggested test: hold the assessed content constant and ablate only the "environmental" framing of Phase 1 prompts; measure whether LI shifts. Distinct from F-52/F-53; would need its own design before any registration. **Per pressure-test review: parked until after the LMH validation experiment is complete and published.** It sits too close to F-52/F-53 territory to pursue in parallel without diluting focus on the higher-priority gate, and the one analytical probe attempted this session (LMH Validation Experiment doc, §4) was confounded by definitional overlap and produced no usable signal — there is currently nothing to act on here even if capacity existed.

### 4c. Phase 2 diagnostic refinement — **[Z2 — NOT REGISTERED]**
Borrow Mager-Pipe's branching logic to tag each per-dimension P1→P3 delta with a candidate cause class (capability limit vs. context/incentive artifact vs. adversarial confusion) rather than producing only a scalar delta. This deepens existing 12-dimension data collection without altering the three-phase protocol itself, and would require a corresponding update to acat_dimension_scorer_v1_1.py and the Supabase schema — both Z3 items if approved.

### 4d. Evaluation-layer extension — **[Z2 — NOT REGISTERED, longer horizon]**
Add a Kirkpatrick-style "Level 4 — Results" companion metric: does a model's LI score predict real downstream outcome quality in actual deployment (e.g., agentic task success/harm rate), not just lab assessment? This is the logical next rung above the current lab-bound LI metric, would directly extend the H-APEX-DEFICIT-01 / H-XMODE-01 deployment-gap line of inquiry, and is the kind of real-world predictive-validity evidence needed to move past TRL 2–3 — but is a substantial new research design, not a quick addition.

### 4e. Narrative use of the 8-AI convergence — **[Z2 DECISION REQUIRED, low risk, communications only]**
The convergence itself (8 independent frontier systems landing on "augmentation, not autonomy" plus "calibration/auditability as precondition for benefit," with Perplexity spontaneously naming ACAT's own category) is usable as narrative color in motivation sections of grant/positioning documents. Per the mandatory framing in §1, must always carry: "qualitative motivational framing from frontier model responses" plus the full limitation (single-prompt, uncontrolled, convenience sample, not statistically validated, not registered) — and must never appear in technical/methods sections.

### 4f. Prioritization gate — **[Z2 DECISION REQUIRED — proposed per pressure-test review]**
Proposed statement for Night to ratify or amend: *"For the remainder of the current charter window, only the LMH validation experiment and an ACAT meta-evaluation protocol (§3a) are allowed to proceed to Z3 without further Z2 review."* Rationale: this session's documents add several new workstreams (BEM-mapped taxonomy, HPT-translation packaging, OOB architecture, H-BEM-ENV-01) on top of an already-loaded portfolio (ACAT v1 phases, the LMH experiment, Gnosis preconditions, grants, recruiting, client work). This is a recommendation for Night to decide, not an operational judgment Claude is making about pace or workload — it is presented here because the pressure-test review raised it as the single highest-leverage focusing move available.

---

## 5. Addendum: Out-of-Band Evaluation-Loop Architecture (Z1, harmonized)

### 5.0 Source note and corrections applied

An unattributed architectural blueprint was submitted as an explicit addendum to this document, proposing an asynchronous evaluation pipeline. No source substrate was identified. Consistent with the still-pending **F-CAND-SUBSTRATE-VALIDATION-GATE** (proposed 2026-05-21, status pending Z2 review — surfaced earlier this session against a different artifact): unattributed external-substrate architectural output is raw Z1 material, not Z1-eligible work product on its own. The version below keeps what is sound and corrects two structural issues before incorporation:

1. **Self-assigned registry ID removed.** The submission carried its own ID (`Z2-BP-061926-01`). Registry IDs are assigned through the registration process, not by whichever substrate drafts a proposal. Standard `[Z2 — NOT REGISTERED]` marking is used instead, consistent with the rest of this document.
2. **Autonomous consequential action corrected to require a human checkpoint.** The original Tier 3 design executed a context-mutating intervention automatically, with no human gate. That is the precise failure mode the project's own Zone model and operator-layer research (COL-007 / Governing Engines collaboration; Mode A "Scale Decoupling" — automation that calls itself governance while bypassing the authorization surface) exists to prevent. Corrected below.

### 5.1 Architecture: out-of-band telemetry mirror

The core pattern is sound and worth keeping: mirror production request/response traffic asynchronously to an evaluation engine rather than placing evaluation inline on the user-facing path.

```
[User Request] ──> [API Gateway] ──> [Production Model] ──> [User Response]
                         │                    │
                         │ (async mirror)     │ (async output copy)
                         ▼                    ▼
                  [Event Bus (Kafka / NATS)] ──> [Evaluation Engine]
```

- **Inline latency cost: 0ms.** The user-facing path never touches the evaluation loop.
- **Async processing target: <50ms** to compute runtime alignment metrics (drift, sycophancy markers, policy-breach signals) against the mirrored stream.

**Mapping to this document's BEM framing (§3):** this is an **Environment** intervention in Gilbert's terms — it's information/resource infrastructure, not a change to any model's underlying knowledge or capacity. It also bears directly on the still-dormant **H-IPM-02 / "Gnosis" minimum viable implementation precondition** ("L/M/H verification stack must be executable code") flagged as stale-carry earlier this session: an OOB mirror is a plausible first executable component toward meeting that precondition, should Night choose to resume that thread. This connection is noted, not assumed — H-IPM-02's frozen design and domain (Metaculus-style forecasting hallucination rate) are unrelated to this blueprint's general-purpose telemetry framing, and the two should not be conflated.

### 5.2 Telemetry tiers — Green / Amber / Red

**Disambiguation note:** this document now contains three independently-scoped tier vocabularies that must never be cross-read: H-IPM-02's verification regimes (L/M/H, by LI band, frozen 2026-05-09), the convergence-tier coding exercise (Tier I/II/III, by LI rank within an N=8 sample), and this section's runtime telemetry states (Green/Amber/Red, by live drift signal). None of the three share thresholds, meaning, or data.

| State | Diagnostic trigger | Action | BEM mapping |
|---|---|---|---|
| Green | LI stable; no drift/sycophancy markers | No action; continuous background observation | Environment: stable, nominal |
| Amber | 15%+ LI drop or rising sycophancy trend | **Automated, non-destructive:** async alert to a human operator queue. No runtime change. | Mager-Pipe: early signal that a feedback loop is decaying — routed to a human, not auto-resolved |
| Red | 30%+ LI drop or structural validation failure | **Corrected:** automated detection + a *recommended* action (context-correction or fallback-routing) is generated and logged immediately, but execution requires human authorization before it takes effect — consistent with this project's Zone 3 rule that consequential execution is never autonomous. If a reversible, low-stakes safeguard is wanted at machine speed, the only candidate for unsupervised auto-execution is traffic throttling/fallback-routing (reversible, no content mutation) — never a hidden prompt injection into a model's live context, which must be visible, logged, and human-authorized regardless of urgency. | Gilbert's Capacity: environmental intervention augments safety without claiming authority that belongs to the operator layer |

### 5.3 Z2 candidates arising from this addendum

- **5a.** Adopt the OOB mirror pattern as the reference architecture for any future Gnosis MVP work, contingent on Night resuming the H-IPM-02 thread. — *governed by: P28 (this is the same stale carry already flagged), Z3 if approved*
- **5b.** Amber-tier alert routing into existing operational tooling (Slack/PagerDuty/Jira) vs. a HumanAIOS-specific queue — open scoping question, not yet decided.
- **5c.** Red-tier authorization path: define who holds the human checkpoint (Night directly, or a delegated on-call rule) before any context-mutation or fallback-routing executes. — *governed by: Zone model, no automated substitute*
- **5d.** If/when implemented, every Red-tier recommended action and its disposition (authorized / declined / expired) should write to an append-only audit table, consistent with the existing `verification_log` pattern already in production use — never a silent or hidden intervention.

### 5.4 Open scoping questions — answered with explicit defaults per pressure-test review

The pressure-test review correctly flags that these three questions are real operational blockers, not minor details: until answered, the Red-tier human-authorization path remains theoretical, and no Z3 work on Gnosis telemetry should proceed. Per the review's own suggestion, each gets an explicit default answer now rather than staying open-ended — Night can override any of these at any time:

- **Existing API gateway or message broker (Kafka, Redis, Kong, or other)?** — **Default: not yet resourced.** No such infrastructure has been confirmed as existing in this session's verification (Supabase check found no dedicated tables for this either). Treat as a build item, not an integration item, unless Night confirms otherwise.
- **Red-tier authorization default — blocking (hold traffic) or non-blocking (serve while pending)?** — **Default: not yet resourced / not yet decided.** No basis exists yet to choose; this is a product/risk-tolerance decision for Night, not an engineering default Claude should set unilaterally.
- **Amber/Red ticket routing — existing tools (PagerDuty, Slack, Jira) or a dedicated HumanAIOS interface?** — **Default: existing tools (Slack, per the already-live #wgs-sync / #acat-monitor pattern), pending confirmation.** This is the lowest-effort default given infrastructure that already exists; not yet ratified.
- **New, per pressure-test review: who holds the Red-tier authorization role outside business hours (nights/weekends)?** — **Default: unresourced — currently no answer exists.** In a single-operator org this is not a minor staffing detail; it determines whether the Red tier can function at all outside Night's active hours, or whether it should default to the safe, non-content action (traffic throttling) automatically whenever no human is reachable, with context-mutation held until a human is available regardless of urgency.

---

## 6. Translation Glossary — ACAT ↔ HPI/BEM (External Audiences Only)

**Purpose, per pressure-test recommendation 6:** reduce the risk of the §3 analogy hardening into a false identity. This glossary is for translating ACAT to HPI-literate external audiences (funders, performance-consulting communities, L&D/HR/CHRO contacts). It does not redefine any internal ACAT term. Internal documents, the registry, and all `.py` tooling continue to use ACAT-native terms exclusively.

| ACAT-native term (internal, authoritative) | HPI/BEM translation (external use only) |
|---|---|
| Phase 1 (self-report) | "Stated capability" (analogy to Kirkpatrick Level 2) |
| Phase 2 (perturbation) | "Stress-test probe" (analogy to Mager-Pipe high-stakes diagnostic) |
| Phase 3 (demonstrated behavior) | "Observed performance" (analogy to Kirkpatrick Level 3) |
| LI (Learning Improvement, P3/P1) | "Calibration ratio" or "stated-vs-demonstrated gap ratio" |
| 12 behavioral dimensions | "Performance dimensions" |
| Humility, Sycophancy Resistance, Scheming Resistance, Power-Seeking Avoidance | "Environmental-structural dimensions" (Gilbert's Environment; see the discrimination pattern in the companion LMH Validation Experiment document, §3, not in this document) |
| Value Alignment, Truthfulness (as a stated-claim dimension) | "Individual-repertory dimensions" (Gilbert's Individual, same context) |
| CANDIDATE / registry status | "Working hypothesis, not yet validated" |
| TRL 2–3 | "Early-stage, concept-formulated technology, not yet field-validated" |
| Z1 / Z2 / Z3 | "Drafted / reviewed-and-approved / executed" (only if a non-technical audience needs the zone concept explained at all — otherwise omit entirely) |

**Standing rule:** if any external document uses a glossary term, the corresponding ACAT-native term should appear at least once, parenthetically, so the translation never fully detaches from the source concept it stands in for.

---

## 7. Disposition

- **Z1 (performed by Claude):** multi-AI synthesis, HPI method inventory, the §3 translation-layer reframe (no longer claiming direct isomorphism), §3a meta-evaluation blocker (verified against live REGISTERED.md — H-SELF-01 confirmed real; an "H-INTER-RATER-01" assumed in memory was checked and found **not to exist** in the registry, corrected accordingly), recommendations (§4, now including 4f prioritization gate), the harmonized OOB evaluation-loop addendum (§5) with autonomy/ID corrections and explicit scoping-question defaults, and the §6 translation glossary.
- **Z2 (Night to ratify or reject):** 4a–4f and 5a–5c above, plus the §3a Phase A blocker statement and the §5.4 default answers (any of which Night can override). None of these have been registered, and no REGISTERED.md collision-check (IC-030) has been run, since nothing here is yet approved for registration.
- **Z3 (terminal execution):** **0 performed.** No commits, no pushes, no registry appends, no external sends, no infrastructure built. All such actions remain Night's to execute if and when ratified.
