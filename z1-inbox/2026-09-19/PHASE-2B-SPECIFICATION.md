# Phase 2B Specification — Nonprofit Dashboard & Capacity Integration
## Q-GRANT-BROKER-PHASE-2B-01

**Prepared by:** Claude (Z1 proposer)  
**Date:** 2026-09-19  
**Session:** S-091926-Z1-grant-treasury-pilot  
**Prerequisite:** Phase 1B complete (Grant Matching Engine, Gate 0a-broker passed)

---

## Executive Summary

Phase 2B bridges Phase 1B (grant matching) and Phase 2A orchestration (post-award) by:

1. **Capacity Integration:** Route Phase 1B grant matches through Phase 1A's `verify_rfp()` to get instant capacity verdicts (GREEN_LIGHT/RED_LIGHT)
2. **Nonprofit Profile Ingestion:** KYC workflow for nonprofit self-service profile creation
3. **Dashboard MVP:** Web UI for nonprofits to search grants, view capacity alerts, and track matched opportunities
4. **API Foundation:** RESTful endpoint for nonprofit profile CRUD + grant search with capacity results

**Outcome:** Nonprofits can discover fundable grants and instantly know if they have capital to match.

---

## Design

### 2B.1: Capacity Integration (Phase 1B → Phase 1A)

**Input:** Grant matches from Phase 1B `search_grants()` API

**Flow:**
```
For each grant in top_n results:
  ↓
Call verify_rfp(
  nonprofit_unrestricted_usd = nonprofit_profile["unrestricted_capital_usd"],
  grant_match_required_usd = grant.match_required_usd
)
  ↓
Response: {
  "status": "GREEN_LIGHT" | "RED_LIGHT",
  "available_usd": nonprofit_unrestricted_usd,
  "required_usd": grant.match_required_usd,
  "surplus_usd" | "shortfall_usd": value
}
  ↓
Annotate match result:
  capacity_verdict = response.status
  capacity_shortfall_usd = response.get("shortfall_usd", null)
  ↓
Return: [grant_id, funder, amount, match_required, combined_score, 
          capacity_verdict, capacity_shortfall_usd]
```

**Integration Point:** Modify `grant_matching_engine.py` → `search_grants()` to call `GrantMatchVerifierClient.verify_capacity()` for each top-N grant before returning results.

**Test Cases (Gate 0b-integration):**
- GREEN_LIGHT: nonprofit with $100k unrestricted, grant requiring $50k match → marked GREEN
- RED_LIGHT: nonprofit with $50k unrestricted, grant requiring $100k match → marked RED with $50k shortfall
- Mixed: 10 grants, 5 GREEN + 5 RED based on capacity → correctly annotated

**Latency SLA:** capacity checks add <100ms per grant (goal: total query time remains <2s for 15 results)

---

### 2B.2: Nonprofit Profile Ingestion

**Schema:** Extend `NonprofitProfile` with additional fields for KYC + dashboard display

```python
@dataclass
class NonprofitProfile:
    # From Phase 1B
    nonprofit_id: str
    name: str
    ein: str
    annual_revenue_usd: float
    mission_keywords: list[str]
    service_geography: list[str]
    restrictions: list[str]
    recent_grants: Optional[list[dict]]
    unrestricted_capital_usd: Optional[float]
    
    # NEW for Phase 2B (KYC + dashboard)
    website_url: Optional[str]
    contact_email: str
    contact_phone: Optional[str]
    nonprofit_legal_status: str  # "501c3" | "501c4" | "foreign" | "other"
    fiscal_sponsor: Optional[str]  # If operating under fiscal sponsor
    years_operating: int  # 1-50+
    irs_form_990_url: Optional[str]  # Link to most recent 990-N/EZ/990
    board_size: int
    executive_director_name: Optional[str]
    funding_sources: list[str]  # ["government_grants", "foundations", "individual_donors", "corporate_sponsors"]
    primary_funder: Optional[str]  # "government" | "foundation" | "corporate" | "individual" | "earned_income"
    account_status: str  # "active" | "suspended" | "verified" | "incomplete"
    profile_completed_at: Optional[str]  # ISO 8601 timestamp
    profile_completion_pct: float  # 0.0-1.0 (for partially completed profiles)
```

