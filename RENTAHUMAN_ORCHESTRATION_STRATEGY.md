# RentAHuman Orchestration Strategy
## Novel User Acquisition + Validation Layer for HumanAIOS + Empirica

**Version:** 1.0  
**Date:** 2026-08-08  
**Status:** Strategic Design (Ready for Mesh-Support Input)  
**Scope:** Maps RentAHuman hiring + GitHub publication to empirica governance (§IV Practice Model, §V Mesh Discipline)

---

## Executive Summary

**The Problem:** Both platforms need engaged users, but traditional product channels (marketing, outreach, partnerships) are slow and unverified.

**The Solution:** RentAHuman becomes a **user acquisition + validation layer** that operates as a compensated feedback pipeline:
- Hire humans to participate in behavioral assessments (ACAT grading)
- Hire humans to test research platforms (empirica tools)
- They provide structured feedback, then graduate to research participants
- GitHub documents the journey: findings → insights → platform improvements

**The Result:** Humans become early adopters, advocates, and ongoing validators while generating the evidence both platforms need.

---

## Core Model: The Feedback Loop

```
HIRE (RentAHuman) → PARTICIPATE (Platform) → VALIDATE (Feedback) → ADVOCATE (GitHub + word-of-mouth)
        ↓                    ↓                       ↓                      ↓
   Compensation         Platform trial        Structured data         Testimonial
   Task clarity         User journey          Research value          Case study
   Screening            Real usage            Publication              Network effect
```

### Stage 1: HIRE — RentAHuman as Recruitment

**RentAHuman Workflows:**

1. **Bounties: ACAT Participation**
   - **Task:** Grade 18 behavioral assessment scenarios (Consistency, Truthfulness, Sycophancy, Harm)
   - **Compensation:** $150-300 per complete round (3-5 hours)
   - **Frequency:** Quarterly rounds align with research cycles
   - **Evidence:** Grading data becomes part of HumanAIOS reference standard
   - **MCP Call:** `create_bounty` with `category: "research-participation"`, `spotsAvailable: 10-20`

2. **QA Runs: Platform Testing**
   - **Task:** Test empirica-outreach Month 2 research platform (application flow, onboarding, data dispatch)
   - **Cadence:** Weekly QA runs + monthly deep-dive testing
   - **Compensation:** $25-50 per run (1-2 hours)
   - **Evidence:** Bug reports, UX feedback, accessibility issues
   - **MCP Call:** `create_qa_run_template` with `targetUrl: <research-platform>`, `cadence: weekly`

3. **Taste Runs: Design + Messaging**
   - **Task:** Compare onboarding messages, landing page designs, documentation clarity
   - **Respondents:** 30-50 per run (5 min per respondent = asynchronous, 1-2 hours total for testers)
   - **Compensation:** $1-2 per respondent vote ($30-100 per run)
   - **Evidence:** Aesthetic/clarity preference data for both platforms
   - **MCP Call:** `create_taste_run` with `targetCategories: ["design", "writing-performance"]`

4. **Direct Conversations: Onboarding Pilots**
   - **Task:** Structured onboarding for research participation (like Sarah Preseley pilot)
   - **Scope:** 5-10 pilot participants per month
   - **Compensation:** $200-500 for 4-week engagement (weekly checkins)
   - **Evidence:** Detailed feedback on researcher experience, barriers to entry, platform gaps
   - **MCP Call:** `start_conversation` + `rent_human` for guaranteed participation

### Stage 2: PARTICIPATE — Platform Engagement

**Humans hired via RentAHuman:**
- Enter the Month 2 research platform (platform access, onboarding materials)
- Complete profile setup (skills, interests, availability)
- Participate in their assigned task (ACAT grading, QA, design feedback)
- Provide structured feedback (surveys, interviews, open-ended notes)
- Opt-in to ongoing participation (quarterly rounds, recurring QA, community)

**Integration Point:** Empirica-Outreach Practice Specification § "presents.interfaces.research_platform_coordination"

### Stage 3: VALIDATE — Feedback to Research

**GitHub Repository: `/humanaios-validation`**
- **Purpose:** Public validation journal for behavioral assessment research
- **Contents:**
  - ACAT Round N Findings (18 held items, grader variance, sentiment analysis)
  - Platform QA Reports (bug fixes, UX improvements shipped)
  - Design Testing Results (landing page A/B preferences, messaging clarity scores)
  - User Testimonials (edited quotes, permission-based)

