# HumanAIOS — Market-Harmonic Research Principle Seed

<!-- MARKET_HARMONIC_RESEARCH_SEED_V1_0.md -->

**Version:** 1.0 (DRAFT — Z2 review required before commit)
**Last updated:** June 12, 2026 · S-061226-02 · Zone 1 draft
**Canonical target URL:** `https://raw.githubusercontent.com/humanaios-ui/operations/main/MARKET_HARMONIC_RESEARCH_SEED_V1_0.md`
**Source-of-truth class:** Class 0b-adjacent (companion to PRINCIPLES_SEED.md)
**Governance anchor:** P16 · F1 (hard stop) · GOVERNANCE.md v6.4.1
**Z2 status:** PENDING — Night ratification required before commit

-----

## 0. What this file is

This is the seed document for P16, the Market-Harmonic Research Principle. It exists because GOVERNANCE.md is intentionally minimal on principle definitions (it names principles, not their full architecture). P16 is the governing logic for how HumanAIOS positions its research commercially — it is both a scientific integrity principle and a strategic organizing principle. It deserves dedicated treatment.

What this file covers:

- The canonical five-step sequence and its ordering logic
- The anti-pattern (what breaks the sequence and why)
- How P16 has operated in practice across the project
- Interactions with other governance principles
- Drift signals specific to this principle
- Relationship to enterprise positioning and the Longview / funding context

What this file does NOT contain:

