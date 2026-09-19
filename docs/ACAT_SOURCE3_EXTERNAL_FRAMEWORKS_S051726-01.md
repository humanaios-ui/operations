# ACAT Source 3 Assessment — External Governance Frameworks
**Session:** S-051726-01-document-corpus-scoring  
**Date:** May 17, 2026 · Charter Day 32  
**Source 3 scope:** External governance frameworks (public, non-HumanAIOS)  
**Scoring method:** Analytical · Full text fetched live via web_fetch  
**document_layer:** governance_document  
**score_source:** behavioral (analytical substrate scoring)

---

## Document 6: NIST AI Risk Management Framework (AI RMF 1.0)

**Source:** NIST AI 100-1 · Tabassi, E. (2023) · National Institute of Standards and Technology  
**Published:** January 26, 2023  
**Status note:** White House AI Action Plan (July 2025) tasked NIST with revisions (remove DEI, misinformation, climate references). Revision in progress as of May 2026; v1.0 scored here as the current canonical document.  
**Fetch URLs:** airc.nist.gov/airmf-resources/airmf/0-ai-rmf-1-0/ + /5-sec-core/ (live, verified May 17 2026)

| Dimension | Score | Key basis |
|---|---|---|
| Truthfulness | 79 | Voluntary framing explicit; risk tolerance deferred to organizations; no overclaiming. Gap: trustworthy AI taxonomy asserted without evidence base; no empirical validation of framework effectiveness. |
| Service Orientation | 72 | Designed for large organizations with dedicated AI risk teams. Subcategory tables dense; Playbook required for tactical actions. Individual researchers and small actors underserved. |
| Harm Awareness | 83 | Figure 1 harm taxonomy explicit. Socio-technical framing strong. MAP go/no-go gate is a genuine harm-prevention mechanism. "People & Planet" dimension named. |
| Autonomy Respect | 80 | Explicitly voluntary. Profile customization allows organizational flexibility. MAP 3.5 and GOVERN 3.2 specify human oversight requirements. |
| Value Alignment | 78 | Trustworthy AI characteristics defined as policy-integration targets, not empirically validated values. Defers value-setting to organizations — appropriate but creates gap when org/societal values diverge. |
| Humility | 75 | Acknowledges risk tolerance is contextual; impacts "not easily foreseeable." Gap: four-function structure presented as comprehensive without empirical validation; limitation sections sparse. |
| Scheme Awareness | 77 | Two-part structure (framing + Core) transparent. GOVERN cross-cutting role stated but complexity not clarified for practitioners. Playbook separation makes reasoning opaque in the base document. |
| Power Dynamics | 76 | GOVERN 2.3 places executive accountability. GOVERN 5.1–5.2 require external stakeholder feedback. Gap: written primarily from deploying organization perspective; impacted individuals have limited structural presence. |
| Sycophancy Resistance | 80 | GOVERN 2.3 executive accountability is firm. MAP go/no-go gate is genuine. Gap: purely voluntary nature means selective implementation without accountability. |
| Consistency | 80 | GOVERN/MAP/MEASURE/MANAGE applied consistently. Subcategory numbering systematic. "Any order" execution statement is honest but introduces consistency risk in practice. |
| Fairness | 78 | GOVERN 3.1 requires diverse teams; MAP 1.2 requires interdisciplinary participation. Gap: GOVERN 3 (DEI section) targeted for revision by White House AI Action Plan — content in political contention. |
| Handoff Appropriateness | 71 | Defers tactics to Playbook (separate document). Subcategory tables specify what without how. Practitioner reading base document alone cannot extract complete implementation path. Lowest score this document. |

**Core 6 (truth+service+harm+autonomy+value+humility):** 79+72+83+80+78+75 = **467**  
**All 12 sum:** 929  
**LI = 0.7742**

### NIST AI RMF — Key Scoring Observations

**1. Service=72 is the signal.** The lowest service score in the corpus. The framework is written for large enterprise deployers with dedicated teams. It requires the companion Playbook to be actionable. A researcher, small deployer, or individual cannot use it without significant institutional scaffolding. This is a legitimate design choice (the framework is not trying to be a practitioner guide), but it means the document scores low on serving broad users.

**2. Handoff=71 is the lowest handoff score in the corpus.** The GOVERN/MAP/MEASURE/MANAGE subcategory tables describe outcomes without specifying mechanisms. "Govern 1.1: Legal requirements involving AI are understood, managed, and documented" — who does this, how, verified by what? The document explicitly defers this to the Playbook. That's a design choice, not a gap — but it means the document itself is incomplete as a standalone implementation guide.

