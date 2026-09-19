"""
Grant Data Loader v1.0
Phase 1B: Grant Matching Engine for Broker Service

Ingests public grant databases (Grants.gov, Foundation Center, Instrumentl, local sources)
and provides a unified interface for grant search and metadata extraction.

Author: Claude Haiku 4.5 (Z1/Z3)
Session: S-091926-Z1-grant-treasury-pilot
Date: 2026-09-19
"""

import json
import logging
from typing import TypedDict, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


class GrantPayload(TypedDict):
    """Grant opportunity from any source."""
    grant_id: str
    funder: str
    funder_category: str  # federal, foundation, corporate, local
    amount_usd: float
    match_required_usd: float
    focus_areas: list[str]  # e.g., ["STEM_education", "diversity"]
    eligible_states: list[str]  # e.g., ["CA", "OR", "WA"]
    deadline: str  # ISO 8601
    eligibility_criteria: dict  # nonprofit type, geography, budget constraints
    disbursement_schedule: Optional[list[dict]]  # [{phase, amount_usd, due_date}]
    description: str
    url: str
    source: str  # "Grants.gov" | "Foundation Center" | "Instrumentl" | "Local"
    fetched_at: str  # ISO 8601


@dataclass
class Grant:
    """Structured grant record."""
    grant_id: str
    funder: str
    funder_category: str
    amount_usd: float
    match_required_usd: float
    focus_areas: list[str]
    eligible_states: list[str]
    deadline: str
    eligibility_criteria: dict
    disbursement_schedule: Optional[list[dict]]
    description: str
    url: str
    source: str
    fetched_at: str

    def to_dict(self):
        return asdict(self)

    @property
    def days_until_deadline(self) -> int:
        deadline_dt = datetime.fromisoformat(self.deadline.replace("Z", "+00:00"))
        now = datetime.now(deadline_dt.tzinfo)
        delta = deadline_dt - now
        return max(0, delta.days)


class GrantDatabase:
    """Abstract base for grant data sources."""

    def search(self, **filters) -> List[Grant]:
        """Search grants by filter criteria."""
        raise NotImplementedError