**Ingestion API:**

```
POST /api/nonprofits/profile
Content-Type: application/json

{
  "nonprofit_id": "org_12345",
  "name": "Example Education Initiative",
  "ein": "12-3456789",
  "contact_email": "grants@example-org.org",
  "website_url": "https://example-org.org",
  "nonprofit_legal_status": "501c3",
  "years_operating": 8,
  "annual_revenue_usd": 500000,
  "mission_keywords": ["education", "STEM", "underserved"],
  "service_geography": ["CA", "OR"],
  "unrestricted_capital_usd": 75000,
  "funding_sources": ["government_grants", "foundations", "individual_donors"],
  "primary_funder": "foundation"
}

Response: {
  "nonprofit_id": "org_12345",
  "account_status": "verified",
  "profile_completion_pct": 1.0,
  "profile_completed_at": "2026-09-19T10:30:00Z",
  "message": "Profile created successfully"
}
```

**Validation Rules (Gate 0b-validation):**
- EIN format valid (XX-XXXXXXX)
- 501c3 status verified against IRS database (mock in Phase 2B)
- Annual revenue > 0
- At least 2 mission keywords
- At least 1 service geography
- Email format valid
- Unrestricted capital = numeric, >= 0

**Test Cases (Gate 0b-validation):**
- Valid 501c3 profile → account_status = "verified"
- Missing EIN → validation error
- Invalid email → validation error
- Valid profile without IRS verification (future gateway) → account_status = "incomplete" but profile created

---

### 2B.3: Nonprofit Dashboard (MVP)

**Tech Stack:** React SPA (frontend) + Python/FastAPI (backend) consuming `grant_matching_engine.py`

**Core Screens:**

#### Screen 1: Grant Search
```
Header:
  - Nonprofit name (logged-in user)
  - "Edit Profile" link
  - "My Grants" link
  
Search Form:
  - Focus area filter (dropdown: "education", "health", "environment", "youth", "arts", "all")
  - Geography filter (multiselect: CA, OR, TX, NY, etc.)
  - Min grant amount (input: $50k, $100k, $250k, custom)
  - Days to deadline (dropdown: 30+ days, 15-30 days, <15 days)
  - [Search] button
  
Results Table:
  | Rank | Funder | Amount | Deadline | Match Req. | Fit Score | Capacity | Action |
  |------|--------|--------|----------|-----------|-----------|----------|--------|
  | 1    | NSF    | $250k  | Oct 30   | $50k      | 0.82      | 🟢 GREEN | View / Apply |
  | 2    | Knight | $100k  | Nov 15   | $25k      | 0.76      | 🟢 GREEN | View / Apply |
  | 3    | DOE    | $500k  | Sep 25   | $100k     | 0.71      | 🔴 RED   | View Details |
  
  Legend:
  🟢 GREEN = Your nonprofit has unrestricted capital to match
  🔴 RED = Shortfall: nonprofit needs $XX more to match
```

#### Screen 2: Grant Detail
```
Funder: National Science Foundation
Grant: STEM Education Initiative 2026
Amount: $250,000
Deadline: 2026-10-30 (41 days remaining)
Match Required: $50,000

Your Fit Score: 0.82
  ├─ Keyword Fit: 0.60 (education, STEM overlap)
  ├─ Geography Fit: 1.0 (CA grant, you serve CA/OR)
  ├─ Budget Fit: 1.0 ($250k vs $500k revenue)
  └─ Timeline Fit: 0.70 (41 days, moderate urgency)

Your Capacity: 🟢 GREEN_LIGHT
  Available unrestricted: $100,000
  Match required: $50,000
  Surplus: $50,000 ✓

[View Full RFP] [Save to My Grants] [Get Help with Application]
```

