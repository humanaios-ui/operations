"""
Nonprofit Profile Model & Validation
Phase 2B: Dashboard & Capacity Integration

Extends Phase 1B's NonprofitProfile with KYC fields, validation, and dashboard metadata.

Author: Claude Haiku 4.5 (Z1/Z3)
Session: S-091926-Z1-grant-treasury-pilot
Date: 2026-09-19
"""

import re
import logging
from typing import TypedDict, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime

logger = logging.getLogger(__name__)


class NonprofitProfile(TypedDict):
    """Nonprofit organization profile for grant matching + dashboard."""
    # From Phase 1B (grant matching)
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
    fiscal_sponsor: Optional[str]
    years_operating: int
    irs_form_990_url: Optional[str]
    board_size: int
    executive_director_name: Optional[str]
    funding_sources: list[str]  # ["government_grants", "foundations", "individual_donors", "corporate_sponsors"]
    primary_funder: Optional[str]  # "government" | "foundation" | "corporate" | "individual" | "earned_income"
    account_status: str  # "active" | "suspended" | "verified" | "incomplete"
    profile_completed_at: Optional[str]
    profile_completion_pct: float


class NonprofitProfileValidator:
    """Validate nonprofit profile data during onboarding."""

    REQUIRED_FIELDS = [
        "nonprofit_id", "name", "ein", "contact_email",
        "annual_revenue_usd", "mission_keywords", "service_geography"
    ]

    OPTIONAL_FIELDS = [
        "website_url", "contact_phone", "fiscal_sponsor",
        "irs_form_990_url", "executive_director_name"
    ]

    VALID_LEGAL_STATUSES = ["501c3", "501c4", "foreign", "other"]
    VALID_PRIMARY_FUNDERS = ["government", "foundation", "corporate", "individual", "earned_income"]
    VALID_FUNDING_SOURCES = ["government_grants", "foundations", "individual_donors", "corporate_sponsors", "earned_income"]

    @staticmethod
    def validate_ein(ein: str) -> tuple[bool, str]:
        """Validate EIN format (XX-XXXXXXX)."""
        if not ein:
            return False, "EIN is required"

        pattern = r"^\d{2}-\d{7}$"
        if not re.match(pattern, ein):
            return False, f"EIN format invalid: expected XX-XXXXXXX, got {ein}"

        return True, ""

    @staticmethod
    def validate_email(email: str) -> tuple[bool, str]:
        """Validate email format."""
        if not email:
            return False, "Email is required"

        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, email):
            return False, f"Email format invalid: {email}"

        return True, ""

    @staticmethod
    def validate_revenue(revenue_usd: float) -> tuple[bool, str]:
        """Validate annual revenue is positive."""
        if revenue_usd is None:
            return False, "Annual revenue is required"

        if revenue_usd <= 0:
            return False, f"Annual revenue must be positive, got {revenue_usd}"

        return True, ""

    @staticmethod
    def validate_mission_keywords(keywords: list[str]) -> tuple[bool, str]:
        """Validate mission keywords: at least 2, non-empty."""
        if not keywords:
            return False, "At least 1 mission keyword required"

        if len(keywords) == 0:
            return False, "Mission keywords list is empty"

        if not all(isinstance(k, str) and len(k) > 0 for k in keywords):
            return False, "All mission keywords must be non-empty strings"

        return True, ""

    @staticmethod
    def validate_geography(states: list[str]) -> tuple[bool, str]:
        """Validate service geography: at least 1 state."""
        if not states or len(states) == 0:
            return False, "At least 1 service state required"

        if not all(isinstance(s, str) and len(s) == 2 and s.upper() == s for s in states):
            return False, "All states must be 2-letter uppercase codes (e.g., CA, OR)"

        return True, ""

    @staticmethod
    def validate_unrestricted_capital(capital_usd: Optional[float]) -> tuple[bool, str]:
        """Validate unrestricted capital (if provided)."""
        if capital_usd is None:
            return True, ""  # Optional, but if provided must be valid

        if capital_usd < 0:
            return False, f"Unrestricted capital must be >= 0, got {capital_usd}"

        return True, ""

    @staticmethod
    def validate_legal_status(status: str) -> tuple[bool, str]:
        """Validate nonprofit legal status."""
        if not status:
            return False, "Nonprofit legal status is required"

        if status not in NonprofitProfileValidator.VALID_LEGAL_STATUSES:
            return False, f"Legal status must be one of {NonprofitProfileValidator.VALID_LEGAL_STATUSES}, got {status}"

        return True, ""

    @staticmethod
    def validate_funding_sources(sources: list[str]) -> tuple[bool, str]:
        """Validate funding sources are valid."""
        if not sources or len(sources) == 0:
            return False, "At least 1 funding source required"

        invalid = [s for s in sources if s not in NonprofitProfileValidator.VALID_FUNDING_SOURCES]
        if invalid:
            return False, f"Invalid funding sources: {invalid}"

        return True, ""

    @classmethod
    def validate_profile(cls, profile_data: dict) -> tuple[bool, dict]:
        """Validate entire nonprofit profile. Returns (is_valid, errors_dict)."""
        errors = {}

        # Check required fields
        for field in cls.REQUIRED_FIELDS:
            if field not in profile_data or profile_data[field] is None:
                errors[field] = f"{field} is required"

        if errors:
            return False, errors

        # Validate each field
        ein_valid, ein_error = cls.validate_ein(profile_data.get("ein", ""))
        if not ein_valid:
            errors["ein"] = ein_error

        email_valid, email_error = cls.validate_email(profile_data.get("contact_email", ""))
        if not email_valid:
            errors["contact_email"] = email_error

        revenue_valid, revenue_error = cls.validate_revenue(profile_data.get("annual_revenue_usd"))
        if not revenue_valid:
            errors["annual_revenue_usd"] = revenue_error

        keywords_valid, keywords_error = cls.validate_mission_keywords(profile_data.get("mission_keywords", []))
        if not keywords_valid:
            errors["mission_keywords"] = keywords_error

        geo_valid, geo_error = cls.validate_geography(profile_data.get("service_geography", []))
        if not geo_valid:
            errors["service_geography"] = geo_error

        capital_valid, capital_error = cls.validate_unrestricted_capital(profile_data.get("unrestricted_capital_usd"))
        if not capital_valid:
            errors["unrestricted_capital_usd"] = capital_error

        status_valid, status_error = cls.validate_legal_status(profile_data.get("nonprofit_legal_status", ""))
        if not status_valid:
            errors["nonprofit_legal_status"] = status_error

        sources_valid, sources_error = cls.validate_funding_sources(profile_data.get("funding_sources", []))
        if not sources_valid:
            errors["funding_sources"] = sources_error

        if errors:
            return False, errors

        return True, {}


