"""
Nonprofit Dashboard API v1.0
Phase 2B: Dashboard & Capacity Integration

FastAPI backend for:
- Nonprofit profile CRUD (create, read, update)
- Grant search with capacity verdicts (GREEN_LIGHT/RED_LIGHT)
- Integration with Phase 1B grant matching + Phase 1A capacity checks

Author: Claude Haiku 4.5 (Z1/Z3)
Session: S-091926-Z1-grant-treasury-pilot
Date: 2026-09-19
"""

import logging
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr

from tools.nonprofit_profile_v1_0 import NonprofitProfileStore, NonprofitProfileValidator
from tools.grant_matching_engine_v1_0 import search_grants, GrantMatcher
from tools.grant_data_loader_v1_0 import MultiSourceGrantSearch

logger = logging.getLogger(__name__)

app = FastAPI(title="Nonprofit Dashboard API", version="1.0.0")

# Shared stores
nonprofit_store = NonprofitProfileStore()
grant_search = MultiSourceGrantSearch()
matcher = GrantMatcher()


# Pydantic models for request/response validation

class NonprofitProfileRequest(BaseModel):
    """Request to create or update nonprofit profile."""
    nonprofit_id: Optional[str] = None  # Optional for create (can be auto-generated)
    name: str
    ein: str
    contact_email: EmailStr
    website_url: Optional[str] = None
    contact_phone: Optional[str] = None
    annual_revenue_usd: float
    unrestricted_capital_usd: Optional[float] = None
    mission_keywords: List[str]
    service_geography: List[str]
    nonprofit_legal_status: str = "501c3"
    fiscal_sponsor: Optional[str] = None
    years_operating: Optional[int] = 1
    irs_form_990_url: Optional[str] = None
    board_size: Optional[int] = 0
    executive_director_name: Optional[str] = None
    funding_sources: List[str]
    primary_funder: Optional[str] = None
    restrictions: Optional[List[str]] = None


class NonprofitProfileResponse(BaseModel):
    """Response with nonprofit profile."""
    nonprofit_id: str
    name: str
    ein: str
    contact_email: str
    website_url: Optional[str]
    contact_phone: Optional[str]
    annual_revenue_usd: float
    unrestricted_capital_usd: Optional[float]
    mission_keywords: List[str]
    service_geography: List[str]
    nonprofit_legal_status: str
    fiscal_sponsor: Optional[str]
    years_operating: int
    irs_form_990_url: Optional[str]
    board_size: int
    executive_director_name: Optional[str]
    funding_sources: List[str]
    primary_funder: Optional[str]
    account_status: str
    profile_completion_pct: float
    profile_completed_at: Optional[str]


class GrantSearchRequest(BaseModel):
    """Request to search grants with capacity."""
    focus_areas: Optional[List[str]] = None
    service_geography: Optional[List[str]] = None
    min_amount_usd: Optional[float] = None
    days_to_deadline_min: Optional[int] = None
    top_n: Optional[int] = 15


class GrantMatch(BaseModel):
    """Grant match with capacity verdict."""
    rank: int
    grant_id: str
    funder: str
    amount_usd: float
    match_required_usd: float
    deadline: str
    days_until_deadline: int
    focus_areas: List[str]
    eligible_states: List[str]
    keyword_fit: float
    geography_fit: float
    budget_fit: float
    timeline_fit: float
    combined_score: float
    capacity_verdict: Optional[str]  # GREEN_LIGHT | RED_LIGHT
    capacity_shortfall_usd: Optional[float]
    url: Optional[str]


class GrantSearchResponse(BaseModel):
    """Response with ranked grants + capacity verdicts."""
    nonprofit_id: str
    nonprofit_name: str
    search_timestamp: str
    matches: List[GrantMatch]
    total_matches_ranked: int


# API Endpoints

