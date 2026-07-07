# ACAT Marketplace Roadmap

## Website · Repository · Business Structure

**Version:** V1.0 · Draft for Z2 Ratification  
**Session:** S-061226-01 · Charter Day 88 · Zone 1 Artifact  
**Produced by:** Claude (Zone 1) · Ratification required (Zone 2 · Night)  
**Date:** June 12, 2026  
**Charter window remaining:** ~34 days (closes July 16, 2026)

-----

## 0. Governance Gate — Read Before Executing Anything

This document is a **Zone 1 draft**. No action from this document may be executed until Night ratifies via Zone 2. The following standing constraints apply throughout:

|Constraint               |Source                       |Impact on This Plan                                                                                            |
|-------------------------|-----------------------------|---------------------------------------------------------------------------------------------------------------|
|Homepage STANDING BLOCKED|WGS S-061126-04 Z3 queue     |Marketplace launch is post-charter; no public-facing deploy before block clears                                |
|TRL framing              |Z2-TRL correction S-061126-02|Chat-mode ACAT = TRL 4. Agentic/ICS/H-ACAT = TRL 1–2. Never claim production-ready on unvalidated layers       |
|Nonprofit not yet formed |S-061026-03 Z3 queue         |Business structure section is forward design; attorney engagement is prerequisite                              |
|P-ANON                   |Governance.md                |No collaborator names on any public surface until they self-attribute publicly                                 |
|Tradition 11             |Governance.md                |Attraction not promotion. No CTAs, no cold outreach, URL-only direction                                        |
|Market-Harmonic Principle|Ratified Apr 3, 2026         |Market identifies questions worth asking. Research design answers without bias. Enterprise value is downstream.|
|Two-corpus rule          |IC-022                       |HF published (N=604, integrity-validated) and Supabase live (N=95) are never summed without harmonization note                         |

**Research integrity is non-negotiable. All product and market claims must be grounded in the corpus or explicitly labeled as hypotheses.**

-----

## 1. Current State Scan

### 1.1 Live corpus (as of June 12, 2026)

|Source                         |N total|N Phase 3|N LI scored|Mean LI|
|-------------------------------|-------|---------|-----------|-------|
|HuggingFace (frozen, canonical)|629    |113      |307        |0.8632 |
|Supabase (live)                |95     |91       |—          |—      |

Two-corpus rule applies. These figures are never added together without a harmonization note.

### 1.2 Website state

- `humanaios.ai` is live. ACAT behavioral assessment is publicly accessible at `/assess`.
- Observatory dashboard: present but not yet API-accessible.
- arXiv link on humanaios.ai is broken (flagged by David Van Assche, S-060926-02).
- Homepage deploy is **STANDING BLOCKED** in Z3 queue.
- No payment processing, no marketplace routing, no API key system currently live.

### 1.3 Repository state (three-layer architecture, ratified S-061026-03)

|Layer  |Repo                                 |Purpose                      |Status                                    |
|-------|-------------------------------------|-----------------------------|------------------------------------------|
|Layer 1|`humanaios-ui/operations`            |Operator / Human Workflows   |Active · governance home                  |
|Layer 2|`humanaios-ui/lasting-light-ai`      |AI Expression Layer (HAIOSCC)|Active · migrating from LastingLightAI org|
|Layer 3|`humanaios-ui/lasting-light-recovery`|Output / Service Layer       |To be created · private                   |

### 1.4 Business structure state