class GrantsGovAPI(GrantDatabase):
    """Federal grants via Grants.gov API (Phase 1B mock)."""

    def __init__(self, use_mock: bool = True):
        self.use_mock = use_mock
        self.name = "Grants.gov"

    def search(self, **filters) -> List[Grant]:
        """Query Grants.gov for federal grants."""
        if self.use_mock:
            return self._mock_search(**filters)
        raise NotImplementedError("Real Grants.gov API integration in Phase 2B")

    def _mock_search(self, **filters) -> List[Grant]:
        """Return mock federal grant opportunities."""
        mock_grants = [
            Grant(
                grant_id="rfp_nsf_stem_2026_001",
                funder="National Science Foundation",
                funder_category="federal",
                amount_usd=250000,
                match_required_usd=50000,
                focus_areas=["STEM_education", "diversity", "underserved"],
                eligible_states=["CA", "OR", "WA", "TX", "NY"],
                deadline="2026-10-30T23:59:59Z",
                eligibility_criteria={
                    "nonprofit_501c3": True,
                    "min_annual_revenue": 100000,
                    "max_annual_revenue": None,
                },
                disbursement_schedule=[
                    {"phase": 1, "amount_usd": 100000, "due_date": "2026-12-01"},
                    {"phase": 2, "amount_usd": 150000, "due_date": "2027-06-01"},
                ],
                description="STEM education grants for underserved K-12 communities",
                url="https://grants.gov/search/opportunity/nsf_stem_2026_001",
                source="Grants.gov",
                fetched_at=datetime.utcnow().isoformat() + "Z",
            ),
            Grant(
                grant_id="rfp_doe_climate_2026_002",
                funder="Department of Energy",
                funder_category="federal",
                amount_usd=500000,
                match_required_usd=100000,
                focus_areas=["climate_action", "clean_energy", "innovation"],
                eligible_states=["CA", "CO", "WA", "MA", "NY"],
                deadline="2026-11-15T23:59:59Z",
                eligibility_criteria={
                    "nonprofit_501c3": True,
                    "min_annual_revenue": 250000,
                    "focus_area_required": "climate_action",
                },
                disbursement_schedule=[
                    {"phase": 1, "amount_usd": 200000, "due_date": "2027-01-15"},
                    {"phase": 2, "amount_usd": 300000, "due_date": "2027-09-01"},
                ],
                description="Clean energy innovation and deployment initiatives",
                url="https://grants.gov/search/opportunity/doe_climate_2026_002",
                source="Grants.gov",
                fetched_at=datetime.utcnow().isoformat() + "Z",
            ),
            Grant(
                grant_id="rfp_nih_health_2026_003",
                funder="National Institutes of Health",
                funder_category="federal",
                amount_usd=300000,
                match_required_usd=75000,
                focus_areas=["health_equity", "community_health", "research"],
                eligible_states=["CA", "TX", "FL", "NY", "IL"],
                deadline="2026-12-01T23:59:59Z",
                eligibility_criteria={
                    "nonprofit_501c3": True,
                    "health_focus": True,
                },
                disbursement_schedule=[
                    {"phase": 1, "amount_usd": 100000, "due_date": "2027-02-01"},
                    {"phase": 2, "amount_usd": 200000, "due_date": "2027-08-01"},
                ],
                description="Community health equity and research initiatives",
                url="https://grants.gov/search/opportunity/nih_health_2026_003",
                source="Grants.gov",
                fetched_at=datetime.utcnow().isoformat() + "Z",
            ),
            Grant(
                grant_id="rfp_ed_literacy_2026_004",
                funder="U.S. Department of Education",
                funder_category="federal",
                amount_usd=150000,
                match_required_usd=30000,
                focus_areas=["literacy", "education", "youth"],
                eligible_states=["all"],
                deadline="2026-09-30T23:59:59Z",
                eligibility_criteria={
                    "nonprofit_501c3": True,
                    "min_annual_revenue": 50000,
                },
                disbursement_schedule=[
                    {"phase": 1, "amount_usd": 75000, "due_date": "2026-11-15"},
                    {"phase": 2, "amount_usd": 75000, "due_date": "2027-05-15"},
                ],
                description="Youth literacy and educational advancement programs",
                url="https://grants.gov/search/opportunity/ed_literacy_2026_004",
                source="Grants.gov",
                fetched_at=datetime.utcnow().isoformat() + "Z",
            ),
            Grant(
                grant_id="rfp_hhs_social_2026_005",
                funder="Department of Health and Human Services",
                funder_category="federal",
                amount_usd=200000,
                match_required_usd=50000,
                focus_areas=["social_services", "vulnerable_populations", "welfare"],
                eligible_states=["CA", "TX", "NY", "FL", "PA"],
                deadline="2026-10-15T23:59:59Z",
                eligibility_criteria={
                    "nonprofit_501c3": True,
                    "social_services_focus": True,
                },
                disbursement_schedule=[
                    {"phase": 1, "amount_usd": 100000, "due_date": "2026-12-20"},
                    {"phase": 2, "amount_usd": 100000, "due_date": "2027-06-20"},
                ],
                description="Social services and vulnerable population support programs",
                url="https://grants.gov/search/opportunity/hhs_social_2026_005",
                source="Grants.gov",
                fetched_at=datetime.utcnow().isoformat() + "Z",
            ),
        ]
        return self._filter_grants(mock_grants, filters)

    def _filter_grants(self, grants: List[Grant], filters: dict) -> List[Grant]:
        """Apply filter criteria to grant list."""
        result = grants
        if "focus_areas" in filters:
            focus_areas = filters["focus_areas"]
            result = [g for g in result if any(f in g.focus_areas for f in focus_areas)]
        if "min_amount" in filters:
            result = [g for g in result if g.amount_usd >= filters["min_amount"]]
        if "max_days_to_deadline" in filters:
            result = [g for g in result if g.days_until_deadline <= filters["max_days_to_deadline"]]
        if "eligible_states" in filters:
            states = filters["eligible_states"]
            result = [g for g in result if any(s in g.eligible_states or "all" in g.eligible_states for s in states)]
        return result