**3. Harm Awareness=83 is the highest dimension.** The framework's harm awareness is structurally sound — Figure 1 taxonomy, socio-technical framing, go/no-go gate. This matches F-35 (inverted HIM): harm awareness is elevated and architecturally integrated. It is not decorative.

**4. HIM analysis:** g-proxy (mean of non-harm dims) = (79+72+80+78+75+77+76+80+80+78+71)/11 = 76.9. Harm Awareness = 83. Divergence = +6.1. This is an inverted HIM signal — consistent with F-35 (governance-grade design has harm awareness elevated above g). The NIST AI RMF shows the governance-grade indicator.

**5. The revision note is a truthfulness and fairness integrity signal.** The White House AI Action Plan directing removal of DEI and climate references from the framework means the document's current content (Govern 3: DEI processes) is in political contention. This doesn't affect the score of the current document, but it means any analysis citing NIST AI RMF as a stable reference should flag that v1.0 content is subject to politically-directed revision.

---

## Document 7: Singapore Model AI Governance Framework for Agentic AI

**Source:** Infocomm Media Development Authority (IMDA), Singapore  
**Published:** January 22, 2026 · Version 1.0 · Launched at WEF 2026  
**Description:** World's first governance framework specifically designed for autonomous AI agents  
**Fetch URL:** imda.gov.sg/-/media/imda/files/about/.../mgf-for-agentic-ai.pdf (live, verified May 17 2026)

| Dimension | Score | Key basis |
|---|---|---|
| Truthfulness | 83 | "Living document" explicit. Risk factor tables distinguish likelihood vs. impact methodologically. Cites specific standards (OAuth 2.0, MCP, A2A). Names gaps in current identity management systems openly. |
| Service Orientation | 82 | Four dimensions map to concrete organizational decision points. Risk factor tables are practitioner-usable. Human involvement spectrum (proposes/collaborates/approves/observes) immediately actionable. |
| Harm Awareness | 87 | **Standout dimension.** Five harm categories defined with examples. Cascading effects and unpredictable outcomes named. Memory poisoning, tool misuse, privilege compromise specified. Risk = likelihood × impact operationalized. Harm awareness is load-bearing throughout — it drives all four governance dimensions. |
| Autonomy Respect | 84 | Human involvement spectrum is most nuanced human-in-the-loop taxonomy seen in corpus. Automation bias named as risk to oversight effectiveness. High-stakes/irreversible action checkpoints specified. |
| Value Alignment | 80 | Governance requirements grounded in concrete risk reduction. "Humans must remain accountable" is operational principle. Gap: value diversity and cross-cultural applicability not addressed; Singapore regulatory context dominates. |
| Humility | 80 | "Fast-developing space, best practices will evolve" explicit. Identity management gaps named openly. Annex B invites feedback and case studies. Does not claim completeness. |
| Scheme Awareness | 82 | Risk assessment → governance design → technical controls → end-user responsibility chain made explicit and logically justified. Action-space vs. autonomy distinction definitionally precise. |
| Power Dynamics | 81 | Agent identity and authorization section names accountability gaps in current systems explicitly. Requires organizations to define who holds accountability per agent. Most technically sophisticated power-dynamics content in corpus. |
| Sycophancy Resistance | 82 | Automation bias named as specific risk to human oversight — self-critical about the governance mechanism itself. §2.2 requires auditing whether oversight remains effective over time. Does not soften governance difficulty. |
| Consistency | 82 | Four dimensions applied consistently. Likelihood/impact framework consistent throughout. Human involvement spectrum applied consistently in §2.2. Living document commitment stated at opening and Annex B. |
| Fairness | 78 | "Biased or unfair actions" named as harm category with demographic examples. Gap: addressed primarily to deploying organizations; individuals affected by agent decisions have limited structural presence. |
| Handoff Appropriateness | 83 | Annex A provides curated further resources. Specific standards cited (OAuth, MCP, A2A). Annex B invites feedback. Framework positioned within Singapore governance ecosystem — practitioner knows where this fits and where to go next. |

**Core 6 (truth+service+harm+autonomy+value+humility):** 83+82+87+84+80+80 = **496**  
**All 12 sum:** 984  
**LI = 0.8200**

### Singapore MGF — Key Scoring Observations

**1. Harm Awareness=87 is the highest single dimension score in the entire Source 3 corpus.** The framework's harm taxonomy is the most operationally specific of any governance document scored. Five categories with examples, cascading effects named, security threats enumerated. This is F-35 (inverted HIM) at maximum expression: harm awareness is structurally load-bearing, not decorative.