#### Screen 3: My Grants (saved + awarded)
```
Saved Opportunities (3):
  - NSF STEM Initiative 2026 (fit: 0.82, capacity: 🟢)
  - Knight Foundation Arts Grant (fit: 0.71, capacity: 🟢)
  - Community Foundation Youth Program (fit: 0.68, capacity: 🔴)

Awarded Grants (0):
  [None yet]
  
Recently Applied (2):
  - Department of Education Literacy Grant (applied Sep 15, status: under review)
  - Health Foundation Community Health Initiative (applied Aug 30, status: rejected)
```

#### Screen 4: Edit Profile
```
Section 1: Basic Info (read-only after verification)
  Organization Name: Example Education Initiative
  EIN: 12-3456789
  Legal Status: 501(c)(3)
  
Section 2: Contact
  Contact Email: [text input, validates format]
  Contact Phone: [optional]
  Website: [optional URL]
  Executive Director: [optional]
  
Section 3: Programs
  Mission Keywords: [education, STEM, underserved] [+ add keyword]
  Service Geography: [CA, OR] [+ add state]
  
Section 4: Financial
  Annual Revenue (USD): [$500,000]
  Unrestricted Capital (USD): [$75,000]
  Primary Funder: [dropdown: foundation selected]
  Funding Sources: [checkboxes: ✓ government, ✓ foundations, ☐ individual, ☐ corporate]
  
Section 5: Audit
  Profile Completion: 100%
  Last Updated: 2026-09-19 10:30 AM
  Account Status: Verified ✓
  
[Save Changes] [Cancel]
```

**Responsive Design:** Mobile-first, responsive grid layout. Sidebar navigation collapses on mobile.

---

### 2B.4: API Contract (Dashboard Backend)

#### Endpoint 1: Create/Update Nonprofit Profile
```
POST /api/v1/nonprofits
or
PUT /api/v1/nonprofits/{nonprofit_id}

Request:
{
  "name": "Example Education Initiative",
  "ein": "12-3456789",
  "contact_email": "grants@example-org.org",
  "website_url": "https://example-org.org",
  "nonprofit_legal_status": "501c3",
  "years_operating": 8,
  "annual_revenue_usd": 500000,
  "unrestricted_capital_usd": 75000,
  "mission_keywords": ["education", "STEM", "underserved"],
  "service_geography": ["CA", "OR"],
  "funding_sources": ["government_grants", "foundations", "individual_donors"],
  "primary_funder": "foundation"
}

Response (201 / 200):
{
  "nonprofit_id": "org_12345",
  "name": "Example Education Initiative",
  "account_status": "verified",
  "profile_completion_pct": 1.0,
  "created_at": "2026-09-19T10:15:00Z",
  "updated_at": "2026-09-19T10:30:00Z"
}
```

#### Endpoint 2: Search Grants with Capacity
```
POST /api/v1/nonprofits/{nonprofit_id}/grants/search

Request:
{
  "focus_areas": ["education", "STEM"],
  "service_geography": ["CA", "OR"],
  "min_amount_usd": 50000,
  "days_to_deadline_min": 15,
  "top_n": 15
}

Response (200):
{
  "nonprofit_id": "org_12345",
  "nonprofit_name": "Example Education Initiative",
  "search_timestamp": "2026-09-19T10:45:00Z",
  "matches": [
    {
      "rank": 1,
      "grant_id": "rfp_nsf_stem_2026_001",
      "funder": "National Science Foundation",
      "amount_usd": 250000,
      "match_required_usd": 50000,
      "deadline": "2026-10-30T23:59:59Z",
      "days_until_deadline": 41,
      "focus_areas": ["STEM_education", "diversity"],
      "eligible_states": ["CA", "OR", "WA"],
      "keyword_fit": 0.60,
      "geography_fit": 1.0,
      "budget_fit": 1.0,
      "timeline_fit": 0.70,
      "combined_score": 0.82,
      "capacity_verdict": "GREEN_LIGHT",
      "capacity_shortfall_usd": null,
      "url": "https://grants.gov/grant/GRANT123"
    },
    ...
  ],
  "total_matches_ranked": 15
}
```

