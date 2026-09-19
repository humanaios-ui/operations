# Phase 1B Specification — Grant Matching Engine (Broker Track)

**Status:** Z1 Draft → Pending Z2 Ratification  
**Date:** 2026-09-19  
**Pilot:** Q-GRANT-TREASURY-ORCHESTRATION-PILOT-01 (Track B: Broker Service)  
**Executor:** Claude (Z1/Z3)  
**Hypothesis:** "Grant discovery + automated capacity matching enables nonprofits to apply confidently without capital assessment friction."

---

## Goal

Build a grant matching engine that:
1. Ingests nonprofit profile (mission, geography, annual revenue, focus areas, restrictions)
2. Queries public grant databases (Grants.gov, Foundation Center, Instrumentl, local foundations)
3. Ranks opportunities by fit (keyword + geography + budget + timeline)
4. Returns ranked list with capacity assessment (can they afford the match?)

**Output flow:** Nonprofit profile → Phase 1B (matching engine) → ranked [grant_id, match_required] → Phase 2B (verify_rfp on their capital) → GREEN_LIGHT/RED_LIGHT (proceed or fundraise first)

---

## Architecture

### Components

**1. Grant Data Ingestion**
- Grants.gov API (ETL for federal/state grants)
- Foundation Center API (private foundation database)
- Instrumentl API (grant discovery SaaS partner)
- Local foundation integrations (manual JSON import for now)
- Schema: [grant_id, funder, funder_category (federal/foundation/corporate), amount_usd, match_required_usd, focus_areas, deadline, eligibility, disbursement_schedule]

**2. Nonprofit Profile Model**
```json
{
  "nonprofit_id": "org_12345",
  "name": "Example Nonprofit",
  "ein": "12-3456789",
  "annual_revenue_usd": 500000,
  "mission_keywords": ["education", "underserved_communities", "STEM"],
  "service_geography": ["CA", "OR", "WA"],
  "restrictions": ["no_religious_advocacy", "IRS_501c3_only"],
  "recent_grants": [
    {
      "funder": "NIH",
      "amount_usd": 250000,
      "awarded_year": 2025
    }
  ],
  "board_priorities": ["climate", "health_equity"],
  "created_at": "2026-09-19T10:00:00Z"
}
```

**3. Matching Algorithm**
```
For each grant in database:
  keyword_fit = cosine_similarity(nonprofit.mission_keywords, grant.focus_areas)
  geography_fit = 1.0 if nonprofit.service_geography overlaps grant.eligible_states else 0.5 if partial else 0.0
  budget_fit = 1.0 if grant.amount_usd in [0.8×nonprofit.revenue, 2.0×nonprofit.revenue] else linear penalty
  timeline_fit = 1.0 if deadline > 60 days else 0.5 if 30-60 days else 0.0 if < 30 days
  
  score = (keyword_fit × 0.4) + (geography_fit × 0.3) + (budget_fit × 0.2) + (timeline_fit × 0.1)
  
  return: {grant_id, score, keyword_fit, geography_fit, budget_fit, timeline_fit, grant.match_required}
```

**4. Capacity Assessment Integration**
- For each top-ranked grant: extract grant_id + match_required_usd
- Call Track A Phase 1 verify_rfp() with nonprofit's capital position
- Annotate each opportunity: "GREEN_LIGHT (ready to apply)" vs "RED_LIGHT (fundraise first)"