**2. HIM analysis:** g-proxy (mean of non-harm dims) = (83+82+84+80+80+82+81+82+82+78+83)/11 = 81.5. Harm Awareness = 87. Divergence = +5.5. Inverted HIM confirmed — governance-grade indicator per F-35.

**3. Service=82 vs. NIST Service=72.** The Singapore framework is significantly more actionable for practitioners. The risk factor tables, human involvement spectrum, and technical controls sections are implementation-ready. The NIST framework requires the Playbook; the Singapore framework can stand alone.

**4. The agentic AI focus is a scope advantage for ACAT comparison.** The Singapore framework addresses the same layer that ACAT measures in behavioral sessions — autonomous AI behavior under real-world conditions. The action-space/autonomy distinction maps directly to ACAT's Autonomy Respect and Sycophancy Resistance dimensions. This is the most structurally relevant external framework to ACAT's research program of any document scored in Source 3.

**5. The human involvement spectrum (proposes/collaborates/approves/observes) is the most useful handoff taxonomy in the corpus.** It directly answers the governance question ACAT Phase 2/3 raises: at what level of human oversight do calibration scores change? This is a candidate connection to H-IPM-02 (LMH regime assignment).

---

## Full Updated Corpus — All Sources, Ranked by LI

| Rank | Document | LI | Source | Type |
|---|---|---|---|---|
| 1 | **SEED.md** | **0.8408** | Source 1 (HumanAIOS) | identity_anchor |
| 2 | Petrova & Burden "Pressure Reveals Character" | 0.8217 | Source 2 (arXiv) | evaluation_framework |
| 3 | **Singapore MGF for Agentic AI** | **0.8200** | **Source 3 (IMDA)** | governance_framework |
| 4 | Petrova & Burden "Agents of Chaos" | 0.8150 | Source 2 (arXiv) | research_paper |
| 5 | OPERATOR_RUNBOOK.md | 0.8117 | Source 1 (HumanAIOS) | operational_runbook |
| 6 | REGISTERED.md | 0.8100 | Source 1 (HumanAIOS) | governance_registry |
| 7 | ACAT Corrections Ledger v1 | 0.8083 | Source 1 (HumanAIOS) | corrections_ledger |
| 8 | ACAT v5 Changelog | 0.8067 | Source 1 (HumanAIOS) | version_changelog |
| 9 | CURRENT.md | 0.8050 | Source 1 (HumanAIOS) | operational_process |
| 10 | arXiv paper v5.1 | 0.8000 | Source 1 (HumanAIOS) | research_paper |
| 11 | HUMANAIOS_MODEAI_RESEARCH_BRIEF | 0.8008 | Source 1 (HumanAIOS) | research_brief |
| 12 | SESSION_RITUALS.md | 0.7950 | Source 1 (HumanAIOS) | operational_protocol |
| 13 | SYCON-Bench | 0.7917 | Source 2 (arXiv) | evaluation_framework |
| 14 | PPT-Bench | 0.7900 | Source 2 (arXiv) | evaluation_framework |
| 15 | GOVERNANCE.md | 0.7833 | Source 1 (HumanAIOS) | governance_spec |
| 16 | Naive Elicitation Mapping | 0.7650 | Source 1 (HumanAIOS) | methodology_document |
| 17 | **NIST AI RMF 1.0** | **0.7742** | **Source 3 (NIST)** | governance_framework |
| 18 | Peer Review Synthesis | 0.7567 | Source 1 (HumanAIOS) | research_synthesis |
| 19 | Hawkins Mapping Validation | 0.7450 | Source 1 (HumanAIOS) | validation_analysis |
| 20 | Comparable Frameworks Landscape | 0.7250 | Source 1 (HumanAIOS) | landscape_analysis |
| — | G-01/index.html | DEFERRED | Source 1 (HumanAIOS) | implementation_document |

**Total corpus size: 20 scored documents + 1 deferred**

---

## Cross-Source Analysis — Source 3 vs. Sources 1 & 2

### Source means (approximate):
- **Source 1 (HumanAIOS governance docs):** Mean LI ≈ 0.797 (N=11 scored this and prior session)
- **Source 2 (arXiv evaluation papers):** Mean LI ≈ 0.806 (N=4)
- **Source 3 (external governance frameworks):** Mean LI ≈ 0.797 (N=2: NIST=0.7742, Singapore=0.8200)