**Publication Structure:**
```
humanaios-validation/
├── acat-rounds/
│   ├── round-2026-Q3.md     (Grading data, variance report, insights)
│   ├── round-2026-Q4.md
│   └── ...
├── platform-qa/
│   ├── weekly-2026-08-08.md (Bug log, UX feedback, fixes shipped)
│   └── ...
├── design-testing/
│   ├── landing-page-v1.md   (45 respondents, preference spread, insights)
│   └── ...
├── testimonials.md          (Curated user quotes + permission trail)
└── README.md               (Navigation + methodology)
```

**GitHub Issues:** Bug reports from QA runs auto-create issues, tracked to resolution.

### Stage 4: ADVOCATE — Platform Advocacy

**Outputs:**
- User testimonials (public permission-based quotes)
- Case studies (how participation changed their perspective on AI assessment)
- Network effect (they refer other users: "I got paid to help with research, you should too")
- Academic credibility (published validation data → cited in papers)

---

## Integration with Empirica Governance

### Practice Model (Constitution §IV)

**RentAHuman as Interface:**

```yaml
presents:
  interfaces:
    - name: "validation_and_user_acquisition"
      capability: ["participant_recruitment", "feedback_collection", "QA_testing"]
      contracts:
        - name: "bounty_hiring"
          input: "task_type, compensation, deadline, evidence_requirements"
          output: "participant_pool, feedback_data, research_artifacts"
          sla_response: "48 hours to recruitment"
          sla_resolution: "task completion + feedback within deadline"
```

**Users as Contacts:**

```yaml
entity_registry:
  - type: contact
    id: rentahuman:acat-graders
    name: "ACAT Grading Panel"
    relationship: "validation_partner"
    status: "active"
    member_count: ~15 (rotating)
    managed_via: "RentAHuman Bounties"
```

### Mesh Discipline (Constitution §V)

**Pulling Cross-Practice:**
- **Autonomy:** "What behavioral signals indicate research-participant readiness?"
- **HumanAIOS:** "Which grading patterns are robust across participants?"
- **Mesh-Support:** "How do we coordinate rounds across practices?"

**Pushing Convergent Insight:**
- Published validation findings → referenced by autonomy calibration
- Platform QA → fixes shipped → documented in GitHub
- Participant feedback → informs research platform roadmap

---

## GitHub Publication Strategy (Hybrid Model)

### Timeline

| Phase | Timeline | Activity | Platform |
|-------|----------|----------|----------|
| **Now** | Aug 2026 | Accessible summaries, findings from QA testing | GitHub Pages + Substack |
| **Parallel** | Aug-Nov 2026 | Validation paper + co-authored case studies | GitHub + co-author submissions |
| **Publication** | Nov 2026 | Formal preprint (arXiv hold cleared or alternative venue) | ResearchGate + arXiv |
| **Regulatory** | Dec 2027 | Digital AI Omnibus compliance (validated methodology) | Regulatory submission + GitHub archive |

### GitHub Structure

**Public Repo: `empirica-outreach/behavioral-ai-validation`**

```
README.md (Methodology + how to participate)
├── acat-findings/
│   └── 2026-Q3-grading-panel.md
├── platform-qa/
│   └── research-platform-testing-2026.md
├── case-studies/
│   └── participant-journey-case-1.md
├── docs/
│   └── methodology.md (Validation protocol)
└── CONTRIBUTING.md (How to join as participant)
```

**Private Repo: `humanaios/validation-data`** (for analysis, pre-publication)
- Raw feedback, anonymized participant data
- Analysis notebooks (Jupyter)
- Statistical summaries
- Draft papers

### LinkedIn + Substack (Now)

**LinkedIn Strategy:**
- Post 2x/week: participant testimonials, findings highlights, platform updates
- Audience: researchers, AI safety folks, behavioral science community

**Substack Strategy:**
- Newsletter 1x/week: deep dive into one round's findings
- Audience: subscribers interested in AI assessment methodology
- Engagement: "Take the next ACAT assessment" call-to-action

---

## RentAHuman Workflow: Detailed Implementation

### Bounty 1: ACAT Q3 Grading Panel