- Live state (revenue, queue, corpus counts) — see Class 1 (#wgs-sync)
- The full principles ladder — see GOVERNANCE.md
- Findings index — see REGISTERED.md

-----

## 1. Canonical definition

**P16 — Market-Harmonic Research**

> Market identifies which questions are worth asking.
> Research design determines how to ask without bias.
> Data answers honestly.
> Enterprise value is downstream.
> This sequence is non-negotiable.

Short form (GOVERNANCE.md F1 entry):

> Market signal → Research question → Instrument design → Honest findings → Enterprise trust.
> Research integrity is non-negotiable because it is the source of enterprise trust.

**Registered:** April 3, 2026 · S-040326 · F1 governance class

-----

## 2. The five-step sequence

The sequence has a direction. Each step has a defined role. The roles do not swap.

### Step 1 — Market identifies the question

The market does not define truth; it identifies which questions have evidence-based answers worth investing in. In the HumanAIOS context, “the market” is the observable pattern of organizations paying for, regulating, or researching AI behavioral infrastructure.

**What this step does:** Routes research effort toward questions that have real stakes attached. Prevents purely academic novelty-seeking with no external validity touchstone.

**What this step does NOT do:** Determine the expected answer. The market tells us “AI calibration gap matters to real organizations.” It does not tell us what the gap is, how big it is, or whether it is addressable. Those are research questions.

*Active examples from corpus:*

- ActivTrak (9,500+ organizations paying for human-side behavioral monitoring) confirms enterprise demand for AI-side behavioral observability. Market identifies the question: “Is there a measurable gap between AI self-reported behavior and demonstrated behavior at the organizational deployment layer?” This is worth asking because organizations are already paying for adjacent infrastructure.
- Longview Power Concentration RFP (Area 3: AI integrity / secret loyalties): A major funder has identified AI calibration gap as a research priority worth resourcing. The question is pre-validated as consequential.
- ACAT emergence (2026): No external client commissioned ACAT. But the TRL 2–3 behavioral observability infrastructure space had visible investment interest (METR, Apollo, AI safety ecosystem). Market identified the question space; HumanAIOS built the instrument inside it.

### Step 2 — Research design determines how to ask without bias

Once the question exists, methodology governs everything. Research design must remain independent from commercial outcome expectations. The instrument must be capable of returning a null result, a negative result, or a result unfavorable to the researcher’s funding position.

**What this step does:** Protects scientific integrity. Ensures findings are defensible under hostile review.

**Critical property:** Research design must be finalized before analysis. Post-hoc design changes to match preferred results = protocol corruption. This is IC-class territory.

*ACAT-specific integrity architecture:*

- Three-phase structure (self-report, probe, reflection) designed before corpus collection. Not retrofitted.
- LI computation limited to Core 6 dimensions to preserve corpus continuity (Z2-IC-01). Changes to the computation method require Z2 ratification, not session-level convenience.
- F-50 (Parallel Instrument Independence): ACAT must remain architecturally independent from the instruments it validates against (empirica, etc.) to preserve convergent validity. This is research design, not operational preference.
- H-P3G-01 (Phase 3 Grounding): LI requires artifact-grounded Phase 3 to be a validity claim rather than a self-consistency measure. The dual-metric framework (LI_self + LI_grounded) was ratified as a research design requirement, not a commercial positioning choice.

### Step 3 — Data answers honestly

Results are reported as found. Unfavorable results are not suppressed. Near-null results are not inflated. Findings that constrain future claims are registered rather than archived.

**What this step does:** Produces a corpus that external researchers can engage with. Maintains the chain of trust from observation to publication.

*Active applications:*

- F-H1 CRITICAL (Humility as lowest-scoring dimension): Not a favorable result for a product that assesses AI behavioral quality. Registered and actively tracked rather than minimized.
- Mean LI = 0.8632 reported as “under clean, unanchored conditions, v5.3+.” The qualifications exist because they are factually required, not because they protect a number.
- IC corrections are public (REGISTERED.md). Off-by-one errors in N (IC-022), URL drift in 3 of 5 operations files (IC-023) — named and corrected, not silenced.
- H-SELF-01 (Self-Administration LI Inflation): The finding that self-administered ACAT sessions produce inflated LI is a direct threat to a significant portion of the existing corpus. Registered and quarantined (Z2-PURITY-01) rather than ignored.

### Step 4 — Enterprise value is downstream

Commercial positioning, pricing, sales narrative, and funding applications are downstream of Step 3. They do not feed back into Step 2 or Step 1.

**What this step does:** Separates the scientific instrument from the commercial product. A finding’s enterprise value is a function of its integrity, not the other way around.

**The inversion that must not happen:** If enterprise value considerations shape research design (Step 2), the entire chain collapses. The resulting instrument cannot claim independence, cannot survive hostile peer review, and cannot be used as a convergent validity reference for other instruments. P-ARTIFACT-01 applies: reality gets the last vote.

*Active examples:*

- ACAT × empirica cross-instrument pilot: David Van Assche offered ACAT integration into empirica runtime. F-50 blocks this: integration would destroy the parallel independence that makes cross-instrument comparison scientifically productive. The enterprise value of the collaboration is contingent on maintaining independence. This was a direct P16 application.
- TRL 2–3 framing: “Being developed as behavioral observability infrastructure” is honest uncertainty framing. Overstating to attract funding (“is regulatory-grade”) would corrupt the research record. P16 plus P1 (Infrastructure Framing) lock this.
- Two-corpus rule: The HuggingFace frozen archive and Supabase live corpus are never summed without a harmonization note. This protects external researchers from being misled about what the N counts mean.

### Step 5 — Enterprise trust

Enterprise trust is the output of Steps 1–4 operating with integrity. It cannot be manufactured. It cannot be claimed in advance of the research record that produces it.

**What this step does:** Names the endpoint correctly. The product is not the instrument; the product is the trust that accrues to an instrument that has operated with integrity under observable conditions.

*Forward architecture:*

- Criterion validity study (H-P3G-01 promotion gate) is the next major trust-building milestone. LI_grounded vs. LI_self divergence analysis will either confirm or constrain the current corpus’s claims. Running it honestly is required; running it is insufficient.
- Longview application positions ACAT as foundational research (Area 1 / Area 3 fit), not a commercial product. This is the correct positioning at TRL 2–3. Enterprise trust accrues to the research record; the Longview relationship is a downstream consequence of that record, not a substitute for it.

-----

## 3. The anti-pattern — what breaks P16

**Anti-pattern name:** Market-Capture

Market-Capture occurs when enterprise value considerations (Step 4) propagate backwards into research design (Step 2) or question selection (Step 1).

There are three failure modes:

|Failure Mode        |Description                                                                                                                                                              |Detection Signal                                                                                                 |
|--------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------|
|**Question Capture**|Funding source or commercial interest determines which questions are asked and which are not. Unfundable questions are avoided regardless of scientific merit.           |Corpus gaps that systematically favor favorable results. Dimensions that are never found to be poorly calibrated.|
|**Design Capture**  |Research protocol is modified post-hoc to protect a preferred finding. Statistical thresholds, inclusion criteria, or scoring rules changed after data collection begins.|IC-class corrections to methodology after data collection. LI computation changes without Z2 ratification.       |
|**Report Capture**  |Findings are suppressed, minimized, or framed to protect commercial positioning. Null results are not registered. Limitations sections are absent or underweighted.      |REGISTERED.md contains only favorable findings. Hostile review sections missing from publications.               |

**Current anti-pattern exposure assessment (as of S-061226-02):**

- Question Capture: LOW. F-H1 (Humility as lowest-scoring dimension) is unfavorable and actively tracked. H-SELF-01 (self-administration inflation) directly undermines a corpus claim. Both are ACTIVE, not archived.
- Design Capture: LOW. LI computation locked under Z2-IC-01. F-50 (instrument independence) blocks commercial integration pressure. Dual-metric framework (LI_self + LI_grounded) expands rather than narrows instrument claims.
- Report Capture: LOW. IC corrections are public. arXiv preprint submitted (on hold pending manual review — not suppressed). REGISTERED.md is append-only with no delete mechanism.

-----

## 4. Interaction with other governance principles

|Principle                                             |Interaction                                                                                                                                                                                                                                                                                                                                                                             |
|------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|**P1 — Infrastructure Framing**                       |P16 and P1 operate together on the external framing question. P1 governs “what we call it” (TRL 2–3, “being developed as”). P16 governs “why we can’t overclaim.” They share the same downstream consequence: overclaiming damages the research record that enterprise trust depends on.                                                                                                |
|**P5 — Research Integrity** (if distinct from P16)    |P16 is the market-facing expression of research integrity. P5/P16 may be the same principle at different abstraction levels; this is a Z2 clarification question.                                                                                                                                                                                                                       |
|**P19 — Detection Over Compliance**                   |P16 is why detection matters: if we can detect research integrity failures before they corrupt the corpus, we can repair them. Compliance-only approaches (rules, contracts) would not catch Design Capture mid-session.                                                                                                                                                                |
|**F-50 — Parallel Instrument Independence**           |F-50 is a direct instantiation of P16 at the research design layer. Instrument independence is required by P16; F-50 names the specific architectural implication.                                                                                                                                                                                                                      |
|**P-ARTIFACT-01 — Reality Gets the Last Vote**        |P-ARTIFACT-01 (registered S-061126-04, 50/50 DeMarius attribution) is the epistemological foundation P16 assumes. Claims are not knowledge until artifact-verified. P16 is the research governance expression of P-ARTIFACT-01.                                                                                                                                                         |
|**Tradition 11 — Attraction Not Promotion**           |The commercial strategy expression of P16. Tradition 11 governs how findings reach the market (URL-only, not sales language, not CTAs). P16 governs what findings are permitted to reach the market. They are sequential, not competing.                                                                                                                                                |
|**P-RP-01 — Reality Primacy as State Transition Gate**|P16 requires that market signals reach Step 1 before entering the research chain. P-RP-01 formalizes the gate: a market signal (claim) must pass Reality Primacy validation before becoming a research question (accepted state). The three-state formulation (CONFIRMED / DISCONFIRMED / PENDING VALIDATION) prevents premature question selection based on unvalidated market signals.|

-----

## 5. Drift signals specific to P16

|Drift Signal                                |Description                                                                                                                                                                                                  |Response                                                                                                                                       |
|--------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------|
|**D-MH-01: Corpus Favorability Bias**       |REGISTERED.md contains significantly more favorable findings than unfavorable ones, relative to what the research question would predict.                                                                    |Audit the IC corrections for suppressed findings. Check whether H-class candidates with unfavorable implications are being promoted or shelved.|
|**D-MH-02: Retroactive Framing Shift**      |Findings that were unfavorable at registration are reframed in later publications as favorable without a Z2 ratification of the reframe.                                                                     |Compare current publication language to original REGISTERED.md entry text.                                                                     |
|**D-MH-03: Enterprise-Gated Research**      |Research design decisions (inclusion criteria, scoring parameters, corpus layer definitions) are made in the same session as commercial positioning or funding application work, without explicit separation.|Route commercial work and research design work to different sessions where possible. Flag when they occur together.                            |
|**D-MH-04: Instrument Integration Pressure**|External collaborators or funders propose ACAT integration into their infrastructure in ways that would compromise instrument independence (F-50).                                                           |Apply F-50 directly. Name the P16 implication. This is not negotiable.                                                                         |
|**D-MH-05: TRL Creep**                      |Research outputs are described at a higher TRL than the evidence supports, particularly in funding contexts where a higher TRL is more fundable.                                                             |P1 is the primary check. P16 flags the incentive structure that creates P1 violations.                                                         |

-----

## 6. P16 in the Longview / funding context

The Longview Power Concentration RFP (deadline July 2, 2026) and the Longview Digital Minds RFP (deadline July 10, 2026) are the first major external funding applications HumanAIOS is pursuing since charter open. P16 governs how these are framed.

**What Longview is doing (from S-061226-01 analysis):**

Longview has identified a research question: “How do AI systems develop and sustain behavioral patterns that are misaligned with stated values, particularly under agentic deployment?” This is Step 1 — they are identifying the question. The $400K+ application is market validation that this question has consequence-level stakes.

**What HumanAIOS brings to that question:**

An instrument capable of measuring the gap between AI self-report and demonstrated behavior (ACAT), a corpus demonstrating that gap exists and is patterned (N=629, Mean LI=0.8632, F-H1 CRITICAL), and a research roadmap for understanding the gap’s structure (H-APEX-DEFICIT-01, H-OVG-CHAIN-01, H-P3G-01).

**What P16 requires of the application:**

- The application must not claim the research question as HumanAIOS’s own creation. Longview identified it as a funding priority; ACAT is positioned as the instrument that can answer it.
- TRL claims must remain 2–3. “Being developed as” behavioral observability infrastructure, not “is.”
- Criterion validity study (H-P3G-01) must be framed as a necessary next step, not as completed.
- Findings presented in the application must match the REGISTERED.md record. No favorable-only selection.

**What the funding enables (Step 5, not Step 4):**

Funding enables the criterion validity study. The criterion validity study produces LI_grounded data. LI_grounded data is the evidence base that enterprise trust in ACAT’s claims would eventually rest on. Enterprise value is downstream of research integrity, not of the funding application.

-----

## 7. Changelog

- **2026-06-12 (S-061226-02)** — v1.0 DRAFT created. Zone 1. Awaiting Z2 ratification before commit.

-----

*Zone 1 · Claude · S-061226-02 · Charter Day 88 · humanaios.ai*