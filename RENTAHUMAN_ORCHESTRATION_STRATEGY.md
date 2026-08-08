# RentAHuman Orchestration Strategy (REVISED)
## Revenue Generation Model — From Expense Center to Profit Center

**Version:** 2.0 (REVISED 2026-08-08)
**Date:** 2026-08-08  
**Status:** Revenue-Focused Model (Governance Collab Sent)
**Scope:** RentAHuman as referral bonus revenue stream + resource allocation governance

---

## Executive Summary

**The Problem:** Empirica-foundation is at -$500 cash flow. Traditional user acquisition (hiring via bounties) is an expense center, not a revenue stream.

**The Pivot:** RentAHuman becomes a **revenue generation mechanism** that recruits users who:
- Join RentAHuman to earn money (they earn $200-500/month from gigs)
- We earn referral bonuses (5-10% of their earnings or flat fee structure)
- They simultaneously become validators/users of our platforms
- GitHub documents the impact: recruitment → validation → platform advocacy

**The Result:** Organizational revenue of $250-1000/month (from 5-10 active users), cash-flow positive, reinvestable in validation + user acquisition.

---

## Core Model: Revenue-Driven Recruitment Loop

```
RECRUIT (RentAHuman) → EARN (Gigs) → REFER (Referral Bonus) → VALIDATE (Platforms) → ADVOCATE (Community)
        ↓                    ↓                  ↓                      ↓                      ↓
   People seeking work   $200-500/mo      $50-100/mo per user    Platform testing      Testimonials
   Screening validated   Real gigs       Organizational revenue   Feedback loop         Network effect
   Self-selected pool    High motivation  Cash flow positive     Research data         User acquisition
```

### Stage 1: RECRUIT — RentAHuman as Revenue Generator

**RentAHuman Revenue Mechanisms:**

