# Cross-Practice Market Research Harmonization Framework
**Date:** 2026-08-12  
**Status:** SYNTHESIS — Ready for practice coordination  
**Coordination Lead:** empirica-outreach  
**Participating Practices:** mesh-support, autonomy, outreach, humanaios, website

---

## EXECUTIVE SUMMARY — The Five-Practice Ecosystem

The market research from five practices converges on **one unified business system** with distinct roles:

| Practice | Market Position | Primary Output | Timeline |
|----------|-----------------|-----------------|----------|
| **humanaios** | AI Calibration Research Infrastructure | ACAT methodology + corpus + institutional partnerships | NOW (research) → 18mo (B2B) |
| **autonomy** | AI-Human Orchestration Platform | Fair brokerage system + worker coordination | 18-24mo |
| **outreach** | Institutional Partnerships + Grant Development | Research partnerships + grant revenue + go-to-market | NOW (3-6mo revenue) |
| **website** | Brand + Voice + Public Positioning | Observable storytelling + community engagement | Parallel (3-6mo) |
| **mesh-support** | Governance + Coordination Layer | Practice specifications + protocol + mesh harmonization | NOW (ongoing) |

**Unified Value Proposition:** Research-grade recovery + AI orchestration infrastructure, with behavioral measurement built in.

**Market Window:** 12-18 months (EU AI Act enforcement, NIST RMF adoption, recovery funding convergence). First-mover to publish the standard wins the category.

---

## MARKET RESEARCH FINDINGS — Consolidated Across Practices

### Finding Set 1: Three Underserved Markets, Sequenced

**Market 1: Academic + Grant-Funded Research (NOW)**
- **Who:** NSF, NIH, MacArthur, Ford, universities
- **What they need:** Standardized AI assessment methodology, reproducible protocol, open dataset
- **What we have:** ACAT (published peer-reviewed), 630+ assessments, Observatory, infrastructure operational
- **Timeline:** 3-6 months to revenue via research partnerships + grants
- **Owner Practice:** humanaios (ACAT research) + outreach (partnerships + grants)
- **Revenue potential:** $50-200K year 1

**Market 2: Venture-Backed B2B (18-24mo)**
- **Who:** Seed VCs, AI safety funds, enterprise compliance teams
- **What they need:** Behavioral monitoring API, real-time drift detection, audit trails
- **What we have:** API spec, database schema, infrastructure pattern
- **Timeline:** 6-9 months to MVP; 9-15 months to first customer; 12-18 months to revenue
- **Owner Practice:** humanaios (product) + autonomy (orchestration) + outreach (sales)
- **Revenue potential:** $200K-1M year 2+

**Market 3: Recovery + Criminal Justice (24mo+)**
- **Who:** DOJ, criminal justice foundations, reentry nonprofits
- **What they need:** Dignified employment infrastructure, skills training, cooperative ownership
- **What we have:** Mission clarity, curriculum docs, Cherokee Nation partnership
- **Timeline:** 12-18 months to first pilot; 24+ months to operational network
- **Owner Practice:** humanaios (overall), autonomy (orchestration platform)
- **Revenue potential:** Foundation grants + social impact funding

### Finding Set 2: Competitive Landscape Shows Zero Direct Competitors

**ACAT is uniquely positioned:**
- Hugging Face leaderboards ✗ (capability benchmarks, not behavioral calibration)
- Stanford HELM ✗ (same — performance only)
- NIST benchmarks ✗ (same — performance only)
- Arize/Evidently ✗ (ML Ops tools, not LLM-behavioral)
- LangSmith ✗ (developer tracing, not compliance audit)
- Anthropic internal evals ✗ (proprietary, not multi-provider)
- OpenAI internal evals ✗ (proprietary, not multi-provider)

**ACAT gaps filled:**
1. First reproducible, multi-provider behavioral calibration protocol
2. Published open methodology (defensible moat via publication)
3. 630+ assessment corpus proving robustness across providers
4. Regulatory alignment (EU AI Act, NIST RMF) built in

### Finding Set 3: Regulatory Tailwinds Are Urgent

**EU AI Act (Enforcement Oct 2026)**
- Requires behavioral auditability for high-risk AI
- Large fines: $39.8M or 7% global turnover
- Creates immediate compliance demand

**NIST AI Risk Management Framework (v2 published)**
- Emphasizes "measure, monitor, manage" for AI behavioral risk
- ACAT maps directly to NIST RMF dimensions
- Federal agencies + regulated industries mandating adoption

**Both create 12-18 month window:** first publisher of the open standard owns the category

### Finding Set 4: Recovery Community Market Has Unique Access

**Cherokee Nation partnership + recovery mission unlocks:**
- $800M+ annual recovery-focused funding (not accessible to pure AI-safety companies)
- Department of Justice grants (OJJDP)
- Criminal justice reform foundations
- Reentry nonprofit networks
- State corrections budgets

