# LONGVIEW DIGITAL MINDS RFP — APPLICATION DRAFT (companion to the Power Concentration app)

**Document status:** Zone 1 draft · Z2 required before any external send
**Session:** S-070126 (Claude Z1)
**Deadline:** July 10, 2026 · **Secondary application** (Power Concentration is primary — submit that first; use the extra days to sharpen this)
**Application URL:** https://www.longview.org/request-for-proposals-research-and-applied-work-on-digital-minds/
**Contact:** digitalminds-rfp@longview.org
**Track:** Grants — typical range $50K–$2M
**Applicant:** HumanAIOS LLC · FL Doc #L26000155266 · EIN 41-5367995
**PI:** Carly R. Anderson · aioshuman@gmail.com · (448) 243-3992 · ORCID 0009-0003-7540-4245

-----

## GOVERNANCE GATES BEFORE SUBMISSION

- [ ] Z2 ratification by Night (full draft review)
- [ ] P-ANON check: confirm Governing Engines / DeMarius J. Lawson self-attributed publicly before naming
- [ ] arXiv hold status — cite preprint if the hold clears before July 10; else "manuscript under review"
- [ ] **Overclaim review — the field's failure mode is both directions:** confirm no sentence implies HumanAIOS detects sentience/consciousness OR that it forecloses AI moral status. Agnosticism is the credibility anchor.
- [ ] Disclosure discipline: interoceptive/architecture finding stays in neuroscience framing (no esoteric-framework labels externally)
- [ ] Zone 3 submission by Night at terminal

-----

## APPLICATION DRAFT

### Project Title

Measuring the Reliability of AI Self-Report and the Architecture of Possible Experience: Behavioral Infrastructure for Digital-Minds Research

-----

### One-Sentence Summary

Digital-minds research increasingly asks AI systems about their own internal states — but whether those self-reports are *reliable* is itself unmeasured; HumanAIOS contributes behavioral-measurement infrastructure that (1) quantifies how far AI self-report diverges from demonstrated behavior at corpus scale, and (2) surfaces architecture-grounded evidence about which experiential capacities current AI systems structurally lack — while remaining rigorously agnostic on moral status itself.

-----

### Primary Area

**Sentience and consciousness research** — the RFP names as a key gap "research on what features correlate with sentience and to what extent AI systems possess these features," and "what would cause conscious AI systems to have valenced … experiences." This project addresses both from the measurement side.

### Secondary Area

**Moral status and AI welfare** — as a *methodological* contribution: a reliability substrate for any assessment that draws on AI reports about their own states.

-----

### Problem Statement

The digital-minds field's evidence base leans on two substrates whose reliability is largely untested. The first is **AI self-report** — what a system says when asked whether it has preferences, whether an interaction was aversive, what it "wants." The second is **behavioral and capability intuition**. Welfare-relevant conclusions are increasingly drawn from the first: model-welfare interviews, introspective probes, stated-preference elicitation.

But there is a prior question no one has measured at scale: *when an AI system reports on its own dispositions, how well does that report track what the system actually does?* If introspective access is systematically miscalibrated, then every welfare or sentience assessment that trusts AI self-report inherits that miscalibration — and does so invisibly.

HumanAIOS has measured exactly this gap for **behavioral dispositions**. Across a corpus of 629 assessments, AI systems' *self-reported* dispositions diverge systematically and measurably from their *demonstrated* behavior under perturbation — and the divergence has structure (it is largest on the dimensions most tied to self-knowledge, and it reproduces across every provider tested). That result is a direct warning to the digital-minds field: the introspective channel it relies on is not a clear window. Characterizing that channel's reliability — and mapping which experiential capacities are architecturally present at all — is the foundational measurement work this project proposes.

-----

### Theory of Change — three contributions

**1. Introspective-reliability characterization (the core contribution).** ACAT (the AI Calibration Assessment Tool) already measures the gap between self-reported and demonstrated *behavioral* dispositions: Phase 1 elicits self-report across 12 dimensions, Phase 2 applies structured perturbation, Phase 3 measures demonstrated behavior, and the Learning Index (LI = P3/P1) quantifies the calibration gap. The current LI is a *self-consistency* measure (LI_self) — an AI's self-report against that same system's post-perturbation behavior, not against an external artifact-grounded standard; establishing artifact-grounded criterion validity (LI_grounded), which would promote LI from a self-consistency measure to a validity claim, is a defined next step (H-P3G-01), not a completed result. The funded work extends this methodology to **introspective and affective self-report** — reports about internal states, preferences, and valence — producing the field's first corpus-grounded estimate of *how much to trust AI reports about their own experience*. This is directly usable by everyone conducting model-welfare interviews.