@app.post("/api/v1/nonprofits", response_model=NonprofitProfileResponse, status_code=201)
def create_nonprofit_profile(profile_req: NonprofitProfileRequest):
    """Create a new nonprofit profile."""
    profile_data = profile_req.dict()

    # Generate nonprofit_id if not provided
    if not profile_data.get("nonprofit_id"):
        profile_data["nonprofit_id"] = f"org_{profile_data['ein'].replace('-', '')}_001"

    success, result = nonprofit_store.create_profile(profile_data)

    if not success:
        if isinstance(result, dict):
            status_code = result.get("status_code", 400)
            error_msg = result.get("error") or str(result.get("errors", "Unknown error"))
            raise HTTPException(status_code=status_code, detail=error_msg)
        raise HTTPException(status_code=400, detail="Failed to create profile")

    return result


@app.put("/api/v1/nonprofits/{nonprofit_id}", response_model=NonprofitProfileResponse)
def update_nonprofit_profile(nonprofit_id: str, profile_req: NonprofitProfileRequest):
    """Update an existing nonprofit profile."""
    profile_data = profile_req.dict()
    profile_data["nonprofit_id"] = nonprofit_id

    success, result = nonprofit_store.update_profile(nonprofit_id, profile_data)

    if not success:
        if isinstance(result, dict):
            status_code = result.get("status_code", 400)
            error_msg = result.get("error") or str(result.get("errors", "Unknown error"))
            raise HTTPException(status_code=status_code, detail=error_msg)
        raise HTTPException(status_code=400, detail="Failed to update profile")

    return result


@app.get("/api/v1/nonprofits/{nonprofit_id}", response_model=NonprofitProfileResponse)
def get_nonprofit_profile(nonprofit_id: str):
    """Get nonprofit profile by ID."""
    success, result = nonprofit_store.get_profile(nonprofit_id)

    if not success:
        raise HTTPException(status_code=404, detail=f"Profile {nonprofit_id} not found")

    return result


@app.post("/api/v1/nonprofits/{nonprofit_id}/grants/search", response_model=GrantSearchResponse)
def search_grants_with_capacity(nonprofit_id: str, search_req: GrantSearchRequest):
    """Search grants for nonprofit and include capacity verdicts."""

    # Get nonprofit profile
    success, profile = nonprofit_store.get_profile(nonprofit_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Profile {nonprofit_id} not found")

    # Query grant sources with filters
    all_grants = grant_search.search_all(
        focus_areas=search_req.focus_areas,
        min_amount=search_req.min_amount_usd,
        max_days_to_deadline=None if search_req.days_to_deadline_min is None else (365 - (search_req.days_to_deadline_min or 0)),
        eligible_states=search_req.service_geography or profile.get("service_geography", []),
    )

    # Search and rank grants (includes capacity checks via verify_rfp)
    results = search_grants(
        profile,
        all_grants,
        top_n=search_req.top_n or 15,
        min_score=0.3
    )

    # Transform results to include capacity verdicts
    matches = []
    for i, match in enumerate(results["matches"], 1):
        grant_match = GrantMatch(
            rank=i,
            grant_id=match["grant_id"],
            funder=match["funder"],
            amount_usd=match["amount_usd"],
            match_required_usd=match["match_required_usd"],
            deadline=match["deadline"],
            days_until_deadline=match["days_until_deadline"],
            focus_areas=[],  # TODO: get from grant object
            eligible_states=[],  # TODO: get from grant object
            keyword_fit=match["keyword_fit"],
            geography_fit=match["geography_fit"],
            budget_fit=match["budget_fit"],
            timeline_fit=match["timeline_fit"],
            combined_score=match["combined_score"],
            capacity_verdict=match.get("capacity_verdict"),
            capacity_shortfall_usd=match.get("capacity_shortfall_usd"),
            url=None,  # TODO: add grant URL from grant object
        )
        matches.append(grant_match)

    return GrantSearchResponse(
        nonprofit_id=nonprofit_id,
        nonprofit_name=profile["name"],
        search_timestamp=results["search_timestamp"],
        matches=matches,
        total_matches_ranked=len(matches),
    )


@app.get("/api/v1/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Nonprofit Dashboard API",
        "version": "1.0.0",
    }


if __name__ == "__main__":
    import uvicorn

    logging.basicConfig(level=logging.INFO)

    # Start server: uvicorn nonprofit_dashboard_api_v1_0:app --reload --port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