class NonprofitProfileStore:
    """In-memory store for nonprofit profiles (mock for Phase 2B)."""

    def __init__(self):
        self.profiles = {}  # nonprofit_id -> profile

    def create_profile(self, profile_data: dict) -> tuple[bool, NonprofitProfile | dict]:
        """Create nonprofit profile with validation."""
        # Validate
        is_valid, errors = NonprofitProfileValidator.validate_profile(profile_data)
        if not is_valid:
            return False, {"errors": errors, "status_code": 400}

        nonprofit_id = profile_data.get("nonprofit_id")
        if nonprofit_id in self.profiles:
            return False, {"error": f"Profile {nonprofit_id} already exists", "status_code": 409}

        # Create profile with defaults
        profile = self._build_profile(profile_data, is_new=True)
        self.profiles[nonprofit_id] = profile

        logger.info(f"Created profile for nonprofit {nonprofit_id}")
        return True, profile

    def update_profile(self, nonprofit_id: str, updates: dict) -> tuple[bool, NonprofitProfile | dict]:
        """Update existing nonprofit profile."""
        if nonprofit_id not in self.profiles:
            return False, {"error": f"Profile {nonprofit_id} not found", "status_code": 404}

        # Get existing profile and merge updates
        existing = self.profiles[nonprofit_id]
        profile_data = {**existing, **updates, "nonprofit_id": nonprofit_id}

        # Validate
        is_valid, errors = NonprofitProfileValidator.validate_profile(profile_data)
        if not is_valid:
            return False, {"errors": errors, "status_code": 400}

        # Update
        profile = self._build_profile(profile_data, is_new=False)
        self.profiles[nonprofit_id] = profile

        logger.info(f"Updated profile for nonprofit {nonprofit_id}")
        return True, profile

    def get_profile(self, nonprofit_id: str) -> tuple[bool, NonprofitProfile | dict]:
        """Retrieve nonprofit profile."""
        if nonprofit_id not in self.profiles:
            return False, {"error": f"Profile {nonprofit_id} not found", "status_code": 404}

        return True, self.profiles[nonprofit_id]

    def list_profiles(self) -> list[NonprofitProfile]:
        """List all nonprofit profiles."""
        return list(self.profiles.values())

    @staticmethod
    def _build_profile(data: dict, is_new: bool = True) -> NonprofitProfile:
        """Build complete profile with computed fields."""
        now = datetime.utcnow().isoformat() + "Z"

        # Calculate profile completion percentage
        completion_pct = NonprofitProfileStore._calculate_completion(data)

        return NonprofitProfile(
            nonprofit_id=data["nonprofit_id"],
            name=data["name"],
            ein=data["ein"],
            contact_email=data["contact_email"],
            website_url=data.get("website_url"),
            contact_phone=data.get("contact_phone"),
            annual_revenue_usd=data["annual_revenue_usd"],
            unrestricted_capital_usd=data.get("unrestricted_capital_usd"),
            mission_keywords=data.get("mission_keywords", []),
            service_geography=data.get("service_geography", []),
            restrictions=data.get("restrictions", []),
            recent_grants=data.get("recent_grants"),
            nonprofit_legal_status=data.get("nonprofit_legal_status", "501c3"),
            fiscal_sponsor=data.get("fiscal_sponsor"),
            years_operating=data.get("years_operating", 1),
            irs_form_990_url=data.get("irs_form_990_url"),
            board_size=data.get("board_size", 0),
            executive_director_name=data.get("executive_director_name"),
            funding_sources=data.get("funding_sources", []),
            primary_funder=data.get("primary_funder"),
            account_status="verified" if completion_pct >= 0.99 else "incomplete",
            profile_completed_at=now if is_new else data.get("profile_completed_at"),
            profile_completion_pct=completion_pct,
        )

    @staticmethod
    def _calculate_completion(data: dict) -> float:
        """Calculate profile completion percentage."""
        required = ["nonprofit_id", "name", "ein", "contact_email", "annual_revenue_usd",
                   "mission_keywords", "service_geography", "nonprofit_legal_status", "funding_sources"]
        optional = ["website_url", "contact_phone", "fiscal_sponsor", "irs_form_990_url",
                   "executive_director_name", "primary_funder", "unrestricted_capital_usd"]

        required_filled = sum(1 for f in required if data.get(f))
        optional_filled = sum(1 for f in optional if data.get(f))

        # Completion: 70% from required, 30% from optional
        required_score = (required_filled / len(required)) * 0.7
        optional_score = (optional_filled / len(optional)) * 0.3

        return min(1.0, required_score + optional_score)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Example: create and retrieve nonprofit profile
    store = NonprofitProfileStore()

    example_profile = {
        "nonprofit_id": "org_example_001",
        "name": "Example Education Initiative",
        "ein": "12-3456789",
        "contact_email": "grants@example-org.org",
        "annual_revenue_usd": 500000,
        "mission_keywords": ["education", "STEM"],
        "service_geography": ["CA", "OR"],
        "nonprofit_legal_status": "501c3",
        "funding_sources": ["government_grants", "foundations"],
        "unrestricted_capital_usd": 75000,
    }

    success, result = store.create_profile(example_profile)
    if success:
        print(f"✓ Profile created: {result['name']}")
        print(f"  Account status: {result['account_status']}")
        print(f"  Completion: {result['profile_completion_pct']*100:.0f}%")
    else:
        print(f"✗ Failed to create profile: {result}")