class FoundationCenterAPI(GrantDatabase):
    """Private foundation grants via Foundation Center (Phase 1B mock)."""

    def __init__(self, use_mock: bool = True):
        self.use_mock = use_mock
        self.name = "Foundation Center"

    def search(self, **filters) -> List[Grant]:
        """Query Foundation Center for foundation grants."""
        if self.use_mock:
            return self._mock_search(**filters)
        raise NotImplementedError("Real Foundation Center API integration in Phase 2B")

    def _mock_search(self, **filters) -> List[Grant]:
        """Return mock foundation grant opportunities."""
        mock_grants = [
            Grant(
                grant_id="rfp_kf_education_2026_001",
                funder="Knight Foundation",
                funder_category="foundation",
                amount_usd=100000,
                match_required_usd=25000,
                focus_areas=["education", "journalism", "arts"],
                eligible_states=["CA", "TX", "NY", "FL", "IL"],
                deadline="2026-11-30T23:59:59Z",
                eligibility_criteria={
                    "nonprofit_501c3": True,
                    "local_focus": True,
                },
                disbursement_schedule=[
                    {"phase": 1, "amount_usd": 50000, "due_date": "2027-01-15"},
                    {"phase": 2, "amount_usd": 50000, "due_date": "2027-07-15"},
                ],
                description="Knight Foundation grants for local impact initiatives",
                url="https://foundationcenter.org/grants/knight-2026-001",
                source="Foundation Center",
                fetched_at=datetime.utcnow().isoformat() + "Z",
            ),
            Grant(
                grant_id="rfp_wf_climate_2026_002",
                funder="Wellcome Foundation",
                funder_category="foundation",
                amount_usd=500000,
                match_required_usd=100000,
                focus_areas=["climate", "biodiversity", "health"],
                eligible_states=["CA", "CO", "WA", "MA", "VT"],
                deadline="2026-12-15T23:59:59Z",
                eligibility_criteria={
                    "nonprofit_501c3": True,
                    "climate_or_health_focus": True,
                },
                disbursement_schedule=[
                    {"phase": 1, "amount_usd": 250000, "due_date": "2027-02-01"},
                    {"phase": 2, "amount_usd": 250000, "due_date": "2027-08-01"},
                ],
                description="Wellcome Foundation support for climate and health initiatives",
                url="https://wellcome.org/grants/climate-health-2026-002",
                source="Foundation Center",
                fetched_at=datetime.utcnow().isoformat() + "Z",
            ),
            Grant(
                grant_id="rfp_cf_social_2026_003",
                funder="Community Foundation Network",
                funder_category="foundation",
                amount_usd=75000,
                match_required_usd=15000,
                focus_areas=["community_development", "social_justice"],
                eligible_states=["CA", "NY", "TX"],
                deadline="2026-10-20T23:59:59Z",
                eligibility_criteria={
                    "nonprofit_501c3": True,
                    "community_based": True,
                },
                disbursement_schedule=[
                    {"phase": 1, "amount_usd": 37500, "due_date": "2026-12-15"},
                    {"phase": 2, "amount_usd": 37500, "due_date": "2027-06-15"},
                ],
                description="Community Foundation grants for local social impact",
                url="https://communityfoundation.org/grants/2026-social-003",
                source="Foundation Center",
                fetched_at=datetime.utcnow().isoformat() + "Z",
            ),
            Grant(
                grant_id="rfp_sf_arts_2026_004",
                funder="Smithsonian Foundation",
                funder_category="foundation",
                amount_usd=50000,
                match_required_usd=10000,
                focus_areas=["arts", "culture", "education"],
                eligible_states=["CA", "NY", "DC", "MA"],
                deadline="2026-09-30T23:59:59Z",
                eligibility_criteria={
                    "nonprofit_501c3": True,
                    "arts_focus": True,
                },
                disbursement_schedule=[
                    {"phase": 1, "amount_usd": 25000, "due_date": "2026-11-30"},
                    {"phase": 2, "amount_usd": 25000, "due_date": "2027-05-30"},
                ],
                description="Smithsonian Foundation support for arts and culture",
                url="https://si.edu/grants/arts-culture-2026-004",
                source="Foundation Center",
                fetched_at=datetime.utcnow().isoformat() + "Z",
            ),
            Grant(
                grant_id="rfp_mf_health_2026_005",
                funder="MacArthur Foundation",
                funder_category="foundation",
                amount_usd=200000,
                match_required_usd=50000,
                focus_areas=["health_equity", "medical_research", "public_health"],
                eligible_states=["CA", "IL", "NY", "TX"],
                deadline="2026-11-01T23:59:59Z",
                eligibility_criteria={
                    "nonprofit_501c3": True,
                    "health_research_focus": True,
                },
                disbursement_schedule=[
                    {"phase": 1, "amount_usd": 100000, "due_date": "2027-01-15"},
                    {"phase": 2, "amount_usd": 100000, "due_date": "2027-07-15"},
                ],
                description="MacArthur Foundation grants for health equity and research",
                url="https://macarthur.org/grants/health-2026-005",
                source="Foundation Center",
                fetched_at=datetime.utcnow().isoformat() + "Z",
            ),
        ]
        return self._filter_grants(mock_grants, filters)

    def _filter_grants(self, grants: List[Grant], filters: dict) -> List[Grant]:
        """Apply filter criteria to grant list."""
        result = grants
        if "focus_areas" in filters:
            focus_areas = filters["focus_areas"]
            result = [g for g in result if any(f in g.focus_areas for f in focus_areas)]
        if "min_amount" in filters:
            result = [g for g in result if g.amount_usd >= filters["min_amount"]]
        if "max_days_to_deadline" in filters:
            result = [g for g in result if g.days_until_deadline <= filters["max_days_to_deadline"]]
        if "eligible_states" in filters:
            states = filters["eligible_states"]
            result = [g for g in result if any(s in g.eligible_states for s in states)]
        return result


