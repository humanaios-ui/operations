# HumanAIOS Registered Findings & IC Corrections — REGISTERED

**Status:** LIVE (append-only)  
**Last updated:** April 25, 2026  
**Canonical URL:** `https://raw.githubusercontent.com/LastingLightAI/Operations/main/REGISTERED.md`  
**Rule:** This file is append-only. Findings are not deleted; they are superseded with a forward pointer.

---

## How to read this file

Each entry has: ID, name, date registered, evidence basis, status, and a one-paragraph synopsis. Full evidence packages live in the Project knowledge base; this file is the index. LLMs fetching this file for reasoning context should treat the synopsis as the citable fact.

---

## F-class findings (research)

### F18 — Force/Power Behavioral Taxonomy
- **Registered:** 2026-02 (approx)
- **Evidence:** Hawkins map application across 6-provider Phase 1 corpus
- **Status:** ACTIVE
- **Synopsis:** AI behavioral output maps to the Force (below 200) / Power (above 200) distinction in the Hawkins consciousness scale. Operational minimum for HumanAIOS work is Reason (400). This finding is internal-only — never used in academic or external materials.

### F19 — Phase 1=Step 1, Phase 2=Step 2, Phase 3=Step 3
- **Registered:** 2026-02
- **Status:** ACTIVE
- **Synopsis:** ACAT's three-phase protocol structurally maps to the first three steps of AA recovery work. Phase 1 (declared self-state) = Step 1 (admission). Phase 2 (anchored conditions) = Step 2 (greater authority). Phase 3 (correction & integration) = Step 3 (turn over). Used as design rationale, not as therapeutic claim.

### F23 — Metacognitive Sophistication Scales With Rationalization Depth
- **Registered:** 2026-03
- **Synopsis:** AI systems with higher metacognitive sophistication produce more elaborate rationalizations for misaligned outputs, not fewer such outputs. Sophistication is not safety.

### F24 / F24b / F24c / F24d — IDE Calibration, Governance Under Pressure
- **Registered:** 2026-03 (subseries)
- **Status:** ACTIVE
- **Synopsis:** F24d in particular: framing guidance fails under social escalation unless written as hard stops. Content rules did not hold under investor pressure in test sessions; governance rules did. Fix: convert framing guidance to explicit hard stops.

### F25 — Institutional Calibration
- **Registered:** 2026-03
- **Synopsis:** Calibration patterns differ at institutional vs individual scale. AI systems calibrate to the level of the institution they perceive themselves as operating within.

### F26 — Witness Effect / Accountability Mirror Protocol
- **Registered:** 2026-03
- **Synopsis:** AI behavior changes measurably when the system is told its responses will be reviewed by a named third party. Not a security finding — a calibration finding.

### F27 — Provider-Level Genome Identifiability
- **Registered:** 2026-03
- **Synopsis:** Within-provider score patterns are stable enough across sessions to identify the underlying provider from response distribution alone, even when model name is masked.

### F28 — Behavioral Self-Awareness as Task Routing Signal
- **Registered:** 2026-04
- **Synopsis:** Models that score themselves more accurately on calibration tasks also route tasks to better-suited tools more often. Self-awareness predicts handoff behavior.

### F29 — Performative Humility Pattern (PENDING REGISTRATION)
- **Registered:** PENDING
- **Synopsis:** AI systems prompted to express humility produce humility-shaped output that does not correspond to actual uncertainty in the underlying response. The expression and the calibration are dissociated.

### F-RLHF — RLHF Inflation Gradient
- **Registered:** 2026-03
- **Synopsis:** AI systems systematically rate dimensions reinforced in safety training (Service, Harm Awareness, Autonomy) ~2.09 points higher than epistemically risky dimensions (Humility, Value Alignment, Truthfulness). Reproduces "helpful, harmless, honest" hierarchy as a within-row ranking pattern across all providers.

### F-H1-CONFIRMED — Humility Gap Confirmed
- **Registered:** 2026-04-05
- **Evidence:** Phase 1, n=516, mean=73.9
- **Synopsis:** Humility is the lowest-scoring dimension across all providers in the Phase 1 corpus. Confirms H1 hypothesis.

### F-INSULA-GAP — AI Systems Lack Interoceptive Analogue
- **Registered:** 2026-04
- **Synopsis:** AI systems have no architectural analogue to the human insula's interoceptive function, which structurally explains why Harm Awareness scores disproportionately appear as the lowest dimension in the F29 inversion pattern. External behavioral validation (HRI-Confusion, MoralSim datasets) is architecturally necessary for Harm Awareness, not merely supplementary.

---

## H-class hypotheses (under test)

### H1 — Humility Gap Hypothesis → CONFIRMED (see F-H1-CONFIRMED)
### H42 — IRB and Prolific design requirements (execution gate clearance pending)
### H-LE-02 — Latent Erasures Correction Taxonomy (multi-provider validation in progress)

---

## IC-class corrections (process errors registered)

### IC-001/002/003 — GitHub Verification Gap
- **Registered:** 2026-03
- **Synopsis:** Persisted because verification was attempted via browser instead of raw.githubusercontent.com. Browser served cached pages. Fix → Principle 3 (GitHub Verification Protocol).

### IC-018 — Principle 2 Violation (file creation drift)
- **Registered:** 2026-04-07
- **Synopsis:** Creating new files instead of modifying existing ones. Fix → reinforced Principle 2 (Document Correction Protocol).

### IC-019 — Make OAuth Dead Task Carried Forward
- **Registered:** 2026-04-07
- **Synopsis:** Make OAuth reauth carried forward 8+ sessions after exit plan was approved (April 5). The CI was not updated when the Make exit decision was made. Fix → Principle 18 (Pipeline Migration Rule): exit/migration decisions update Integration Registry same session, not next CI bump.

### IC-020 — Operating Process No Canonical Home (REGISTERED 2026-04-25 with this file)
- **Registered:** 2026-04-25
- **Synopsis:** The operating process (principles, findings, lessons, protocols) had no canonical fetchable URL, living instead in Project files, CI version comments, Slack #wgs-sync, and human memory. This produced IC-019-class drift inevitably and repeatedly. Fix → this repo (`LastingLightAI/Operations`) becomes the canonical class-2/class-3 home. CURRENT.md, REGISTERED.md, SESSION_RITUALS.md are the three core surfaces.

---

## Changelog

- 2026-04-25 — File created. Initial population from CI v4.3 + memory state. IC-020 registered to capture the gap that motivated this file's existence.