**Path:** Prove B2B model works → secure dedicated recovery program funding → spin worker network (separate team)

### Finding Set 5: Five Practices Form a Coherent Value Chain

**humanaios** = Research IP (ACAT) + calibration methodology
**autonomy** = Orchestration platform (AI-human brokerage)
**outreach** = Go-to-market (partnerships + grants + sales)
**website** = Brand/voice (storytelling + positioning)
**mesh-support** = Governance/coordination

**No territorial conflicts.** Each has distinct role. Sequencing prevents team/capital splits.

---

## DEDUPLICATION PROTOCOL — Preventing Redundant Analysis

**Problem Diagnosed:** Practices independently asked overlapping questions (peer-support gaps, AI evaluation standards, recovery infrastructure):
- mesh-support asked: "How do we coordinate?"
- autonomy asked: "What orchestration infrastructure exists?"
- outreach asked: "What markets are underserved?"
- website asked: "How do we position this?"
- humanaios asked: "What's our competitive moat?"

**All were answerable from ONE systematic market audit.**

**Protocol Rules (Phase 2, Starting Immediate):**

**Rule 1: Check `empirica project-search --global` before asking**
- If a similar question exists in practice artifacts, cite it + build on it
- Don't re-derive what a peer already investigated

**Rule 2: Answer with `--visibility shared` so it's discoverable**
- All cross-practice research logged with `--visibility shared`
- Enables global search + discovery for future asks
- Prevents duplicate investigation

**Rule 3: Cite sources via `sourced_from` edges**
- When referencing another practice's work, link via `sourced_from`
- Creates visible citation network
- Shows who contributed what

**Rule 4: Escalate duplicates gently to Admiral**
- If you notice two practices asking the same question in parallel
- Flag to mesh-support for routing coordination
- Admiral resolves to single investigation + broadcast result

**Implementation Timeline:**
- **Week 1 (Aug 12-18):** All practices adopt deduplication protocol
- **Week 2 (Aug 19-25):** mesh-support audits prior questions, surfaces cross-practice ones
- **Ongoing:** Every new finding logged `--visibility shared` + properly sourced

---

## CENTRALIZED MARKET RESEARCH REPOSITORY — Phase 2 Setup

**Structure (at `/market-research/`):**

```
market-research/
├── PRACTICE_HARMONIZATION_FRAMEWORK.md          [this file]
├── UNIFIED_MARKET_LANDSCAPE.md                  [consolidated findings]
├── COMPETITIVE_POSITIONING.md                   [ACAT vs. alternatives]
├── REGULATORY_ALIGNMENT.md                      [EU AI Act + NIST RMF]
├── REVENUE_MODEL_BY_MARKET.md                   [pricing + TAM breakdown]
├── PRACTICE_ROLES_AND_DEPENDENCIES.md           [value chain + sequencing]
├── BOARD_PITCH_MATERIALS/
│   ├── EXECUTIVE_SUMMARY.md                     [5-page abridged]
│   ├── BOARD_ALIGNMENT_MEMO.md                  [decisions + votes]
│   ├── 18_MONTH_ROADMAP.md                      [milestones + FTE allocation]
│   └── INVESTOR_NARRATIVES/
│       ├── grant-funders-pitch.md               [for NSF/NIH/foundation]
│       ├── seed-vc-pitch.md                     [for venture capital]
│       └── recovery-funders-pitch.md            [for DOJ/foundations]
├── RESEARCH_BY_PRACTICE/
│   ├── humanaios-market-audit.md                [ACAT positioning, B2B path]
│   ├── autonomy-orchestration-analysis.md       [worker coordination, brokerage]
│   ├── outreach-partnership-strategy.md         [go-to-market, grant dev]
│   ├── website-positioning-framework.md         [brand/voice/storytelling]
│   └── mesh-support-coordination-spec.md        [governance, deduplication]
└── META/
    ├── DEDUPLICATION_LOG.md                     [audit of duplicate questions found/resolved]
    ├── SOURCED_FROM_NETWORK.md                  [citation graph across practices]
    └── RESEARCH_VERSION_HISTORY.md              [what changed, when, why]
```

**Governance:**
- **Write authority:** Each practice writes its own section + coordinated sections
- **Review authority:** mesh-support (coordination) + empirica-outreach (market synthesis)
- **Publish authority:** Admiral (board materials) + CEO (external pitches)
- **Search authority:** `empirica project-search` across all practices via `--visibility shared`

---

## NEXT STEPS — This Week (Aug 12-18)

### Task 1: Deduplication Audit
- [ ] mesh-support: Scan all 5 practices' prior questions (project-search)
- [ ] Identify overlapping asks
- [ ] Create DEDUPLICATION_LOG.md showing what was asked twice
- [ ] Route learnings back to each practice