**5. API Endpoint**
```
POST /api/grants/search

Request:
{
  "nonprofit_id": "org_12345",
  "profile": {
    "name": "Example Nonprofit",
    "annual_revenue_usd": 500000,
    "mission_keywords": ["education", "STEM"],
    "service_geography": ["CA", "OR"],
    "restrictions": ["IRS_501c3_only"],
    "unrestricted_capital_usd": 75000  // optional: if provided, capacity check enabled
  },
  "filter": {
    "min_amount_usd": 50000,
    "max_deadline_days": 180
  }
}

Response:
{
  "matches": [
    {
      "rank": 1,
      "grant_id": "rfp_nsl_2026_0819",
      "funder": "National Science Foundation",
      "amount_usd": 250000,
      "match_required_usd": 50000,
      "deadline": "2026-10-30",
      "focus_areas": ["STEM_education", "diversity"],
      "fit_score": 0.85,
      "component_scores": {
        "keyword_fit": 0.92,
        "geography_fit": 0.80,
        "budget_fit": 0.75,
        "timeline_fit": 1.0
      },
      "capacity_check": {
        "status": "GREEN_LIGHT",
        "nonprofit_unrestricted_usd": 75000,
        "match_required_usd": 50000,
        "verdict": "proceed_to_apply"
      },
      "url": "https://grants.gov/search/rfp/nsl_2026_0819"
    },
    {
      "rank": 2,
      "grant_id": "rfp_wf_2026_0820",
      "funder": "Wellcome Foundation",
      "amount_usd": 500000,
      "match_required_usd": 100000,
      "deadline": "2026-11-15",
      "capacity_check": {
        "status": "RED_LIGHT",
        "nonprofit_unrestricted_usd": 75000,
        "match_required_usd": 100000,
        "shortfall_usd": 25000,
        "verdict": "fundraise_then_apply"
      }
    }
  ],
  "total_matches": 47,
  "timestamp": "2026-09-19T10:15:30Z"
}
```

---

## Test Harness (Gate 0a-broker)

### Test Scenarios

**Scenario B1a: Perfect fit**
- Nonprofit: $500k revenue, education + STEM focus, CA/OR service area
- Grant: $250k NSF STEM education grant, CA eligible
- Expected: Score 0.85+, rank in top 3
- Verify: Matching algorithm prioritizes high keyword + geography overlap

**Scenario B1b: Geographic mismatch**
- Nonprofit: TX-focused
- Grant: CA-only eligible
- Expected: Score <0.6, relegated to lower rank
- Verify: Geography constraint properly penalizes

**Scenario B1c: Budget mismatch (too small)**
- Nonprofit: $100k revenue
- Grant: $1M (>10x nonprofit revenue)
- Expected: Score reduced by budget_fit penalty
- Verify: Budget fit prevents unrealistic matches

**Scenario B1d: Budget mismatch (too large)**
- Nonprofit: $2M revenue
- Grant: $25k (too small)
- Expected: Score reduced but not eliminated (might be match only)
- Verify: Doesn't reject small grants outright

**Scenario B1e: Deadline pressure**
- Nonprofit: education focus
- Grant A: 90-day deadline (timeline_fit = 1.0)
- Grant B: 15-day deadline (timeline_fit = 0.0)
- Expected: Grant A outranks Grant B if all else equal
- Verify: Deadline urgency reflected in scoring

**Scenario B1f: Capacity integration**
- Nonprofit: $500k revenue, $100k unrestricted capital
- Grant: $250k with $80k match required
- Expected: capacity_check = GREEN_LIGHT
- Verify: verify_rfp() called with correct capital amounts

**Scenario B1g: Capacity RED_LIGHT**
- Nonprofit: $200k unrestricted
- Grant: $500k with $150k match required
- Expected: capacity_check = RED_LIGHT with shortfall amount
- Verify: Deficit clearly stated for fundraising guidance

### Data Sources

5 test nonprofits × 3 grant sources = 15 match tests:
- **Nonprofits:** Education org (CA), Environmental org (TX+CO), Health org (NY), Arts org (multi-state), Youth org (rural)
- **Sources:** Grants.gov mock dataset (5 federal grants), Foundation Center sample (5 foundation grants), Instrumentl mock (5 corporate grants)

### Success Criteria

- **Precision:** Top 10 matches include ≥8 grants rated "very good fit" by human expert (80%+ precision)
- **Recall:** No "obvious good fit" grants (expert-rated 0.90+) missing from top 15 results (90%+ recall)
- **Ranking stability:** Same nonprofit + same grant database returns same rank over 3 consecutive searches (deterministic)
- **Capacity integration:** 5/5 verify_rfp() calls return correct GREEN/RED verdict matching nonprofit's capital
- **API latency:** Search response <2 seconds for 50 grant database