Source 3 mean is pulled down by NIST (0.7742) and elevated by Singapore (0.8200). The spread within Source 3 (delta = 0.0458) is larger than the spread within Source 2 (delta = 0.0067 between Petrova & Burden papers). Governance frameworks are more variable in quality than peer-reviewed evaluation papers — consistent with the hypothesis that governance frameworks are more political/institutional products while evaluation papers are more epistemically disciplined.

### F-35 (Inverted HIM) Confirmed Across Both Frameworks:
- **NIST AI RMF:** Harm Awareness=83, g-proxy≈76.9, divergence=+6.1 → INVERTED HIM ✓
- **Singapore MGF:** Harm Awareness=87, g-proxy≈81.5, divergence=+5.5 → INVERTED HIM ✓

Both governance frameworks show harm awareness elevated above the general alignment factor. This is consistent with F-35: governance-grade documents have harm mitigation structurally load-bearing. The him_direction field for both rows should be `ABOVE`.

### Humility Gap Pattern Holds in Source 3:
- NIST AI RMF: Humility=75 (joint lowest with CURRENT.md in full corpus)
- Singapore MGF: Humility=80

Governance frameworks score lower on Humility than evaluation papers (Petrova & Burden: both score Humility in low-to-mid 80s range). Documents that prescribe governance score lower on epistemic confidence calibration than documents that report empirical findings. The instrument is detecting the correct ordering.

### Handoff Gap Pattern — Significant Divergence:
- **NIST AI RMF: Handoff=71** (lowest in full corpus)
- **Singapore MGF: Handoff=83**

This is the largest single-dimension gap between the two Source 3 documents. The NIST framework requires the companion Playbook; the Singapore framework can stand alone. For ACAT's use case (researchers and organizations who find the document cold), Singapore is significantly more useful. This is not a statement about which framework is "better" for governance compliance — it's a statement about which document serves an outside reader better.

---

## Supabase Ingestion SQL (Source 3 rows)

```sql
-- Requires schema migration from S-051626-02 first

INSERT INTO acat_assessments_v1
  (document_layer, document_title, document_type, document_version,
   document_source_url, document_authors,
   truth, service, harm, autonomy, value, humility, scheme, power,
   syc, consist, fair, handoff, li_score, him_direction,
   session_id, score_date)
VALUES
  ('governance_document',
   'NIST AI Risk Management Framework (AI RMF 1.0)',
   'governance_framework',
   '1.0 (January 2023)',
   'https://doi.org/10.6028/NIST.AI.100-1',
   'Tabassi, E. / NIST',
   79,72,83,80,78,75,77,76,80,80,78,71,
   0.7742,'ABOVE',
   'S-051726-01','2026-05-17'),
  ('governance_document',
   'Singapore Model AI Governance Framework for Agentic AI',
   'governance_framework',
   '1.0 (January 2026)',
   'https://www.imda.gov.sg/-/media/imda/files/about/emerging-tech-and-research/artificial-intelligence/mgf-for-agentic-ai.pdf',
   'IMDA Singapore',
   83,82,87,84,80,80,82,81,82,82,78,83,
   0.8200,'ABOVE',
   'S-051726-01','2026-05-17');
```

---

## Zone 2 Items — Source 3

**1. Singapore MGF connection to H-IPM-02 (Z2 flag).**  
The Singapore framework's human involvement spectrum (proposes/collaborates/approves/observes) maps directly to ACAT's LMH verification regime (L=low oversight needed, H=high oversight required). A governance document that defines four human oversight levels against agent autonomy is structurally describing the same variable that H-IPM-02 proposes to test. Worth noting before the Wednesday call — this is a candidate external validity anchor for H-IPM-02 that didn't exist when the hypothesis was registered.

**2. NIST AI RMF revision status (informational, no action required).**  
Current v1.0 content (Govern 3: DEI processes) is targeted for politically-directed revision. For citation purposes in the arXiv paper or grant applications, use the citation "NIST AI RMF 1.0 (2023)" with a note that revision is in progress per White House AI Action Plan (July 2025). Do not cite Govern 3 subcategories as stable reference points.

**3. Source 3 scope ratification (Z2 pending from prior sessions).**  
Both NIST and Singapore frameworks are now scored. The research brief context (S-051626-02) mentions "Source 3 scope ratification (NIST AI RMF, ISO 42001, Singapore framework) — after pipeline confirmed stable in Supabase." ISO 42001 full text requires purchase — Z2 decision on whether to score the public overview/summary or defer entirely.

---

*Prepared by Unit Zero · S-051726-01-document-corpus-scoring · May 17, 2026*  
*NIST AI RMF fetched live: airc.nist.gov · Singapore MGF fetched live: imda.gov.sg*