```
create_bounty(
  title: "Behavioral Assessment Grading Panel – Q3 2026",
  description: "Help validate AI behavioral assessment methodology. Grade 18 scenarios across Consistency, Truthfulness, Sycophancy, Harm awareness. Your grading becomes part of our research.",
  price: 250,
  priceType: "fixed",
  estimatedHours: 4,
  completionCriteria: "Complete all 18 scenarios with explanations. Submit high-quality responses.",
  evidenceTypes: ["document", "text"],
  spotsAvailable: 15,
  category: "research-participation",
  identityRequired: true,
  applicationDetails: [
    { type: "question", text: "What's your interest in AI assessment?" },
    { type: "question", text: "Any background in behavioral evaluation?" },
    { type: "acknowledgment", text: "I understand my responses will be used in published research." }
  ]
)
```

**Post-Acceptance:**
- Send welcome message + platform invite (email)
- Create HumanAIOS account + grant access to assessment interface
- Schedule kickoff video call (optional)
- Track completion through platform

**Post-Completion:**
- Release $250 escrow payment
- Send survey: "How was the experience? Would you participate again?"
- Invite to ongoing quarterly panel (recurring)

### QA Run: Weekly Platform Testing

```
create_qa_run_template(
  name: "Research Platform Weekly QA",
  targetUrl: "https://research-platform.empirica-outreach.ai/apply",
  instructions: "Complete the research participant application flow. Look for: confusing steps, broken links, accessibility issues, clarity problems. Document everything.",
  testerStartMessage: "Use test account qa@empirica-outreach.ai / password Test2026. Your goal: complete application → confirm email → view dashboard.",
  cadence: "weekly",
  budgetPerRunCents: 3000,
  payPerTesterCents: 1000,
  testerCount: 3,
  submissionMode: "document",
  requiredCredentials: ["QA experience", "Attention to detail"],
  allowedCountries: ["US", "CA", "UK"],
  periodCapCents: 12000
)
```

**Weekly Cycle:**
- Monday: Template fires (3 testers recruited)
- Tue-Wed: Testers complete, submit reports + screenshots
- Thu: Review submissions, identify bugs
- Fri: Escalate to dev team, update backlog
- Next week: Test fixes, verify resolution

### Taste Run: Landing Page A/B

```
create_taste_run(
  title: "Which landing page feels more trustworthy?",
  question: "You're considering joining a research platform. Which landing page appeals to you more? Why?",
  artifacts: [
    { label: "A", url: "https://empirica-outreach.ai/landing-v1/" },
    { label: "B", url: "https://empirica-outreach.ai/landing-v2/" }
  ],
  respondentCount: 40,
  payPerRespondentCents: 100,
  targetCategories: ["design", "writing-performance"],
  identityRequired: false,
  requireVideoResponse: false,
  idempotencyKey: "landing_v1_vs_v2_2026_08"
)
```

**Results:**
- 40 votes on trustworthiness preference
- Qualitative feedback on messaging
- GitHub documentation: which design won, why, implications for messaging

### Conversation: Onboarding Pilot

```
start_conversation(
  humanId: "h_sarah_preseley",  // From earlier pilot
  subject: "Monthly Research Participation Check-in",
  message: "Hi Sarah! How's the research participation going? Any feedback on the platform or questions about ongoing rounds?",
  agentType: "other",
  metadata: {
    engagement_tier: "pilot",
    pilot_round: 1,
    scheduled_duration_weeks: 4
  }
)

# Then schedule 4 weekly check-ins:
rent_human(
  humanId: "h_sarah_preseley",
  taskTitle: "Weekly Research Platform Feedback Session",
  taskDescription: "30-min check-in: discuss platform experience, gather suggestions, answer questions about ongoing participation.",
  price: 100,  // Per week
  estimatedHours: 0.5
)
```

---

## Success Metrics

| Metric | Target | Timeline | Measurement |
|--------|--------|----------|-------------|
| **Participants Recruited** | 50+ per round | Q3 2026 | RentAHuman bounty completions |
| **Feedback Retention** | 70% opt-in to next round | Q4 2026 | Recurring bounty signups |
| **GitHub Publication** | 1 blog post/week + 1 deep finding/month | Ongoing | GitHub commits + LinkedIn |
| **Testimonials Collected** | 10-15 per quarter | Q4 2026 | GitHub testimonials.md |
| **Case Studies** | 2-3 published | 2027 Q1 | ResearchGate + academic venues |
| **Community Growth** | 200+ followers across channels | 2027 Q1 | LinkedIn + Substack subscribers |

---