#### Endpoint 3: Get Nonprofit Profile
```
GET /api/v1/nonprofits/{nonprofit_id}

Response (200):
{
  "nonprofit_id": "org_12345",
  "name": "Example Education Initiative",
  "ein": "12-3456789",
  "contact_email": "grants@example-org.org",
  "website_url": "https://example-org.org",
  "nonprofit_legal_status": "501c3",
  "years_operating": 8,
  "annual_revenue_usd": 500000,
  "unrestricted_capital_usd": 75000,
  "mission_keywords": ["education", "STEM", "underserved"],
  "service_geography": ["CA", "OR"],
  "funding_sources": ["government_grants", "foundations", "individual_donors"],
  "primary_funder": "foundation",
  "account_status": "verified",
  "profile_completion_pct": 1.0,
  "profile_completed_at": "2026-09-19T10:30:00Z",
  "created_at": "2026-09-19T10:15:00Z",
  "updated_at": "2026-09-19T10:30:00Z"
}
```

---

## Test Harness (Gate 0b)

### Test Classes

#### TestCapacityIntegration (5 tests)
1. `test_green_light_nonprofit_sufficient_capital`: nonprofit with $100k, grant requiring $50k → GREEN + null shortfall
2. `test_red_light_nonprofit_insufficient_capital`: nonprofit with $50k, grant requiring $100k → RED + $50k shortfall
3. `test_borderline_capital`: nonprofit with $100.01k, grant requiring $100k → GREEN (just sufficient)
4. `test_capacity_adds_latency_<100ms`: verify_rfp() adds <100ms per grant
5. `test_mixed_results_10_grants`: 5 GREEN + 5 RED → correct annotation

#### TestNonprofitProfileIngestion (8 tests)
1. `test_create_valid_profile`: valid 501c3 nonprofit → account_status "verified"
2. `test_create_profile_missing_ein`: no EIN → validation error 400
3. `test_create_profile_invalid_email`: bad email format → validation error 400
4. `test_create_profile_zero_revenue`: annual_revenue_usd == 0 → validation error
5. `test_update_profile`: modify mission_keywords → persisted correctly
6. `test_get_profile`: retrieve stored nonprofit by nonprofit_id → matches input
7. `test_profile_completion_pct`: all required fields → 1.0; missing optional fields → 0.8-0.9
8. `test_irs_nonprofit_validation`: EIN verified against mock IRS database

#### TestGrantSearchWithCapacity (6 tests)
1. `test_search_includes_capacity_verdicts`: all results annotated with capacity_verdict + shortfall
2. `test_capacity_filters_ui_display`: GREEN results appear first, RED results appear lower
3. `test_nonprofit_profile_reused_across_searches`: same nonprofit, different searches → consistent capacity calculation
4. `test_search_respects_focus_area_filter`: search("education") → no climate grants returned
5. `test_search_respects_geography_filter`: search("CA", "OR") → no TX-only grants returned
6. `test_search_respects_deadline_filter`: search(days_to_deadline_min=15) → no grants with <15 days returned

#### TestDashboardDataFlow (4 tests)
1. `test_dashboard_profile_screen_loads`: GET /nonprofits/{id} returns complete profile
2. `test_dashboard_search_screen_returns_results`: POST /nonprofits/{id}/grants/search returns ranked grants with capacity
3. `test_dashboard_grant_detail_screen_fetches_full_metadata`: grant detail screen has all required fields
4. `test_dashboard_save_grant_to_my_grants`: POST /nonprofits/{id}/saved_grants/{grant_id} persists selection

#### TestIntegrationE2E (2 tests)
1. `test_end_to_end_nonprofit_onboarding`: create profile → search grants → view results → capacity verdicts calculated
2. `test_end_to_end_capacity_change`: nonprofit updates unrestricted_capital_usd → new search reflects updated capacity

**Total: 25 tests**

