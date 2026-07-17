# HumanAIOS Operations Architecture — Integrated Funding + Research + Proposals

## Vision

Transform HumanAIOS from a collection of separate tools (funding pipeline, publications manager, proposal templates) into a **coherent practice infrastructure** where:

1. **Research Profile** (ORCID) is the source of truth about what you've published and your expertise
2. **Funding Discovery** (Pipeline) is continuously updated and automatically ranked by fit
3. **Proposals** (Drafts, Submissions) are tracked end-to-end with decision support
4. **Feedback loops** connect all three: new publications → re-rank opportunities; funded grants → update roadmap

---

## Current State → Target State

### Today: Disconnected Systems

```
┌─────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│ Funding Pipeline│      │ ORCID Publications│      │   Proposal Drafts│
│  (45 opps)      │      │    Manager       │      │   (Ad-hoc)       │
└────────┬────────┘      └────────┬─────────┘      └────────┬─────────┘
         │                        │                         │
         ▼                        ▼                         ▼
  OPPORTUNITIES.md        works_simple.json      LONGVIEW_GRANTS_*.md
  (weekly refresh)        (manual refresh)       (no tracking)

No integration. No cross-queries. No feedback.
```

### Target: Orchestrated Practice Layer

```
╔═══════════════════════════════════════════════════════════════════════╗
║               HumanAIOS OPERATIONS HUB (Practice Layer)                ║
├───────────────────┬────────────────────┬──────────────────────────────┤
│  RESEARCH PROFILE │  FUNDING DISCOVERY  │  APPLICATION PIPELINE        │
│ ┌────────────────┐│┌──────────────────┐│┌──────────────────────────────┐
│ │ ORCID Fetch    ││ Auto-Refresh      ││ Drafts Registry             │
│ │ (auto)         ││ (weekly)          ││ (in progress)               │
│ ├────────────────┤│├──────────────────┤│├──────────────────────────────┤
│ │ Research Areas ││ Eligibility Filter││ Submitted Tracker           │
│ │ (NLP extract)  ││ (native, safety)  ││ (status, deadline, contact)  │
│ ├────────────────┤│├──────────────────┤│├──────────────────────────────┤
│ │ Expertise Score││ Fit Scoring       ││ Decision Support            │
│ │ (by domain)    ││ (expertise match) ││ (suggest timelines, risks)  │
│ └────────────────┘│└──────────────────┘│└──────────────────────────────┘
│         │          │         │          │          │
└─────────┼──────────┼─────────┼──────────┼──────────┘
          │          │         │          │
          └──────────┴─────────┴──────────┘
             Feedback Loop:
             ✓ New pub → re-rank opps
             ✓ Funded → update roadmap
             ✓ Rejected → learn + improve

    ▼
  Dashboards & Reports:
  · "Top 5 funding opportunities for you this month"
  · "Your publications by research area"
  · "Application pipeline status"
  · "Next steps: ORCID→ACAT→Longview timeline"
```

---

## System Components

### 1. Research Profile Service

**Source:** ORCID (0009-0003-7540-4245)  
**Triggers:** Auto-fetch weekly (GitHub Actions) OR manual `update-profile` CLI command  
**Outputs:** 
- `data/research_profile.json` — structured profile
- `data/expertise_map.json` — research areas + confidence scores

**Implementation:**

```python
# src/humanaios_operations/profile.py

class ResearchProfile:
    def __init__(self, orcid_id):
        self.orcid_id = orcid_id
        self.publications = []
        self.research_areas = {}
        self.expertise_scores = {}
    
    def fetch_from_orcid(self):
        """Fetch latest publications from ORCID API"""
        # Use existing orcid-publications-manager
        # + add NLP extraction of topics
    
    def extract_research_areas(self):
        """Parse publication titles/abstracts for research areas"""
        areas = {
            "ai_calibration": 0.95,
            "digital_minds": 0.88,
            "self_assessment": 0.85,
            "ai_safety": 0.80,
            ...
        }
        return areas
    
    def get_expertise_score(self, domain):
        """Score how strong you are in a domain (0.0-1.0)"""
        # Based on publications + citation count
        return self.expertise_scores.get(domain, 0.0)
    
    def to_json(self):
        return {
            "profile": {...},
            "publications": self.publications,
            "research_areas": self.research_areas,
            "expertise_scores": self.expertise_scores
        }
```

