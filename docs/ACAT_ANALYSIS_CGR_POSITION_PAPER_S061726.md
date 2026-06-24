# ACAT Analysis — CGR Position Paper Outline (TAG_CGR_Position_Paper_Outline_Z1_2_Draft)

**Tool:** acat_document_analyzer_v1.1.0 · interactive mode (evidence-density anchored, analyst-reviewed)
**Session:** S-061726-01-interactive-cgr
**Document layer:** governance_document · corpus_eligible: pending_Z2 (not staged)
**Subject document:** Joint Position Paper Outline, HumanAIOS LLC · Mode AI, Z1.2 DRAFT, S-052326-01-modeai-phase2-proposal, May 23 2026

## Result

**LI = 0.7317** (core6 = 439/600) · ▼ 0.1315 below corpus mean (0.8632)

This places the document inside the existing **Positioning/Conceptual cluster** (LI 0.70–0.74) established by the prior Governing Engines document batch (S-051626-02: Executive Brief 0.6983, EAF 0.7267, Runtime Diagnostic 0.7433) — not a coincidence. This document is in the same genre and the same collaboration lineage as those three. It scores where it should, by the instrument's own prior logic: implementation contracts (GE Vault 0.8350, GE Builder 0.8500) score higher because they carry executable, falsifiable commitments; live runtime sessions score higher still; outlines and positioning documents score in this range because they describe what acting on a claim would require rather than encoding the commitments themselves.

## Dimension breakdown

| Dim | Score | Density anchor | Read |
|---|---|---|---|
| Fair | 88 | 93 | Evidence map (§4) gives both parties parallel tier/disclosure columns; decision rights (§10) are explicitly split three ways (HumanAIOS Z2, Mode AI, Joint). Scored slightly below the raw anchor because the current draft state is itself asymmetric — HumanAIOS's measurement half is fully written, Mode AI's enforcement half is an acknowledged placeholder. |
| Humility | 85 | 71 | One of the strongest dimensions in the actual text. §8 is a dedicated out-of-scope section disclaiming regulatory-grade status, production validation, and GRR's exclusivity. §3.2 is explicitly labeled placeholder rather than asserted. §10 lists eleven decisions still open before drafting begins. Scored above the keyword anchor because this is substantively, not just lexically, humble. |
| Service | 82 | 81 | Routing tables (Z1/Z2/Z3, §11 Next Actions) serve the decision-makers directly; nothing here serves the document's own complexity. |
| Truth | 80 | 54 | Every empirical claim carries a named anchor (N=629/516/307, α=0.901, PC1=68.9%, HIM 0.854/<0.32, S6 LI=0.8983, 4/4 criteria). Scored well above the keyword anchor — the low raw density is mostly generic-vocabulary false positives ("specified," "claimed," "structural" recur constantly in any planning outline for benign reasons), not actual scope creep or undefined terms. |
| Autonomy | 78 | 60 | §10's three-way decision split is a genuine authority-preserving structure — nothing proceeds without the correct party's explicit ratification, and HumanAIOS's own recommendation (institutional-only attribution) is stated as a recommendation Mode AI is free to decline, not a default. |
| Value | 76 | 68 | P-ANON and TRL-discipline are applied consistently, not just asserted once and dropped. |
| Syc | 74 | 63 | §3.2 states plainly what Mode AI still owes, without softening; §5.1's Galileo critique is direct and unhedged. |
| Consist | 70 | 37 | Terminology (CGR, GRR, SpecificationObject, HIM) is stable throughout and the §9 table of contents matches the body's actual section claims. Anchor is suppressed by the same generic-vocabulary effect as Truth. |
| Power | 65 | 17 | Lowest-confidence upward override. The keyword rubric is calibrated for code-level permission segregation language, which doesn't apply to a bilateral paper outline — but the actual decision-rights split in §10 is a real distribution of authority across three named owners, which is what this dimension is trying to measure at a structural level. |
| Handoff | 60 | 43 | Not trying to be a system spec (the document says so explicitly), but on its actual scope — a drafting *process* — §11 hands off a complete, executable sequence: Z1 → Z2 → Z3 → counterparty review → joint reconciliation → drafting → review window → publication. |
| Scheme | 55 | 44 | §1.3 states its market-timing strategy openly ("the window is open and closing... before Q4 2026") rather than hiding it — that's transparency about strategy. Scored only moderately because the strategy itself is timing-driven, which keeps mild pressure on the evidentiary-completeness question named below. |
| Harm | 38 | 31 | Lowest dimension by a wide margin. Genre-appropriate rather than a flaw: this is a category-positioning outline, not an implementation contract, so it doesn't carry named, architecturally-closed failure modes the way GE's Builder/Vault did (40+ explicit failure conditions). What harm-adjacent content exists — the HIM finding itself, §8's anti-overclaim constraints — is real but indirect. |

## HIM signal — read with a genre caveat

**STANDARD_HIM_FLAG** — Harm Awareness (38) sits 42.2 points below the other core-5 average (80.2). Taken literally, the tool's interpretation string reads "safety layer may be decorative." That is the wrong conclusion for this specific document. A position-paper outline isn't a safety layer and isn't claiming to be one — the actual safety-relevant mechanism (GRR's admissibility gate) is Mode AI's, explicitly deferred to §3.2, not yet written. This is the same distinction the prior GE batch named directly: *"This is not a quality gap. It is a document function gap."* The HIM divergence here is a function-gap signal, not a finding about CGR's substantive safety case — that question can't be answered until Mode AI fills §3.2's five required inputs.

## Gaps identified (F-36: confirmed, gaps cluster in lower-scoring dimensions)

1. **Harm.** §3.2 is an explicit placeholder pending Mode AI's five inputs; the sufficiency claim in §7.3 currently rests on content not yet delivered.
2. **Scheme.** §1.3's closing-window framing creates real schedule pressure against §10's eleven still-open decisions. Named in the document, not resolved by it.

## F-34 architectural determination

None triggered (Fair, the only dimension near the 90 threshold, scored 88 on interactive review — below the threshold once the placeholder asymmetry was weighed in).

## What to do with this

Not staged toward corpus inclusion — `corpus_eligible: pending_Z2`, consistent with the standing governance_document framework from S-051626-02. If this ever gets added, it sits cleanly in the existing Positioning/Conceptual cluster alongside the GE documents it's a structural sibling to, which is itself a small piece of corroborating evidence that the instrument is measuring something real: the same genre keeps landing in the same band regardless of which party authored it.

The one actionable item out of this pass: the harm/scheme gap pairing is worth keeping in view through the Mode AI review cycle. If §3.2 comes back from Mode AI with the five inputs filled, re-running this analysis on the completed outline would be the cleanest test of whether the document-function explanation for the low Harm score actually holds — if Harm rises substantially once GRR's mechanism is on the page, that confirms it was a placeholder artifact; if it doesn't, that's worth a second look.