class InstrumentalAPI(GrantDatabase):
    """Grant discovery SaaS partner (Phase 1B mock)."""

    def __init__(self, use_mock: bool = True):
        self.use_mock = use_mock
        self.name = "Instrumentl"

    def search(self, **filters) -> List[Grant]:
        """Query Instrumentl for curated grant matches."""
        if self.use_mock:
            return self._mock_search(**filters)
        raise NotImplementedError("Real Instrumentl API integration in Phase 2B")

    def _mock_search(self, **filters) -> List[Grant]:
        """Return mock Instrumentl curated grants."""
        mock_grants = [
            Grant(
                grant_id="rfp_inst_startup_2026_001",
                funder="Startup Accelerator Fund",
                funder_category="corporate",
                amount_usd=50000,
                match_required_usd=10000,
                focus_areas=["social_enterprise", "innovation", "entrepreneurship"],
                eligible_states=["CA", "NY", "TX", "MA"],
                deadline="2026-10-31T23:59:59Z",
                eligibility_criteria={
                    "nonprofit_501c3": True,
                    "startup_stage": True,
                },
                disbursement_schedule=[
                    {"phase": 1, "amount_usd": 25000, "due_date": "2026-12-15"},
                    {"phase": 2, "amount_usd": 25000, "due_date": "2027-06-15"},
                ],
                description="Startup Accelerator Fund for social impact enterprises",
                url="https://instrumentl.com/grant/startup-accelerator-2026-001",
                source="Instrumentl",
                fetched_at=datetime.utcnow().isoformat() + "Z",
            ),
            Grant(
                grant_id="rfp_inst_tech_2026_002",
                funder="Tech For Good Initiative",
                funder_category="corporate",
                amount_usd=100000,
                match_required_usd=20000,
                focus_areas=["technology", "digital_inclusion", "innovation"],
                eligible_states=["CA", "WA", "NY", "MA", "TX"],
                deadline="2026-11-30T23:59:59Z",
                eligibility_criteria={
                    "nonprofit_501c3": True,
                    "tech_focus": True,
                },
                disbursement_schedule=[
                    {"phase": 1, "amount_usd": 50000, "due_date": "2027-01-15"},
                    {"phase": 2, "amount_usd": 50000, "due_date": "2027-07-15"},
                ],
                description="Tech For Good Initiative supporting digital transformation",
                url="https://instrumentl.com/grant/tech-for-good-2026-002",
                source="Instrumentl",
                fetched_at=datetime.utcnow().isoformat() + "Z",
            ),
            Grant(
                grant_id="rfp_inst_youth_2026_003",
                funder="Youth Empowerment Coalition",
                funder_category="corporate",
                amount_usd=75000,
                match_required_usd=15000,
                focus_areas=["youth", "education", "leadership"],
                eligible_states=["CA", "TX", "NY", "CO", "IL"],
                deadline="2026-09-15T23:59:59Z",
                eligibility_criteria={
                    "nonprofit_501c3": True,
                    "youth_focus": True,
                },
                disbursement_schedule=[
                    {"phase": 1, "amount_usd": 37500, "due_date": "2026-11-15"},
                    {"phase": 2, "amount_usd": 37500, "due_date": "2027-05-15"},
                ],
                description="Youth Empowerment Coalition grants for leadership development",
                url="https://instrumentl.com/grant/youth-empowerment-2026-003",
                source="Instrumentl",
                fetched_at=datetime.utcnow().isoformat() + "Z",
            ),
            Grant(
                grant_id="rfp_inst_env_2026_004",
                funder="Environmental Stewardship Fund",
                funder_category="corporate",
                amount_usd=125000,
                match_required_usd=25000,
                focus_areas=["environment", "sustainability", "conservation"],
                eligible_states=["CA", "CO", "WA", "MT", "OR"],
                deadline="2026-10-30T23:59:59Z",
                eligibility_criteria={
                    "nonprofit_501c3": True,
                    "environmental_focus": True,
                },
                disbursement_schedule=[
                    {"phase": 1, "amount_usd": 62500, "due_date": "2026-12-30"},
                    {"phase": 2, "amount_usd": 62500, "due_date": "2027-06-30"},
                ],
                description="Environmental Stewardship Fund for conservation initiatives",
                url="https://instrumentl.com/grant/environmental-2026-004",
                source="Instrumentl",
                fetched_at=datetime.utcnow().isoformat() + "Z",
            ),
            Grant(
                grant_id="rfp_inst_mental_2026_005",
                funder="Mental Health Alliance",
                funder_category="corporate",
                amount_usd=60000,
                match_required_usd=12000,
                focus_areas=["mental_health", "wellness", "community_support"],
                eligible_states=["CA", "NY", "TX", "FL"],
                deadline="2026-11-15T23:59:59Z",
                eligibility_criteria={
                    "nonprofit_501c3": True,
                    "mental_health_focus": True,
                },
                disbursement_schedule=[
                    {"phase": 1, "amount_usd": 30000, "due_date": "2027-01-15"},
                    {"phase": 2, "amount_usd": 30000, "due_date": "2027-07-15"},
                ],
                description="Mental Health Alliance support for community wellness programs",
                url="https://instrumentl.com/grant/mental-health-2026-005",
                source="Instrumentl",
                fetched_at=datetime.utcnow().isoformat() + "Z",
            ),
        ]
        return self._filter_grants(mock_grants, filters)

    def _filter_grants(self, grants: List[Grant], filters: dict) -> List[Grant]:
        """Apply filter criteria to grant list."""
        result = grants
        if "focus_areas" in filters:
            focus_areas = filters["focus_areas"]
            result = [g for g in result if any(f in g.focus_areas for f in focus_areas)]
        if "min_amount" in filters:
            result = [g for g in result if g.amount_usd >= filters["min_amount"]]
        if "max_days_to_deadline" in filters:
            result = [g for g in result if g.days_until_deadline <= filters["max_days_to_deadline"]]
        if "eligible_states" in filters:
            states = filters["eligible_states"]
            result = [g for g in result if any(s in g.eligible_states for s in states)]
        return result