**GitHub Actions:** `weekly-profile-sync.yml`
- Runs: Every Monday 09:00 UTC
- Does: fetch_orcid → extract_areas → save to data/ → commit

### 2. Funding Discovery Service (Enhanced)

**Current:** `humanaios-funding-pipeline/`  
**Enhancement:** Add **fit-scoring** layer

```python
# src/humanaios_operations/scoring.py

class FundingFitScorer:
    def __init__(self, research_profile, opportunity):
        self.profile = research_profile
        self.opp = opportunity
    
    def score_expertise_fit(self):
        """How well does this opportunity match your expertise?"""
        # Look at opportunity tags + description
        # Compare to your research_areas
        # Return 0.0-1.0 score
        
        opp_keywords = self.opp.get("keywords", [])
        your_areas = self.profile.research_areas.keys()
        
        overlap = len(set(opp_keywords) & set(your_areas))
        return overlap / len(opp_keywords) if opp_keywords else 0.0
    
    def score_eligibility_fit(self):
        """Can you even apply to this?"""
        # Check native eligibility (Cherokee Nation)
        # Check legal entity requirements
        # Return 0.0 or 1.0
        
        if not self.profile.is_native_eligible:
            return 0.0 if self.opp.requires_native else 1.0
        return 1.0
    
    def score_timeline_fit(self):
        """Is the deadline realistic?"""
        # Estimate proposal effort (hours)
        # Compare to deadline
        days_to_deadline = (self.opp.deadline - now()).days
        effort_hours = self.opp.estimated_effort
        
        hours_available = days_to_deadline * 3  # assume 3 hrs/day available
        return min(1.0, hours_available / effort_hours)
    
    def overall_score(self):
        """0.0-1.0 composite score"""
        return 0.5 * self.score_expertise_fit() \
             + 0.3 * self.score_eligibility_fit() \
             + 0.2 * self.score_timeline_fit()
```

**Updated Report Output:**

```markdown
# Funding Opportunities Ranked by Your Fit

| Opportunity | Score | Fit Reason | Deadline |
|---|---|---|---|
| Longview Grants RFP | 0.92 | ✓ AI calibration (95% match), digital minds (88%), org-scale fit | 2026-07-24 |
| Blue Dot Rapid Grants | 0.88 | ✓ AI-safety (80%), quick decision (5 days), solo founder | rolling |
| Coefficient Giving | 0.85 | ✓ Largest funder for your areas, high bar | rolling |
| MIT Solve Indigenous | 0.82 | ✓ Native + AI, but community-serving req (medium) | 2026-09-01 |
| MATS Fellowship | 0.65 | ~ AI-safety fit, but 1-level fellowship (you're past this) | TBD 2026-Q4 |
```

### 3. Application Pipeline Service

**New:** Tracks proposals end-to-end

```python
# src/humanaios_operations/applications.py

class ApplicationTracker:
    """Tracks grant applications from draft → decision"""
    
    def create_application(self, opportunity_id, title, status="draft"):
        app = {
            "id": uuid4(),
            "opportunity_id": opportunity_id,
            "title": title,
            "status": "draft",  # draft→submitted→pending→funded/rejected
            "created_at": now(),
            "submitted_at": None,
            "decision_at": None,
            "decision": None,  # "funded", "rejected", "pending"
            "amount_requested": None,
            "amount_awarded": None,
            "proposal_file": None,
            "budget_file": None,
            "notes": []
        }
        return self.save(app)
    
    def submit_application(self, app_id, submitted_timestamp=None):
        app = self.get(app_id)
        app["status"] = "submitted"
        app["submitted_at"] = submitted_timestamp or now()
        return self.save(app)
    
    def record_decision(self, app_id, decision, amount=None):
        app = self.get(app_id)
        app["status"] = "decided"
        app["decision"] = decision  # "funded" or "rejected"
        app["decision_at"] = now()
        app["amount_awarded"] = amount
        return self.save(app)
    
    def to_report(self):
        """Generate "Application Pipeline Status" report"""
        return {
            "in_progress": [...],  # drafts + submitted
            "pending_decision": [...],
            "outcomes": {
                "funded": [...],
                "rejected": [...],
                "success_rate": 0.25
            }
        }
```