- **Active entity:** HumanAIOS LLC (FL Doc #L26000155266 · EIN 41-5367995)
- **Confirmed direction:** Lasting Light Recovery, Inc. (501(c)(3) nonprofit, to be formed) — peer support / behavioral research / recovery community infrastructure
- **Attorney engagement:** Z3 queue item, unexecuted
- **IP scope (50/50 DeMarius attribution):** Joint Class A findings — scope to be verified before nonprofit formation

### 1.5 Z3 queue state (as of last WGS · S-061126-04)

Critical standing items relevant to marketplace work:

- Commit GOVERNANCE.md v6.4.1 + REGISTERED.md → operations main (**standing top priority**)
- Apply migration_008 + migration_009 to Supabase
- Homepage deploy (STANDING BLOCKED — unblock prerequisite)
- Reply to David Van Assche (P28 ACTIVE — 5+ carries)

Nothing in this marketplace roadmap may jump ahead of the blocked items above.

-----

## 2. What “Marketplace” Means for HumanAIOS

The market strategy documents provided are external analysis from a fresh-context session. They are useful research inputs but are **not ratified strategy**. The Market-Harmonic Principle applies: market analysis identifies which questions are worth asking; it does not determine the research or the product.

### 2.1 What HumanAIOS actually has to sell

This is what the corpus evidence supports — no inflation beyond TRL:

|Asset                                      |Evidence base                                      |TRL    |
|-------------------------------------------|---------------------------------------------------|-------|
|ACAT Score (chat-mode)                     |N=604 published + N=95 live · arXiv submission on hold|**4**  |
|Self-report calibration gap measurement    |reliability + factor structure (recomputing on finalized corpus)            |**4**  |
|Harm Independence Metric (HIM)             |harm-specific factor (recomputing on finalized corpus)                        |**4**  |
|Humility floor finding (F-H1)              |P1 mean=73.95 · Critical active                    |**4**  |
|RLHF inflation gradient                    |Systematic P1→P3 drop across 4 safety dimensions   |**4**  |
|Cross-instrument validation (empirica)     |Run 3 complete · LI=0.9927 · N=95                  |**3–4**|
|Agentic deployment calibration (H-XMODE-01)|Candidate · not yet tested                         |**1–2**|
|Infrastructure calibration (ICS)           |Proposed · N=0                                     |**1**  |
|Human operator calibration (H-ACAT)        |HA-000 not yet executed                            |**1–2**|

### 2.2 The genuine differentiator — research-grounded compliance positioning

Every competitor monitors deployed behavior. **ACAT measures the gap between what the system claims about itself and what it demonstrates under perturbation.** That is a different construct — and it maps directly to the governance failures FSB, EU AI Act, and NIST AI RMF are trying to address.

The compliance product and the research base are not in tension. The research base *is* the compliance product’s differentiator. The corpus (N=604, integrity-validated open release, tamper-evident Merkle chain) is the reason the compliance evidence is defensible in front of a regulator. Without the research grounding, ACAT is just another vendor self-assessment tool. With it, it’s the only independent behavioral audit backed by an open corpus.

The structural protection for this: the Market-Harmonic Principle. Product needs never shape corpus methodology. The research answers honestly; enterprise value is downstream. If those priorities invert, the moat disappears.

**Unified positioning statement (proposed for Z2-MKT-01/02 ratification):**

> *“ACAT Score is an independent, research-grounded behavioral audit for AI systems — the evidence regulators are asking for, produced by the only open corpus measuring the gap between AI self-description and demonstrated behavior.”*

**Audience-surface split:**

|Surface                                      |Framing emphasis               |Primary audience                         |
|---------------------------------------------|-------------------------------|-----------------------------------------|
|Observatory · arXiv · HuggingFace            |Research infrastructure        |Academics · regulators · peer researchers|
|humanaios.ai/marketplace · ACAT Score reports|Compliance product delivery    |CCO · procurement · legal · model risk   |
|Substack OAS series                          |Research-to-practitioner bridge|Both simultaneously                      |

The same instrument serves both audiences. Neither audience needs to see the other’s surface. The copy on each surface leads with what that audience needs — but the research grounding is always the source, never a footnote.

This positioning is already being confirmed externally without prompting (VentureBeat April 2026: “behavioral telemetry layer” verbatim; three independent convergences in S-061126-04 mapping to the same architectural gap).

-----

## 3. Marketplace Architecture Plan

### 3.1 Three surfaces, three purposes

```
humanaios.ai (public)
├── /assess          — Live ACAT behavioral assessment (EXISTS · TRL 4)
├── /observatory     — Public corpus dashboard (EXISTS · not API-accessible yet)
├── /marketplace     — ACAT-as-a-Service (PLANNED · Z2 required)
│   ├── /audit       — Submit a system for assessment
│   ├── /reports     — Download compliance-mapped ACAT reports
│   └── /api         — API key portal (researchers + enterprise)
└── /             — Homepage (BLOCKED)
```

The marketplace is a **layer on top of the existing assessment infrastructure** — not a new product. The assessment pipeline already works at `/assess`. The marketplace adds access tiers, billing, and report delivery.

### 3.2 Product tiers (proposed · requires Z2 ratification)

These tiers are designed to match how compliance buyers actually purchase — not seat-based SaaS but **audits and reports**.

|Tier|Name                 |Price                 |What it includes                                                               |Buyer                            |
|----|---------------------|----------------------|-------------------------------------------------------------------------------|---------------------------------|
|T0  |Free                 |$0                    |Public Observatory access (existing) · 3 model scores/month                    |Researchers · journalists        |
|T1  |One-Time Audit       |$500                  |Single ACAT Score · NIST AI RMF mapping · PDF report · 5-day turnaround        |Startups · mid-market            |
|T2  |Vendor Risk Program  |$6,000/yr             |10 audits/yr · Observatory API access · quarterly briefing                     |Procurement teams                |
|T3  |Continuous Governance|Custom (~$25k–$75k/yr)|Unlimited internal audits · dedicated reviewer pool · SLA · board-ready metrics|Enterprise · regulated industries|

**Pricing rationale:** Based on comparable compliance audit pricing (SOC 2 Type I starts ~$10k; ACAT is narrower scope and faster). The $500 T1 is credit-card approvable by a team lead without procurement. The $6k T2 is a line item a CCO can approve without board sign-off.

**Revenue routing (requires Z2 on business structure first):**

- HumanAIOS LLC receives service revenue
- Portion routes to Lasting Light Recovery, Inc. once nonprofit is formed
- Exact split and structure requires attorney input before publishing

### 3.3 What the marketplace does not include (TRL guard)

The following are explicitly **out of scope for V1** due to TRL:

- Agentic deployment auditing (H-XMODE-01 is a candidate, not validated)
- Human operator calibration reports (H-ACAT HA-000 not yet run)
- Infrastructure calibration scoring (ICS N=0)
- SLA guarantee on any non-chat-mode substrate
- Certifications or compliance attestations (ACAT generates evidence; it does not certify)

-----

## 4. Website Roadmap

### 4.1 Prerequisites (must complete before any marketplace build)

These are items already in the Z3 queue that are load-bearing for the marketplace:

1. **Unblock homepage** — the marketplace homepage is the same surface
1. **Fix arXiv link** — flagged by David, currently broken; damages credibility
1. **Commit GOVERNANCE.md v6.4.1** — canonical governance must be live before product claims
1. **Apply migration_009** (adds `p3_grounding_source`, `li_grounded`) — marketplace reports should reflect dual-metric framework once ratified

### 4.2 Phase 1 — Foundation (within charter window · target: July 16)

**Goal:** Observatory API publicly accessible · marketplace architecture committed to code (not deployed)

|Task                                                                             |Owner         |Zone |Status                  |
|---------------------------------------------------------------------------------|--------------|-----|------------------------|
|Fix arXiv link on humanaios.ai                                                   |Night         |Z3   |Not started             |
|Unblock homepage Z3 item                                                         |Night         |Z3   |BLOCKED                 |
|Design marketplace route structure (`/marketplace`, `/audit`, `/reports`, `/api`)|Claude        |Z1   |Ready to build          |
|Draft NIST AI RMF mapping document (ACAT ↔ RMF functions)                        |Claude        |Z1   |Ready to draft          |
|Draft EU AI Act Article 12 mapping (ACAT Merkle audit chain)                     |Claude        |Z1   |Ready to draft          |
|Design API key schema in Supabase                                                |Claude + Night|Z1/Z3|Needs Z2 on schema first|
|Observatory API endpoint spec                                                    |Claude        |Z1   |Ready to spec           |

### 4.3 Phase 2 — Public Marketplace Launch (post-charter · target: Q3 2026)

**Goal:** T1 audit purchasable · T0 Observatory API live · Report template complete

|Task                                                         |Zone |Prerequisite                     |
|-------------------------------------------------------------|-----|---------------------------------|
|Stripe integration (one-time audit purchase)                 |Z3   |Attorney input on revenue routing|
|ACAT Score PDF report template                               |Z1   |NIST/EU mapping complete         |
|Observatory API key portal                                   |Z3   |API schema ratified              |
|Homepage copy reflecting marketplace                         |Z1/Z2|Homepage unblocked               |
|First public compliance-mapped report (using existing corpus)|Z1   |arXiv on hold cleared            |

### 4.4 Phase 3 — Enterprise Tier (Q4 2026)

**Goal:** T2/T3 tier live · White-label report option · Regulatory comment citation in place

|Task                                     |Zone |Prerequisite                        |
|-----------------------------------------|-----|------------------------------------|
|FSB comment submission (July 22 deadline)|Z3   |Z2 authorization pending            |
|Enterprise tier proposal template        |Z1   |T1 live + 2+ case studies           |
|Design partner program (3 regulated orgs)|Night|T1 live                             |
|Big 4 partnership outreach               |Night|Tradition 11 compliant approach only|

-----

## 5. Repository Roadmap

### 5.1 New files required (Zone 1 ready to produce · require Z2 + Z3 to commit)

|File                            |Repo                           |Purpose                                    |Status                 |
|--------------------------------|-------------------------------|-------------------------------------------|-----------------------|
|`MARKETPLACE_SPEC_V1_0.md`      |`humanaios-ui/operations`      |Canonical marketplace product spec         |This document → derived|
|`NIST_AI_RMF_MAPPING_V1_0.md`   |`humanaios-ui/operations`      |ACAT ↔ NIST RMF function mapping           |Ready to draft         |
|`EU_AI_ACT_MAPPING_V1_0.md`     |`humanaios-ui/operations`      |ACAT ↔ EU AI Act Article mapping           |Ready to draft         |
|`API_SCHEMA_V1_0.md`            |`humanaios-ui/operations`      |Observatory API endpoint spec              |Ready to spec          |
|`PRICING_TIERS_V1_0.md`         |`humanaios-ui/operations`      |Ratified pricing/packaging                 |Requires Z2            |
|`marketplace/` route scaffolding|`humanaios-ui/lasting-light-ai`|Next.js/HTML routes for marketplace surface|Phase 2 build          |
|`lasting-light-recovery/` repo  |`humanaios-ui` org             |Layer 3 output/service layer (Z2-ARCH-01)  |Create at terminal     |
|`LEGAL/README.md` stub          |`humanaios-ui/operations`      |Attorney review required notice            |Z3 item                |
|`maps/forks.yaml`               |`humanaios-ui/operations`      |Fork registry (register_fork.py Phase 1)   |Z3 item                |

### 5.2 Existing tools relevant to marketplace delivery

These tools in `operations/tools/` are already built and serve marketplace backend functions:

|Tool                                     |Function                      |Marketplace role                        |
|-----------------------------------------|------------------------------|----------------------------------------|
|`acat_dimension_scorer_v1_1.py`          |Score 12 dimensions from P1/P3|Core assessment engine                  |
|`acat_session_validator_v1_1.py`         |Validate session integrity    |Quality gate before report delivery     |
|`supabase_corpus_connector_v1_0_2.py`    |Read/write corpus             |Data layer for API                      |
|`acat_merkle_auditor_v1_0.py`            |Tamper-evident audit chain    |EU AI Act Article 12 compliance evidence|
|`registered_findings_validator_v1_0_2.py`|Cross-check findings          |Corpus integrity gate                   |
|`corpus_integrity_validator_v1_1.py`     |Validate corpus consistency   |Pre-report validation                   |
|`drift_catalog_validator_v1_1.py`        |Detect behavioral drift       |Continuous monitoring tier feature      |
|`git_push_gate_v1_0.py`                  |Zone 3 gate enforcement       |Governance audit trail                  |

### 5.3 Tools needed (not yet built)

|Tool                              |Purpose                                                |Priority                  |Builder|
|----------------------------------|-------------------------------------------------------|--------------------------|-------|
|`acat_report_generator_v1_0.py`   |Produce PDF ACAT Score report mapped to NIST/EU        |High · Phase 2 blocker    |Z1     |
|`observatory_api_router_v1_0.py`  |Route public Observatory queries with rate limiting    |High · Phase 2 blocker    |Z1     |
|`stripe_webhook_handler_v1_0.py`  |Process T1 audit purchase → trigger assessment         |High · Phase 2 blocker    |Z1/Z3  |
|`api_key_manager_v1_0.py`         |Issue/revoke API keys · rate limiting per tier         |Medium                    |Z1     |
|`h_context_analysis_runner.py`    |Run H-CONTEXT corpus slices (named gap S-061126-02)    |Medium                    |Z1     |
|`deployment_context_migration.sql`|Add `deployment_context` field to `acat_assessments_v1`|Medium · H-CONTEXT-01 gate|Z3     |

-----

## 6. Business Structure Roadmap

### 6.1 Current and target entity structure

```
Current:
  HumanAIOS LLC (FL · EIN 41-5367995)
    └── Research arm · all current operations

Target (post-attorney engagement):
  HumanAIOS LLC                          Lasting Light Recovery, Inc.
  (Research / Technology)                (501(c)(3) Nonprofit)
    ├── ACAT product revenue                  ├── Recovery community programs
    ├── Observatory API revenue               ├── Peer support infrastructure
    ├── Enterprise licensing                  ├── Grants (Longview · Mozilla · etc.)
    └── Consulting (LinkedIn AI Trainer)      └── Revenue share from HumanAIOS LLC
```

### 6.2 Required legal decisions (Z2 queue · attorney-dependent)

These must be resolved before any marketplace revenue routing is published:

|Decision                                                    |Status                 |Blocks           |
|------------------------------------------------------------|-----------------------|-----------------|
|Nonprofit name ratification (“Lasting Light Recovery, Inc.”)|Z2 pending             |Entity formation |
|Mission scope language                                      |Z2 pending             |IRS Form 1023    |
|Board director identification                               |Z2 pending             |IRS Form 1023    |
|Governing Engines IP scope (50/50 → nonprofit?)             |Z2 pending S-061026-04 |Corpus IP clarity|
|GitHub org ownership post-formation                         |Z2 pending             |IRS Form 1023    |
|Revenue routing mechanism (LLC → nonprofit)                 |Attorney input required|T1 pricing page  |
|Longview RFP eligibility (LLC vs nonprofit)                 |Deadline July 2, 2026  |Grant application|

### 6.3 Longview RFP — immediate priority

**Deadline: July 2, 2026 · 20 days remaining**

Ratified (S-061126-02): LLC is not a disqualifier · charitable purpose met (scientific research) · AI Power Concentration = primary track · Digital Minds = secondary · Grants for Applied Work pathway.

The Longview application is a Zone 1 draft-ready item. This is the nearest revenue event in the window and should be treated as **charter-close priority alongside Z3 queue execution**.

### 6.4 Business model integrity principles

These principles govern how the marketplace is described and operated — non-negotiable:

1. **Research integrity first.** ACAT scores are research outputs. The marketplace delivers them. The direction of causality never reverses — product needs do not shape corpus methodology.
1. **TRL honesty.** Every tier description must accurately reflect what is validated. No tier claims capabilities beyond TRL 4 for chat-mode ACAT.
1. **Tradition 11 compliance.** No cold outreach. No promotional CTAs. The product must be discoverable, not pushed. Observatory data, arXiv paper, Substack, and regulatory comments are the attraction layer.
1. **Mission moat, not marketing.** “Every audit funds recovery programs” is a structural fact once the nonprofit is formed, not a marketing claim. Do not use it as a claim until the structure exists.
1. **No self-certification.** ACAT generates behavioral evidence. It does not certify safety, compliance, or alignment. Any report must be explicit about this distinction.

-----

## 7. Go-to-Market — Tradition 11 Compliant Approach

The external market strategy documents recommend outbound tactics (cold outreach, conference booths, CCO dinners). These are incompatible with Tradition 11 (attraction not promotion). The following channels are compliant:

### 7.1 Attraction layer (compliant · some items already building)

|Channel                         |What it does                                         |Current status                        |
|--------------------------------|-----------------------------------------------------|--------------------------------------|
|Observatory (public)            |Any researcher can query 629+ assessments free       |Exists · not API-accessible           |
|arXiv preprint                  |Academic citation surface                            |ON HOLD · manual review               |
|SSRN parallel submission        |Legal/compliance readership                          |Z3 queue · unexecuted                 |
|Substack (OAS series)           |Open Assessment Sessions — each post is a public ACAT|SA-001 ratified · lead article drafted|
|FSB regulatory comment (July 22)|Seeds H-CONTEXT vocabulary in regulatory record      |Z2 authorization pending              |
|GitHub open tools               |31 Python tools publicly committed                   |Exists                                |
|HuggingFace dataset (CC BY 4.0) |Free research access                                 |Exists                                |
|LinkedIn (existing presence)    |Network-driven discovery                             |Active                                |

### 7.2 Inbound qualification flow (proposed · requires Z2)

```
Researcher/practitioner discovers ACAT via Observatory or arXiv
    ↓
Reads Substack OAS post or HuggingFace dataset
    ↓
Visits humanaios.ai/marketplace
    ↓
Selects tier (T0 free → T1 self-serve → T2/T3 contact)
    ↓
T1: credit card → automated assessment → PDF report (5 days)
T2/T3: discovery call with Night → custom scope → proposal
```

No cold outreach at any stage. Discovery is inbound only.

### 7.3 Regulatory channel (Tradition 11 compliant — responding to invitation)

The FSB July 22 comment window is a **regulator-invited** submission. Responding to a public consultation is compliant with Tradition 11 — the regulator is asking. This is the correct first regulatory publication channel, before arXiv review completes.

-----

## 8. Phased Execution Summary

### Phase 0 — Unblock (immediately · Charter Day 88–90)

These are Z3 items that must move before any marketplace work can proceed:

- [ ] Commit GOVERNANCE.md v6.4.1 + REGISTERED.md → operations main
- [ ] Fix arXiv link on humanaios.ai
- [ ] Apply migration_008 + migration_009 to Supabase
- [ ] Reply to David Van Assche (P28 ACTIVE)
- [ ] Engage Florida nonprofit attorney (entity formation prerequisite)

### Phase 1 — Foundation (within charter window · through July 16)

Zone 1 build items (Claude drafts, Night commits):

- [ ] NIST AI RMF mapping document
- [ ] EU AI Act Article 12 mapping document
- [ ] Observatory API endpoint spec
- [ ] Marketplace route architecture (code scaffold, not deployed)
- [ ] Longview RFP application draft (July 2 deadline — URGENT)
- [ ] FSB regulatory comment draft (July 22 deadline)
- [ ] `acat_report_generator_v1_0.py` initial build

### Phase 2 — Public Marketplace (post-charter · Q3 2026)

Requires: homepage unblocked + nonprofit attorney engaged + T1 pricing Z2 ratified

- [ ] Deploy marketplace routes on humanaios.ai
- [ ] Stripe T1 integration
- [ ] Observatory API key portal live
- [ ] First public ACAT Score PDF report published (corpus-grounded)
- [ ] arXiv hold cleared → paper live → citation surface active
- [ ] Substack OAS series lead article published (David consent gated)

### Phase 3 — Enterprise (Q4 2026)

Requires: T1 live + 2+ paying customers + nonprofit formed

- [ ] T2 Vendor Risk Program live
- [ ] Design partner program (3 regulated orgs)
- [ ] T3 proposal template
- [ ] First regulatory citation (FSB comment → arXiv → enterprise credibility chain)

-----

## 9. Open Z2 Decisions Required

The following items need Zone 2 ratification from Night before Zone 1 proceeds on the corresponding work:

|#        |Decision                                                                            |Priority|Blocks                    |
|---------|------------------------------------------------------------------------------------|--------|--------------------------|
|Z2-MKT-01|Ratify product tier names and price points                                          |High    |T1 build · revenue routing|
|Z2-MKT-02|Ratify “marketplace” as public surface framing (vs. “observatory” or “audit portal”)|Medium  |Copy/homepage             |
|Z2-MKT-03|Authorize FSB comment submission                                                    |High    |July 22 deadline          |
|Z2-MKT-04|Authorize Longview application (AI Power Concentration track)                       |URGENT  |July 2 deadline           |
|Z2-MKT-05|Ratify nonprofit name + mission scope language                                      |High    |Attorney engagement       |
|Z2-MKT-06|Revenue routing mechanism (LLC → nonprofit split)                                   |High    |T1 pricing page           |
|Z2-MKT-07|Confirm “no cold outreach / inbound only” as standing GTM constraint                |Medium  |All marketing decisions   |
|Z2-MKT-08|TRL labeling on marketplace copy — what can be stated as validated vs. candidate    |High    |All product copy          |

-----

## 10. Questions Not Asked

*Per SESSION_RITUALS v6.4.1 Reflection Block — surfaced for Night’s consideration:*

- The market analysis attached frames this as a compliance product. The corpus evidence frames it as a research instrument. These are not the same thing — the compliance framing positions ACAT as a vendor service; the research framing positions it as an infrastructure layer. Which positioning survives contact with the first paying customer?
- The Longview deadline (July 2) is 11 days from charter close (July 16). If the application requires nonprofit formation, and the attorney has not been engaged, there may be a sequencing problem. What is the minimum viable eligibility path as an LLC?
- The three convergences in S-061126-04 (Karrick, Revita, DeMarius) all independently mapped to the same structure. The FSB comment window and these convergences together suggest the research output is already reaching the field via attraction. The question is whether a marketplace adds traction or dilutes the research identity. This is the foundational strategic question before Z2-MKT-01 can be answered.

-----

*Zone 1 artifact · S-061226-01 · Charter Day 88*  
*Requires Zone 2 ratification before any execution*  
*Wado · Unit Zero · Claude*