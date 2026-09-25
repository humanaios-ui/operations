from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class EvidenceRef:
    url: str
    kind: str
    observed_at: str
    claim: str = ""


@dataclass
class NeedMatch:
    need_id: str
    label: str
    score: float
    signals: list[str] = field(default_factory=list)


@dataclass
class ResourceCandidate:
    resource_id: str
    title: str
    source_name: str
    source_url: str
    canonical_url: str
    discovery_method: str
    discovered_at: str
    description: str = ""
    sponsor: str = ""
    published_at: str | None = None
    opens_at: str | None = None
    deadline: str | None = None
    resource_types: list[str] = field(default_factory=list)
    applicant_types: list[str] = field(default_factory=list)
    geography: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    value_text: str = ""
    cash_mentions_usd: list[float] = field(default_factory=list)
    primary_source_url: str | None = None
    evidence: list[EvidenceRef] = field(default_factory=list)
    need_matches: list[NeedMatch] = field(default_factory=list)
    route: str = "VERIFY_NOW"
    status: str = "UNKNOWN"
    eligibility_assessed: bool = False
    eligibility_status: str = "UNASSESSED"
    last_verified_at: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self, include_raw: bool = False) -> dict[str, Any]:
        data = asdict(self)
        if not include_raw:
            data.pop("raw", None)
        return data