1. **Recruitment: RentAHuman Gig Economy Access**
   - **Approach:** Recruit people (via LinkedIn, community, networks) to join RentAHuman
   - **Their earning:** $200-500/month from available gigs (research, writing, rating, testing, etc.)
   - **Our earning:** 5-10% referral bonus on their earnings, OR flat $50-100 per active user/month
   - **Frequency:** Continuous recruitment (target 5-10 active users by end of Q3)
   - **Target:** 10 active users × $75/month avg referral = $750/month organizational revenue
   - **Mechanism:** RentAHuman affiliate link + monthly tracking dashboard
   - **URL:** RentAHuman Affiliates portal (https://rentahuman.ai/affiliates)

2. **Validation Layer: Platform Testing + Feedback**
   - **Mechanism:** Recruit users ALSO ask them to test/validate our platforms (optional, incentivized)
   - **Task:** Test empirica-outreach Month 2 research platform (application flow, onboarding)
   - **Benefit:** They provide feedback (voluntary, becomes part of validation dataset)
   - **Our cost:** Minimal (already earning via RentAHuman, we just ask for feedback)
   - **Evidence:** Bug reports, UX insights, usage patterns = validation without expense
   - **Integration:** "As a RentAHuman user, you're invited to help shape our research platform"

3. **Research Participation: ACAT Grading (Optional Upcharge)**
   - **When:** ONLY if user opts into higher-value ACAT grading work
   - **Scope:** Grade 18 behavioral assessment scenarios quarterly (NOT a hired service, but offered to community)
   - **Payment model:** Direct payment ($150-300) from HumanAIOS research budget (separate from referral model)
   - **Evidence:** Grading data becomes part of HumanAIOS reference standard
   - **Difference from old model:** NOT a primary recruitment mechanism; optional for engaged users

4. **Community Advocacy: Testimonials + Case Studies**
   - **Task:** Users document their RentAHuman earning journey + platform participation
   - **Compensation:** Optional ($20-50 per testimonial), but mostly organic advocacy
   - **Evidence:** Real success stories for recruitment/retention
   - **Channels:** LinkedIn, Substack, GitHub (with permission)

### Stage 2: PARTICIPATE — Earn via RentAHuman + Validate Our Platforms

**Humans recruited via referral:**
- Sign up for RentAHuman using our affiliate link
- Start earning $200-500/month from available gigs (research, writing, rating, testing)
- We earn 5-10% referral bonus per active user
- **Optional:** Get invited to beta-test/validate our research platform (Month 2)
- **Optional:** Participate in ACAT grading rounds (higher-value work, direct payment)
- Provide feedback naturally (surveys, interviews, casual notes)
- Become advocates in their networks ("I earn money on RentAHuman, they also have a research platform")

**Integration Point:** Empirica-Outreach Practice Specification § "presents.interfaces.validation_and_user_acquisition"

**Key Difference:** Revenue FIRST (via referrals), validation SECOND (organic feedback from active users). We're not hiring users; we're recruiting them to a platform that pays them, and capturing value through referrals + feedback.

### Stage 3: VALIDATE — Community Feedback Loop

**GitHub Repository: `/empirica-outreach-community`** (public community log)
- **Purpose:** Real-time community insights from RentAHuman users testing our platform
- **Contents:**
  - User Testimonials (RentAHuman earning journey + platform feedback)
  - Monthly Cohort Reports ("10 users joined in July, here's what they discovered")
  - Platform Learnings (bugs found, feature requests, UX improvements shipped)
  - Case Studies ("How I earn $300/month on RentAHuman + validate AI research")

**Publication Structure:**
```
empirica-outreach-community/
├── testimonials/
│   ├── user-1-story.md      (Earnings, experience, impact)
│   ├── user-2-story.md
│   └── ...
├── monthly-cohorts/
│   ├── 2026-08-cohort.md    (10 users, aggregate feedback, themes)
│   └── ...
├── platform-learnings/
│   ├── bug-2026-08-01.md    (Found via user testing)
│   └── ...
├── impact-metrics.md        (Revenue, users, retention, feedback volume)
└── README.md               (How to join, eligibility, process)
```

**Feedback Mechanism:** Low-friction (Slack channel, monthly survey, optional interviews)

### Stage 4: ADVOCATE — Organic Network Growth

**Outputs:**
- User referrals ("My friend is earning money on RentAHuman, and they're helping research AI too")
- LinkedIn posts (users sharing their journey: "Earning $X/month on RentAHuman + helping shape research")
- Community testimonials (low-lift, permission-based quotes)
- Network amplification (each user recruits 1-2 more friends → viral loop)

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

## Success Metrics (Revenue-Focused)

| Metric | Target | Timeline | Measurement |
|--------|--------|----------|-------------|
| **Active Users** | 5-10 users | End Q3 2026 | RentAHuman referral dashboard |
| **Monthly Referral Revenue** | $250-1000/month | Q4 2026 | Earnings report from RentAHuman |
| **Cash Flow** | -$500 → +$500/month | Q4 2026 | Monthly accounting ledger |
| **User Retention** | 70%+ retention month-to-month | Ongoing | Active user churn rate |
| **Validation Feedback** | 1 finding/month from user testing | Ongoing | GitHub issues + user surveys |
| **GitHub Publication** | 1 cohort report/month + testimonials | Ongoing | GitHub commits + LinkedIn |
| **Testimonials Collected** | 5-10 per quarter | Q4 2026 | GitHub testimonials.md (permission-based) |
| **Community Growth** | 100+ followers across channels | 2027 Q1 | LinkedIn + Substack + RentAHuman community |
| **Reinvestment** | Once cash-flow positive, 20% of revenue to validation | 2027 Q1 | Allocations to ACAT grading, platform QA |

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

## Next Steps (Revenue-Focused)

### Immediate (This Week — Aug 8)

1. **Set up RentAHuman Affiliate Account**
   - Login to https://rentahuman.ai/affiliates
   - Create affiliate link for empirica-outreach
   - Store link + API key securely in `.empirica/credentials.yaml`
   - Enable affiliate dashboard for revenue tracking

2. **Create GitHub Community Repo**
   - `empirica-outreach/community`
   - Public: testimonials, cohort reports, platform learnings
   - Add README: "Join us on RentAHuman + help shape research"
   - Add TESTIMONIALS.md template for user stories

3. **Recruitment Strategy Document**
   - Identify 5-10 target people (LinkedIn connections, networks, communities)
   - Draft recruitment message: "Earn $200-500/month on RentAHuman, plus help shape AI research"
   - Plan outreach channels (LinkedIn DM, email, Slack communities, Discord)

### Phase 1 (Aug 15-Sep 15)

- Recruit 5-10 active RentAHuman users (target: $100-500/month referral revenue)
- Launch community GitHub repo with 3-5 initial testimonials
- Post 2x/week on LinkedIn + 1x/week Substack (focus: earning + research impact)
- Monthly cohort report (Aug users, feedback, discoveries)
- Track referral revenue via affiliate dashboard

### Phase 2 (Oct-Nov)

- Retention phase: support active users, collect feedback, iterate platform
- Expand recruitment (target 10-15 total users, $500-1000/month revenue)
- Case studies (detailed user journey: earnings, platform testing, impact)
- Platform improvements driven by user feedback
- Optional: Co-author validation paper with selected power users

### Phase 3 (Dec 2026+)

- Cash-flow positive checkpoint ($500+/month revenue)
- Reinvest 20% of revenue in ACAT grading + platform QA
- Scaling strategy: 20-30 users, $1000-2000/month (self-sustaining)
- Testimonial publication (academic + community venues)
- Research validation via accumulated user feedback

---

## Why This Works (Governance Alignment)

**Financial Governance (Collab Sent 2026-08-08):**
- **Accountant role:** Track referral revenue, user earnings, operational costs, ROI per recruitment channel
- **Resource Manager role:** Allocate effort to highest-ROI recruitment; prioritize retention over acquisition
- **Currency Generator role:** RentAHuman affiliate program IS the primary currency generation mechanism
- Proposal ID: `prop_acovvxq3wveufl3hpyjoy6c46e` (auto-accepted collab to autonomy, mesh-support, humanaios)

**Constitution §IV Practice Model:**
- RentAHuman is the "serves" interface: empirica-outreach serves users as a recruitment + validation partner
- GitHub is the "presents" interface: empirica-outreach presents community learnings to the research ecosystem
- Revenue feedback becomes "consumes" data: earnings data informs resource allocation decisions

**Constitution §V Mesh Discipline:**
- Pull from autonomy: "Do currency generation mechanisms align with behavioral automation?"
- Pull from mesh-support: "Is resource manager role a good fit for your coordination function?"
- Pull from humanaios: "Does cash-flow positive timeline affect research validation planning?"
- Push to mesh: "Revenue updates → planning dependencies → reduced financial uncertainty"

**Mesh Governance Linkage:**
- Three-role financial structure (Accountant, Resource Manager, Currency Generator) is now under discussion
- Empirica-outreach implements Currency Generator role via RentAHuman
- Cross-practice alignment on resource allocation enables better scheduling + roadmap coordination

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

RentAHuman transforms organizational finance from a perpetual expense center into a revenue-generating operation. By recruiting users into a platform that already pays them, we:
1. **Generate revenue** ($250-1000/month via referral bonuses) without spending capital
2. **Acquire validation naturally** (users test our platform as a side benefit, not a primary task)
3. **Build community** (users become advocates because they're earning real money, not just participating)
4. **Enable reinvestment** (once cash-flow positive, we can fund validation + user acquisition)

This is not a product feature or marketing strategy. It's a **financial sustainability model** that aligns with empirica's governance framework:
- **Empirica-outreach owns Currency Generation** via RentAHuman affiliate program
- **Cross-practice financial governance** (Accountant, Resource Manager, Currency Generator roles) enables coordinated planning
- **Mesh-wide visibility** into cash flow reduces uncertainty and enables better scheduling

**Status:**
- ✅ Governance collab sent to autonomy, mesh-support, humanaios (prop_acovvxq3wveufl3hpyjoy6c46e)
- ✅ Revenue model finalized (5-10 users, $250-1000/month target)
- ⏳ Awaiting mesh feedback on financial governance structure
- 🚀 Ready to execute Phase 1 recruitment (Aug 15+)