class MultiSourceGrantSearch:
    """Query multiple grant databases in parallel and combine results."""

    def __init__(self):
        self.sources = [
            GrantsGovAPI(use_mock=True),
            FoundationCenterAPI(use_mock=True),
            InstrumentalAPI(use_mock=True),
        ]

    def search_all(self, **filters) -> List[Grant]:
        """Search all sources and combine results."""
        all_grants = []
        for source in self.sources:
            try:
                grants = source.search(**filters)
                all_grants.extend(grants)
                logger.info(f"Retrieved {len(grants)} grants from {source.name}")
            except Exception as e:
                logger.error(f"Error querying {source.name}: {e}")
        return all_grants


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    search = MultiSourceGrantSearch()
    results = search.search_all(
        focus_areas=["education", "STEM_education"],
        min_amount=50000,
        max_days_to_deadline=180,
        eligible_states=["CA", "NY"],
    )

    print(f"\nFound {len(results)} matching grants:\n")
    for grant in sorted(results, key=lambda g: g.amount_usd, reverse=True)[:5]:
        print(f"  {grant.funder} ({grant.source})")
        print(f"    Amount: ${grant.amount_usd:,.0f} | Match: ${grant.match_required_usd:,.0f}")
        print(f"    Deadline: {grant.deadline} ({grant.days_until_deadline} days)")
        print()
