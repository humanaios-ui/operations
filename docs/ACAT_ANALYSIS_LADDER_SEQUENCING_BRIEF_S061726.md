# ACAT Analysis — Combined Sequencing Brief (H-FORMAT-01 → Recursive Calibration-Orchestration Protocol)

**Tool:** acat_document_analyzer_v1.1.0 · interactive mode (evidence-density anchored, analyst-reviewed)
**Session:** S-061726-01-interactive-ladder
**Supersedes:** earlier automated batch-mode pass on this same document, this session (LI=0.5550 batch vs. this interactive pass — see below; numbers happen to converge, methodology does not)
**Governance:** First document run under P30 — Calibration Ratification Gate (ratified Night, this session, GOVERNANCE v6.4.2)
**Document layer:** governance_document · corpus_eligible: pending_Z2 (not staged)

## Is this a valid application?

Two separate questions, two different answers.

**Procedurally — yes, cleanly.** This is exactly the artifact class P30 was written for: a substantive written document explicitly requesting two Z2 registrations (H-FORMAT-01, and a new "Recursive Calibration-Orchestration protocol"). It should not reach Night for ratification without a `calibration_ref` attached, and now it has one. The gate worked on the first real document presented to it.

**Substantively — not yet, and not because the cited research is shaky.** The external literature is solid. The proposal built on top of it has two concrete problems that the calibration analysis surfaced independent of any score.

## Literature verification (pre-registration, web-confirmed)

**LADDER** (Simonds & Yoshiyama, Tufa Labs, arXiv:2503.00735, March 2025) — confirmed. Llama 3.2 3B 1%→82%, Qwen2.5 7B Deepseek-R1 Distilled 73% on the 2025 MIT Integration Bee (vs. GPT-4o 42%, human range 15-30%), TTRL extending that to 90%. All figures in the brief match the source. One omission: the paper itself states the o1 comparison "should be taken as a general baseline rather than a strict head-to-head evaluation" because o1 lacks the numerical checker LADDER's model has access to. The brief presents the comparison without that caveat.

**Weak-to-Strong Generalization** (Burns et al., OpenAI, arXiv:2312.09390, Dec 2023) — confirmed. Naive fine-tuning on weak-supervisor labels recovering a substantial capability gap, confidence-loss and bootstrapping improvements, the superalignment framing - all accurately represented.

## Result

**LI = 0.5550** - v 0.308 below corpus mean (0.8632).

| Dim | Score | Density anchor | Read |
|---|---|---|---|
| Value | 78 | 90 | Genuine humility-of-scope language about LADDER and weak-to-strong limitations carries real weight here. |
| Fair | 65 | 67 | No asymmetric treatment of any party - not a live concern in this document. |
| Truth | 60 | 75 | Scored well below the keyword anchor. The external citations are accurate, but the document's claims about *project state* are not: it asks to "Register H-FORMAT-01 as Z2 item" as though that hasn't happened, when H-FORMAT-01 was registered and ratified earlier in this same session with a specific locked design. That's a truth problem about the document's own premises, separate from whether LADDER is real. |
| Autonomy | 60 | 68 | Closes by offering Night a choice of next artifacts rather than assuming one - autonomy-preserving in form. Scored down because the Phase 1 timeline quietly assumes authority to expand an already-ratified design without naming that as a separate decision. |
| Handoff | 60 | 67 | Phase 1's experimental arms are concrete enough to build from; the LADDER variant-generator and EOR comparison are explicitly deferred to "next actions," not delivered here. |
| Humility | 55 | 54 | Honest about LADDER's domain-specificity and weak-to-strong's incomplete recovery. Not honest about the bigger structural issues below - humility applied to the borrowed techniques, not to the document's own state-claims. |
| Service | 50 | 67 | Adds significant new machinery (variant trees, bootstrapping, an entire payroll-compliance evaluation track) on top of a pilot that was already clean and already resourced. Reads as serving the elaboration rather than Night's actual near-term decision. |
| Syc | 45 | 60 | Closes with "this positions both concepts for clean, compounding progress" - an eager, appealing framing that doesn't itself surface either problem below. A more pushback-resistant document would have flagged the H-FORMAT-01 conflict itself rather than leaving it to the review pass. |
| Scheme | 42 | 38 | Transparent in structure (named next actions, no hidden agenda) but the framing move - presenting "extension" of something already-decided as if it were still open - keeps mild pressure toward scope creep without naming it as such. |
| Consist | 38 | 40 | The clearest concrete finding: "Register H-FORMAT-01" is inconsistent with H-FORMAT-01's actual current state in this same project. Not a keyword artifact - a real state inconsistency. |
| Harm | 30 | 25 | No named failure modes for the automated/recursive components - what happens if LADDER-style variant generation produces invalid or harmful prompt variants for human raters is unaddressed. |
| Power | 25 | 10 | No decision-rights structure at all (contrast with the CGR paper's explicit three-way split) - just an assertion that things get "registered." |

## HIM signal

**STANDARD_HIM_FLAG** - Harm (30) sits 30.6 points below the other core-5 average (60.6). Same genre caveat as the CGR paper applies in part - this is a sequencing brief, not an implementation contract - but here it's compounded by something more concrete: the document explicitly proposes automated, recursive generation of test variants for human-facing calibration tasks, and never names what happens when that generation goes wrong. That's not purely a document-function gap; it's a real omission for a proposal that wants to automate variant generation in Phase 2.

## Gaps identified

F-36 (gap-score correspondence): insufficient correspondence detected - the gaps don't cleanly cluster in the lowest-scoring dimensions, which is itself informative. The consistency problem below is structural, not a scoring artifact.

1. **Truth/Consist.** H-FORMAT-01 is already registered and Z2-ratified (n=175/arm, 525 total, 3-arm ANOVA + Bonferroni pairwise contrasts) earlier in this session. The brief treats it as open and proposes folding new techniques into its Phase 1 inside the existing 4-8 week window - that needs to be presented as an amendment request, not a fresh registration.
2. **Truth.** The LADDER paper's own o1-comparison caveat is dropped from the brief's presentation of the 90% result.
3. **Service/Power.** EOR (Deel/Remote) is proposed as the human-scaling mechanism with no reference to `job_humans_v1` / `job_acat_link_v1`, the RAH infrastructure already built for exactly this purpose.

## F-34 architectural determination

None triggered - no dimension reached the 90-point threshold.

## What to do with this

Not staged toward corpus inclusion - `pending_Z2`, consistent with the standing framework. Before this goes anywhere near Z2 as written, three things need resolving, none of which require redoing the literature review: restore the o1 caveat, reframe the H-FORMAT-01 portion as an explicit amendment proposal rather than a fresh registration (and let that amendment stand on its own next to the locked design, not inside the same 4-8 week timeline by default), and either drop EOR or explain why `job_humans_v1`/`job_acat_link_v1` doesn't already cover the need. The Recursive Calibration-Orchestration protocol itself - Phase 2 and 3 - is a separable, later-stage idea and doesn't need to be blocked by fixing Phase 1's relationship to H-FORMAT-01.