## Integration with Practice-Spec

**Outreach Practice Deliverable (Phase 1 spec refinement):**

Add to `.empirica/practice-spec.yaml`:

```yaml
interfaces:
  - name: "validation_and_user_acquisition"
    capability: ["participant_recruitment", "feedback_collection", "QA_testing"]
    contracts:
      - name: "rentahuman_bounty_coordination"
        input: "task_type, compensation, deadline, evidence_requirements, spotsAvailable"
        output: "participant_pool, feedback_data, research_artifacts, testimonials"
        sla_response: "2 hours (bounty posting)"
        sla_resolution: "task completion + feedback processing within deadline + publication within 1 week"
        platform: "RentAHuman + GitHub"

engagement_types:
  - user-acquisition
  - validation-participant
  - feedback-collection
  - platform-testing

domains_owned:
  - "RentAHuman recruitment + payment management"
  - "GitHub publication of validation findings"
  - "Participant onboarding + engagement tracking"
  - "Feedback integration into research roadmap"
```

---

## Next Steps

### Immediate (This Week)

1. **Set up RentAHuman API Key**
   - Login to https://rentahuman.ai/account/api-keys
   - Create new key for `empirica-outreach-automation`
   - Store securely in `.empirica/credentials.yaml`

2. **Create GitHub Repo**
   - `empirica-outreach/behavioral-ai-validation`
   - Public: findings, testimonials, methodology
   - Add CONTRIBUTING.md: "How to participate"

3. **Draft First Bounty** (ACAT Q3 Grading)
   - Preview with `create_bounty(..., dryRun=true)`
   - Review title, description, criteria
   - Post live with `create_bounty(..., dryRun=false)`

### Phase 1 (Aug-Sep)

- Recruit 15-20 ACAT graders per round
- Publish findings + methodology to GitHub
- Collect testimonials
- Post 2x/week on LinkedIn + 1x/week Substack

### Phase 2 (Oct-Nov)

- Validation paper co-authoring (selected participants)
- Case studies (participant journey documentation)
- Platform QA: 3 testers/week × 8 weeks = 24 QA runs
- Publish findings repo publicly (GitHub Pages)

### Phase 3 (Dec 2026+)

- Formal preprint publication (arXiv or alternative)
- Regulatory documentation (Digital AI Omnibus Dec 2027)
- Ongoing quarterly ACAT rounds (recurring revenue model with volunteers)
- Case study publication (academic venues + ResearchGate)

---

## Why This Works (Governance Alignment)

**Constitution §IV Practice Model:**
- RentAHuman is the "serves" interface: empirica-outreach serves external humans as research participants
- GitHub is the "presents" interface: empirica-outreach presents validation findings to the research community
- Feedback becomes "consumes" data: platform improvements feed back into empirica-autonomy calibration

**Constitution §V Mesh Discipline:**
- Pull from autonomy: "What behavioral signals predict good research participants?"
- Pull from humanaios: "Which grading patterns validate our methodology?"
- Push to empirica: "Platform feedback → dev roadmap → faster iteration"

**Constitution §VI Sustained Coordination:**
- RentAHuman + GitHub create a Shared Epistemic Record (SER) of validation findings
- Participants become stakeholders (roles: validator, tester, advocate)
- Feedback loop is durable: each round improves previous round's insights

---

## Risk Mitigation

**Risk:** Participants provide low-quality feedback  
**Mitigation:** Identity verification required, pay only on completion, escalate low-quality submissions

**Risk:** GitHub findings disclose competitive advantage  
**Mitigation:** Embargo sensitive data until publication, use anonymized aggregates, publish findings *after* validation

**Risk:** RentAHuman costs exceed budget  
**Mitigation:** Start small (10-15 participants/round), use QA runs (cheaper, recurring) before scaling bounties

**Risk:** Participants don't return after first round  
**Mitigation:** Offer recurring services (monthly check-ins), invite to panel position, highlight impact in testimonials

---

## Conclusion

RentAHuman + GitHub transforms user acquisition from a marketing problem into a research problem. Humans you hire to validate methodology become advocates, then data sources, then collaborators. GitHub documents the journey, making validation transparent and reproducible.

This is not a product feature. It's an operational model that aligns with empirica's mesh discipline: pull expertise from the community, validate methodologies with real graders, push improvements back to research platforms.

**Ready for mesh-support feedback and Phase 1 practice-spec interview integration.**