---

## Deliverables

### Code

**1. grant_matching_engine_v1_0.py** (~300 lines)
- GrantMatcher class: orchestrates keyword fit, geography fit, budget fit, timeline fit
- NonprofitProfile dataclass: schema validation
- GrantDatabase interface: abstraction for Grants.gov, Foundation Center, Instrumentl
- CombinedSearch method: ranks all opportunities
- integrate_capacity_check() method: calls verify_rfp() for each top grant

**2. grant_data_loader_v1_0.py** (~200 lines)
- GrantsGovAPI: fetch + ETL for federal grants
- FoundationCenterAPI: private foundation grants
- InstrumentalAPI: SaaS partner integration
- MockGrantDatabase: for Phase 1B testing

**3. tests/test_grant_matching_engine.py** (~250 lines)
- TestScenarioB1a–B1g: 7 scenario test classes
- MockNonprofitProfile + MockGrantDatabase fixtures
- 15 parametrized tests (5 nonprofits × 3 sources)
- Ranking precision/recall validation

### Documentation

**PHASE-1B-GRANT-MATCHING-SPEC.md** (this file)

**GRANT-MATCHING-API-CONTRACT.md**
- Full OpenAPI spec for POST /api/grants/search
- Request/response schema + examples
- Integration with verify_rfp() endpoint

---

## Effort Estimate

| Task | Hours | Notes |
|------|-------|-------|
| Grant data loader (Grants.gov, Foundation Center, Instrumentl) | 3 | API auth + ETL pipeline |
| Nonprofit profile schema + validation | 1 | Dataclass + parsing |
| Matching algorithm (scoring + ranking) | 2 | Keyword fit, geography, budget, timeline |
| Capacity integration (verify_rfp call) | 1 | Wrapper + response annotation |
| Test harness (7 scenarios + 15 parametrized tests) | 2 | Mock data + fixtures |
| **Phase 1B Total** | **9 hours** | Ready for Gate 0a-broker validation |

---

## Falsifiers (Why This Could Fail)

1. ✅ Matching algorithm produces false positives (high-ranked grants with <50% expert fit score)
2. ✅ Capacity check integration fails to call verify_rfp() or misinterprets results
3. ✅ Grant database ETL misses 20%+ of fundable grants (recall <80%)
4. ✅ Ranking is non-deterministic (same search returns different results)
5. ✅ API latency >2 seconds on 50-grant database (scalability concern)

---

## Success Criteria for Gate 0a-broker

- ✅ 15/15 test match results (5 nonprofits × 3 sources) correlate ≥0.80 with human expert curation
- ✅ Zero false negatives: no "obvious fit" grants (>0.90 expert score) missing from top 15
- ✅ Capacity check integration: 5/5 verify_rfp() calls return correct GREEN/RED verdict
- ✅ Determinism: same nonprofit + database returns same ranking over 3 runs
- ✅ API latency: <2 seconds for 50-grant search

---

## Next Steps (Post-Phase 1B)

1. **Phase 2B:** Nonprofit dashboard + profile ingestion (KYC flow)
2. **Phase 2B:** Wire real Grants.gov + Foundation Center credentials (replace mocks)
3. **Phase 3B:** Create nonprofit-facing web UI (search + alerts + capacity status)
4. **Phase 3B:** Define SaaS pricing + transaction fee structure (Z2 decision)
5. **Phase 4B:** Beta test with 3 real nonprofits; measure adoption + grant award rate

---

## Integration with Track A

- **verify_rfp() dependency:** Phase 1B calls Track A Phase 1 verify_rfp() for capacity assessment
- **Data flow:** Nonprofit profile + ranked grant → extract match_required → verify_rfp(nonprofit_capital, match_required) → return GREEN/RED
- **Audit trail:** Every capacity check logged in REGISTERED.md / NF_LEDGER.jsonl (same as Track A)
- **API contract compatibility:** Phase 1B search response includes grant.match_required_usd, which verify_rfp() consumes directly

---

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_012WCbNY31capoZ99NtXQuQC