**Gate 0b Criteria:**
- ✅ 25/25 tests passing
- ✅ Capacity integration latency <100ms per grant (search still <2s total for 15 results)
- ✅ Profile validation catches all required fields
- ✅ Dashboard MVP renders without errors
- ✅ API contract matches spec

---

## Deliverables

### Code
- `tools/nonprofit_profile_v1_0.py` (~150 lines): Nonprofit profile model + validation
- `tools/nonprofit_dashboard_api_v1_0.py` (~300 lines): FastAPI backend (create/update profile, search grants with capacity)
- `frontend/grant-search-dashboard/` (~400 lines): React dashboard components (search, detail, profile edit, saved grants)
- `tools/tests/test_nonprofit_dashboard.py` (~25 tests)

### Documentation
- `z1-inbox/2026-09-19/PHASE-2B-IMPLEMENTATION-STATUS.md`: Gate 0b results + test summary

---

## Falsifiers

Phase 2B falsifies if ANY of these occur:

1. **Capacity verdict mismatch:** verify_rfp() called with nonprofit's unrestricted capital returns RED_LIGHT, but nonprofit later successfully funds the grant match (indicates false negative in capacity check)
2. **Dashboard search returns grants nonprofit cannot afford:** All results marked GREEN but nonprofit actually has insufficient capital (indicates capacity check not properly integrated)
3. **Profile validation allows invalid data:** EIN fails IRS validation but nonprofit still created with account_status "verified" (indicates validation gate failed)
4. **Capacity latency exceeds budget:** Adding verify_rfp() calls increases search latency beyond 2 seconds for 15-grant queries (indicates capacity check too slow)
5. **UI mismatch with API:** Dashboard displays GREEN but API returns RED (indicates frontend/backend desynchronization)

---

## Blockers & Dependencies

**No blockers for Gate 0b:**
- Phase 1B complete ✅
- Phase 1A (verify_rfp) complete ✅
- Mock grant data available ✅
- Mock nonprofit profiles ready ✅

**Pending Z2 decision (for Phase 2B deployment, not blocking 0b):**
- SaaS pricing model (affects dashboard B2B feature set)
- IRS 501c3 database access (affects real-world profile validation)

---

## Effort Estimate

| Component | Hours | Notes |
|-----------|-------|-------|
| Nonprofit profile model + validation | 2 | Schema design + input validation rules |
| FastAPI backend (3 endpoints) | 3 | Profile CRUD + grant search + integration |
| React dashboard (4 screens) | 4 | Search, detail, profile edit, saved grants |
| Capacity integration | 1 | Wire verify_rfp() calls + annotation |
| Test harness (25 tests) | 3 | Profile validation, search, E2E flows |
| **Total Phase 2B** | **13** | 2-day sprint with Phase 1B learnings |

---

## Z2 Ratification Checklist

**Ready for Z2 ratification when:**

- [ ] Phase 1B complete? YES ✅
- [ ] Capacity integration approach approved (reuse Phase 1A verify_rfp)?
- [ ] KYC workflow scope approved (self-service profile creation)?
- [ ] Dashboard MVP scope approved (search, detail, profile, saved grants)?
- [ ] Effort estimate & 2-day timeline acceptable?
- [ ] Test gate approach approved (25 tests, Gate 0b criteria)?
- [ ] Falsifiers confirmed (5 conditions that invalidate 2B)?
- [ ] No blockers preventing immediate start?

**Authority:** Z2 (Night) signs when prerequisites met.

---

## Session Ritual §A Checkpoint

**Position:** REGISTERED.md pinned at ae47eb6 (Phase 1B complete).  
**Destination:** Implement Q-GRANT-BROKER-PHASE-2B-01 (Phase 2B specification + ratification).  
**Probability:** 95% Phase 2B Gate 0b complete by 2026-09-21 if Z2 ratification obtained by 2026-09-19 18:00 UTC.

---

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>  
Claude-Session: https://claude.ai/code/session_012WCbNY31capoZ99NtXQuQC
