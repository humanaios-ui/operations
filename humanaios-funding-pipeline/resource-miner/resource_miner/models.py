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
class RequirementMatch:
    requirement_id: str
    label: str
    gap_status: str
    score: float
    signals: list[str] = field(default_factory=list)


@dataclass
class DemandQuery:
    query: str
    subject_kind: str
    intent_class: str


@dataclass
class DemandMetric:
    provider: str
    query: str
    metric: str
    unit: str
    observed_at: str
    value: float | None = None
    raw_value: str = ""
    geography: str = ""
    period: str = ""
    censored_below: float | None = None


@dataclass
class DemandSnapshot:
    subject_kind: str
    query_cluster: list[DemandQuery]
    provider_metrics: list[DemandMetric]
    observed_at: str
    notes: list[str] = field(default_factory=list)


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
    resource_affordances: list[str] = field(default_factory=list)
    applicant_types: list[str] = field(default_factory=list)
    geography: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    value_text: str = ""
    cash_mentions_usd: list[float] = field(default_factory=list)
    primary_source_url: str | None = None
    evidence: list[EvidenceRef] = field(default_factory=list)
    need_matches: list[NeedMatch] = field(default_factory=list)
    requirement_matches: list[RequirementMatch] = field(default_factory=list)
    route: str = "VERIFY_NOW"
    status: str = "UNKNOWN"
    eligibility_assessed: bool = False
    eligibility_status: str = "UNASSESSED"
    last_verified_at: str | None = None
    mine_name: str = ""
    mine_url: str | None = None
    opportunity_kind: str = ""
    demand_snapshots: list[DemandSnapshot] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self, include_raw: bool = False) -> dict[str, Any]:
        data = asdict(self)
        if not include_raw:
            data.pop("raw", None)
        return data