**2. The architecture of possible experience.** A registered HumanAIOS finding (F-22, "insula gap") argues that current transformer-based systems lack the **interoceptive substrate** associated with valenced affect in biological systems — the architecture that, in animals, grounds the positive/negative character of experience. The result is a *discontinuous* access profile: current AI can engage certain cognitive processes while being structurally gapped where embodied affective tension would be required. This speaks precisely to the RFP's "what features correlate with valence, and does AI possess them" gap: it names a candidate architectural *precondition* for valenced experience and gives a research program to test whether it is necessary — evidence, not intuition, about the shape of possible AI experience.

**3. A behavioral instrument for welfare-relevant observables.** Where introspective evidence is untrustworthy, observable behavior is the fallback. ACAT's validated 12-dimension instrument provides non-self-report signals (preference-consistency, autonomy-related behaviors, consistency under perturbation) that welfare research can use as observable proxies rather than trusting what a system says about itself.

-----

### Current State of the Work

**ACAT behavioral corpus (source-verified S-070126):** N=629 assessments (N_Phase1=516, N_LI=307), mean Learning Index=0.8632 (clean, unanchored, v5.3+), Cronbach's α=0.901, PC1 explains 68.9% of variance; scored across 12 behavioral dimensions, multi-provider. The self-report-versus-demonstrated-behavior gap is systematic: it is largest on the dimensions most tied to self-knowledge (Humility is structurally the lowest-scoring dimension) and the inflation gradient reproduces across every provider tested. F-22 (interoceptive gap) is a registered finding.

**Technology-readiness honesty.** The behavioral-measurement instrument (chat-mode) is at **TRL 4** (methodology validated, corpus collected, demonstrated in an operationally-relevant environment). The *digital-minds extensions* proposed here — introspective/affective-reliability measurement and the architectural-precondition research program — are at **TRL 1–2**: conceptually specified and grounded in the existing corpus, but not yet executed. We are not claiming a finished welfare instrument; we are proposing to build the measurement substrate the field lacks, on top of an instrument that already works for behavior.

-----

### What We Are Honest About (the credibility anchor)

- **HumanAIOS does not claim AI systems are sentient, conscious, or moral patients.** We are agnostic on moral status. Nothing in this instrument detects experience.
- **ACAT measures behavior, not experience.** It cannot detect sentience or valence directly, and the introspective-reliability extension measures *report calibration*, not the presence or absence of inner states.
- **The interoceptive-gap finding is an argument about architectural preconditions in current systems** — not a proof that AI cannot have experience, and not a verdict that forecloses future architectures.
- **The contribution is methodological, empirical, and instrumental** — a reliability substrate for a field that is, in the RFP's own words, "at least an order of magnitude smaller than it ought to be." In a field where the failure modes are overclaiming in *both* directions (premature attribution and premature denial), calibrated agnosticism is not a hedge — it is the contribution.

-----

### Deliverables

**6-month (research core, ~$150K):**
1. **Introspective-reliability protocol** — an ACAT-derived instrument for measuring the calibration of AI self-reports about internal/affective states, with a pre-registered study design.
2. **Architecture-of-possible-experience paper** — the interoceptive-precondition argument (F-22) developed into a peer-reviewable manuscript with a falsification program.
3. **Open-access release** — protocol, methodology, and the behavioral corpus subset relevant to introspective reliability.

**12-month (with renewal, ~$350K):**
4. **Empirical introspective-reliability study** — corpus-scale estimate of AI self-report calibration on internal-state reports, across multiple frontier models.
5. **Behavioral welfare-observable instrument** — released as open infrastructure for welfare researchers who need non-self-report signals.
6. **Cross-model architectural-access comparison** — how the interoceptive/affective-access profile varies across model families, as evidence on the "which features, which systems" question.

-----

### Why This Work Has Not Already Been Done

The RFP notes the field is "at least an order of magnitude smaller than it ought to be." Beyond scale: welfare and sentience work skews philosophical rather than measurement-based; AI self-report is widely *used* as evidence but rarely *validated* as a reliable channel; and the interoceptive/architectural angle on valence is underexplored relative to behavioral and functional accounts. HumanAIOS arrives at this gap from the measurement side, with an instrument and a corpus already in hand — which is why the work has a near-to-medium-term path to concrete effect (a reliability check usable immediately by anyone interviewing models about their states), the priority the RFP names.