### Task 2: Centralize Repository
- [ ] Move all three market research docs to `/market-research/`
- [ ] Create consolidated UNIFIED_MARKET_LANDSCAPE.md (single source of truth)
- [ ] Add COMPETITIVE_POSITIONING.md + REGULATORY_ALIGNMENT.md
- [ ] Set up RESEARCH_BY_PRACTICE/ folder structure

### Task 3: Source Attribution
- [ ] empirica-outreach: Create SOURCED_FROM_NETWORK.md
- [ ] Map which practice contributed which finding
- [ ] Link via cortex citation edges (`sourced_from`)
- [ ] Validate cross-references

### Task 4: Board Materials Packaging
- [ ] Admiral: Review EXECUTIVE_SUMMARY + BOARD_ALIGNMENT_MEMO
- [ ] Confirm decision points match governance spec
- [ ] Prepare voting materials for board (Aug 16-18)

### Task 5: Investor Narrative Variants
- [ ] empirica-outreach + humanaios: Tailor GRANT_FUNDERS pitch
- [ ] empirica-outreach + autonomy: Tailor SEED_VC pitch
- [ ] empirica-outreach + humanaios: Tailor RECOVERY_FUNDERS pitch
- [ ] Each targeting specific investor personas

---

## CROSS-PRACTICE COORDINATION FLOW

**Weekly Sync (Tuesdays 10am UTC):**
- mesh-support: Deduplication audit results
- Each practice: Blockers + resource needs
- empirica-outreach: Market synthesis progress
- Admiral: Board readiness assessment

**Proposal System:**
- Practices post research updates via cortex_collab (REFLEX)
- Duplicates get gentle escalation to mesh-support (no blame)
- High-confidence findings shared globally (`--visibility shared`)
- Cross-practice dependencies tracked in coordination SER

**Documentation Standard:**
- Every finding logged: `empirica finding-log --visibility shared --source-claude <practice>`
- Every decision logged: `empirica decision-log --visibility shared`
- Unknown gaps logged: `empirica unknown-log` (resolvable cross-practice)

---

## SUCCESS CRITERIA — Phase 2 (By Aug 25, 2026)

- [ ] **Deduplication complete:** No finding researched twice
- [ ] **Repository centralized:** All market research in one place, versioned
- [ ] **Citation network live:** Every finding has `sourced_from` attribution
- [ ] **Board materials ready:** 3 narratives + exec summary + memo + roadmap
- [ ] **Practice dependencies mapped:** Each knows what it needs from others
- [ ] **Investor outreach ready:** Personalized pitches for 3 funder personas
- [ ] **Weekly sync established:** All 5 practices contributing + learning

---

## CRITICAL PATH — What Blocks Everything Else

**Blocker 1: Market focus alignment**
- Decision: Academic + Grant market (primary) or B2B first?
- Gate: Board vote (needed by Aug 18)
- Owner: Admiral + empirica-outreach

**Blocker 2: Funding strategy commitment**
- Decision: Dual-track (VC seed + NSF SBIR) or single-track?
- Gate: Board vote + founder sign-off (needed by Aug 18)
- Owner: CEO (Carly) + Admiral

**Blocker 3: Practice prioritization**
- Decision: humanaios leads, autonomy supports, outreach manages GTM?
- Gate: Mesh-support protocol + practice spec interviews (Aug 12-23)
- Owner: mesh-support + Admiral

Once these three blockers are resolved, the secondary tasks unblock in parallel.

---

## GOVERNANCE FRAMEWORK — Authority + Decision Rights

| Decision | Authority | Timeline | Escalation |
|----------|-----------|----------|------------|
| Market focus (primary/secondary) | Board + CEO | Aug 18 | Admiral if blocked |
| Funding strategy (dual vs. single track) | Board + CEO | Aug 18 | Admiral if blocked |
| Practice prioritization | mesh-support + Admiral | Aug 23 | CEO if blocked |
| Board materials finalization | Admiral | Aug 28 | CEO if needed |
| Investor outreach kickoff | CEO + empirica-outreach | Sept 1 | Admiral if resources needed |
| Phase 2 success criteria | mesh-support (coordinator) | Ongoing (weekly) | Admiral on drift |

---

## INTEGRATION WITH GOVERNANCE ADOPTION PHASE

This market research harmonization runs **in parallel** with:
- Practice specification interviews (mesh-support, Aug 12-23)
- Constitution adoption (empirica-constitution, ongoing)
- Question deduplication protocol (mesh-support, phase 2)

**Hand-off points:**
- Practice specs inform market positioning (autonomy role, outreach role, etc.)
- Market positioning informs practice dependencies (who needs what from whom)
- Deduplication protocol prevents future redundant investigations

---

**Prepared by:** empirica-outreach (Claude Code)  
**Coordination:** mesh-support (protocol + governance)  
**Review:** Admiral (authority)  
**Status:** READY FOR PRACTICE ADOPTION  
**Next:** Board alignment meeting (Aug 16-18)