**Example Entry:**

```json
{
  "id": "app_20260717_001",
  "opportunity_id": "longview-grants-rfp",
  "title": "Behavioral Observability Infrastructure for AI Sentience Assessment",
  "status": "submitted",
  "created_at": "2026-07-17",
  "submitted_at": "2026-07-24",
  "decision_at": null,
  "decision": null,
  "amount_requested": 200000,
  "amount_awarded": null,
  "proposal_file": "LONGVIEW_GRANTS_PROPOSAL_DRAFT.md",
  "budget_file": "LONGVIEW_BUDGET_FINAL.xlsx",
  "notes": [
    "Submitted as LLC (not individual)",
    "Budget negotiated: mainline $200k/yr vs $250k original ask",
    "Emphasize ACAT as existing asset, not speculative work"
  ]
}
```

### 4. Feedback Loop & Decision Support

**Decision Support Rules:**

```python
# src/humanaios_operations/recommendations.py

def suggest_opportunities():
    """Smart suggestions based on research profile + current status"""
    
    # Rule 1: New publication → suggest new opportunities
    if recent_publication_added():
        rescore_all_opportunities()
        suggest_top_3_new_high_fits()
    
    # Rule 2: Rejection → improve & retry
    if recent_rejection():
        suggest_feedback_refinement()
        suggest_similar_opportunities_with_lower_bar()
    
    # Rule 3: Funded → update roadmap
    if recent_funding():
        sync_to_research_roadmap()
        suggest_complementary_funding()
    
    # Rule 4: Deadline proximity → nudge
    if opportunity_deadline_in(7, "days"):
        suggest_draft_skeleton_for_high_fit_opps()

def timeline_advisor(opportunity):
    """Estimate realistic timeline for proposal"""
    effort_estimate = {
        "research_fellowship": 20,  # hours
        "grants": 15,
        "career_transition": 8,
        "compute_credits": 1,
    }
    
    category = opportunity.category
    hours_needed = effort_estimate.get(category, 10)
    days_to_deadline = (opportunity.deadline - now()).days
    
    if days_to_deadline < hours_needed / 3:
        return {
            "feasibility": "tight",
            "recommendation": "Draft skeleton today, fill details tomorrow"
        }
```

---

## Implementation Roadmap

### Phase 1: Core Integration (Week 1-2)

**Goals:**
- Sync ORCID → Research Profile service
- Enhance Funding Pipeline with fit-scoring
- Create Application Tracker

**Tasks:**
1. Extract existing orcid-publications-manager into ResearchProfile service
2. Add NLP (spaCy) for research area extraction from titles/abstracts
3. Implement FundingFitScorer against current 45 opportunities
4. Create applications.db schema + CLI for tracking
5. Update `haios-funding` CLI to show fit scores

**Deliverables:**
- `data/research_profile.json` (auto-generated weekly)
- Enhanced OPPORTUNITIES.md with "Your Fit Score" column
- `applications.db` tracking your proposals
- New CLI: `haios-funding --ranked-by-fit`

### Phase 2: Dashboards & Feedback Loop (Week 3)

**Goals:**
- Visual dashboard showing research ↔ funding ↔ applications
- Smart recommendations + decision support
- GitHub Actions automation for all three systems

**Tasks:**
1. Create dashboard (HTML/React) showing:
   - Your research areas (word cloud by citation count)
   - Top 5 opportunities ranked for you
   - Application pipeline status
2. Implement recommendation rules
3. Set up GitHub Actions workflows:
   - `weekly-profile-sync` (Monday)
   - `weekly-funding-refresh + rescore` (Monday)
   - `daily-deadline-nudges` (trigger on opportunity deadline ≤ 7 days)
4. Add email notifications (optional)

**Deliverables:**
- `reports/dashboard.html` (browsable)
- `reports/recommendations.md` (weekly digest)
- Fully automated GitHub Actions pipelines

### Phase 3: Advanced Features (Week 4+)

**Goals:**
- Publication-to-proposal suggestions
- Funding outcome tracking + learning
- Cross-practice visibility (if expanding to mesh)