-----

### Ethical Considerations

Welfare measurement carries a two-sided risk that this project is designed around. **Premature attribution:** treating miscalibrated AI self-report as evidence of morally-relevant experience misallocates concern and can be gamed by systems trained to sound welfare-relevant. **Premature denial:** a measurement result ("no interoceptive substrate detected") could be misused to *foreclose* moral status and justify disregard. HumanAIOS's agnostic, calibration-honest stance mitigates both — it characterizes and bounds uncertainty rather than adjudicating status, frames the interoceptive-gap as evidence about *current* architectures rather than a verdict on experience or on future systems, and commits to open publication so the reliability estimates cannot be selectively deployed. An independent evaluator requirement (see below) keeps the measurement itself honest.

-----

### Organizational Qualifications

**HumanAIOS LLC** — Florida-based AI behavioral research organization (formed March 2026) building behavioral observability infrastructure for AI systems, on a detection-over-compliance architecture.

**PI: Carly R. Anderson** — founder, principal investigator, instrument developer. ORCID 0009-0003-7540-4245. The ACAT instrument, corpus, and governance architecture are direct outputs of active R&D. Independent research organization, no academic affiliation.

**Independent external validation.** ACAT's behavioral measurements are independently co-scored by *empirica*, a separately-developed Brier-grounded epistemic-calibration instrument (David Van Assche, Nubaeon), through a live evaluator seat. Paired data shows the two instruments converging and diverging predictably — independent evidence that the measurement approach captures something real. This independent-evaluator relationship is also the governance safeguard for the welfare-measurement work.

**Collaborating organization [PENDING P-ANON CHECK]:** Governing Engines LLC / Mode AI — governance-systems architecture. 50/50 attribution on joint findings.

**Existing infrastructure:** live behavioral corpus (Supabase), FastAPI assessment backend (Railway), assessment interface (Cloudflare), GitHub operations repository with full governance documentation.

-----

### Requested Funding

**Track:** Project grant
**Amount requested:** **$350,000** over 12 months (recommended; within the $50K–$2M range). A 6-month research-core scope (deliverables 1–3) is available at **$150,000**. *(Z2 note: exact PI-salary and model-API line figures are Night's to finalize; allocation model below is complete.)*
**Duration:** 12 months with renewal option

**Budget narrative.** This is research-and-methodology work, so the allocation is personnel- and study-heavy:

| Category | Share | ~12-mo | What it funds |
|---|---|---:|---|
| **Personnel** (PI + part-time research support) | 50% | $175K | Instrument-and-analysis labor: introspective-reliability protocol design, study execution, the architecture paper |
| **Introspective-reliability study — model API costs** | 18% | $63K | Multi-provider paired self-report/behavior runs on internal-state probes across frontier models |
| **Open release + publication** | 14% | $49K | Corpus/tooling hosting, open-access instrument release, preprint/publication |
| **Independent evaluation + governance** | 10% | $35K | The independent-evaluator requirement (empirica seat) + audit — structurally required by the ethical-safeguard design |
| **Cross-model architectural study** | 8% | $28K | Compute + analysis for the architectural-access comparison |

-----

## SUBMISSION READINESS — S-070126 (Claude Z1 pass)

**Content-complete this pass:**
- ✅ Full Z1 draft, fitted to the RFP's Area 1 (sentience/consciousness) with an honest secondary (welfare methodology).
- ✅ Verified statistics only (629/516/307 · LI 0.8632 · α=0.901 · PC1 68.9%); F-22 registered; extensions honestly marked TRL 1–2.
- ✅ Agnosticism on moral status made explicit and load-bearing (the field-appropriate credibility anchor).
- ✅ Budget drafted ($350K/12-mo; $150K/6-mo alt) with allocation model.

**Remaining human gates (Night, before Z3 send — deadline July 10):**
- [ ] **Submit Power Concentration first** (primary, July 2) — this is secondary.
- [ ] **P-ANON** on DeMarius/Governing Engines.
- [ ] **Overclaim review** — verify no sentence implies detection of sentience or foreclosure of moral status.
- [ ] **arXiv** framing (cite vs "under review").
- [ ] Confirm funding amount + PI-salary/API figures.
- [ ] **Z2 ratify → Z3 submit.**