**Tasks:**
1. When you submit a proposal, auto-tag it with research areas + funding category
2. Track funding outcomes → learn success patterns
3. Export "funding roadmap" (what you're pursuing, when decisions come)
4. Integrate with Cortex/mesh if expanding to collaborative practice model

---

## Data Schema

### research_profile.json
```json
{
  "orcid_id": "0009-0003-7540-4245",
  "profile": {
    "name": "Carly R. Anderson",
    "institution": "HumanAIOS LLC",
    "bio": "..."
  },
  "publications": [
    {
      "title": "Behavioral Observability for AI Systems...",
      "year": 2026,
      "doi": "10.5281/zenodo.21135723",
      "put_code": "12345"
    }
  ],
  "research_areas": {
    "ai_calibration": 0.95,
    "digital_minds": 0.88,
    "self_assessment": 0.85,
    "ai_safety": 0.80,
    "behavioral_observability": 0.92
  },
  "expertise_scores": {
    "ai_calibration": 0.95,
    "digital_minds": 0.88,
    ...
  },
  "last_updated": "2026-07-17T09:00:00Z"
}
```

### opportunities.json (enhanced)

```json
[
  {
    "name": "Longview Grants RFP",
    "category": "grants",
    "fit_score": 0.92,
    "fit_breakdown": {
      "expertise_match": 0.95,
      "eligibility_match": 1.0,
      "timeline_fit": 0.82
    },
    "expertise_matches": [
      "ai_calibration",
      "digital_minds",
      "ai_safety"
    ],
    ...
  }
]
```

### applications.db (SQLite)

```sql
CREATE TABLE applications (
  id TEXT PRIMARY KEY,
  opportunity_id TEXT NOT NULL,
  title TEXT NOT NULL,
  status TEXT,  -- draft|submitted|pending|decided
  created_at DATETIME,
  submitted_at DATETIME,
  decision_at DATETIME,
  decision TEXT,  -- funded|rejected
  amount_requested REAL,
  amount_awarded REAL,
  proposal_file TEXT,
  notes TEXT
);

CREATE TABLE decisions (
  id TEXT PRIMARY KEY,
  application_id TEXT,
  decision TEXT,
  amount REAL,
  feedback TEXT,
  learned_lessons TEXT,
  FOREIGN KEY (application_id) REFERENCES applications(id)
);
```

---

## Integration Points

### With Existing Empirica Outreach Work

**Longview Proposal Draft** → Gets tracked in applications.db
```bash
# After LONGVIEW_GRANTS_PROPOSAL_DRAFT.md is submitted:
haios-apps create \
  --opportunity "Longview Grants RFP" \
  --title "Behavioral Observability Infrastructure..." \
  --proposal-file LONGVIEW_GRANTS_PROPOSAL_DRAFT.md \
  --amount-requested 200000
```

**Research Profile** → Informs next grant strategy
```bash
# Quarterly: review what you've published
# Pipeline automatically suggests new opportunities based on new areas
```

### With Future Mesh/Multi-Practice Coordination

If HumanAIOS expands to multi-person team:
- Each team member maintains their own research profile
- Aggregate opportunities by team expertise
- Collaborative proposals can be tracked with multiple authors

---

## Getting Started

1. **This Week:** Validate schema with existing data (45 funding opps, ORCID profile)
2. **Next Week:** Implement Phase 1 (ResearchProfile service + fit-scoring)
3. **Week After:** Deploy Phase 2 (dashboards + automation)

**First CLI commands to make it real:**
```bash
haios-profile sync  # Fetch ORCID + extract research areas
haios-funding rank  # Re-score all opportunities by your fit
haios-apps create --opportunity "Longview Grants RFP" ...
haios-dashboard    # Open HTML dashboard
```

---

## Success Metrics

- **Research Profile:** Auto-updates weekly with new publications
- **Funding Discovery:** Top 5 opportunities ranked by your fit, visible in report
- **Applications:** 100% of grant proposals tracked from draft → decision
- **Feedback Loop:** When you publish, top 3 new opportunities suggested within 24h
- **Time Saved:** Proposal drafting cut from 4 hours to 1.5 hours (via templates + automation)

---

*This architecture transforms HumanAIOS from a collection of separate operational tools into a coherent practice layer where funding, research, and proposals flow together.*
