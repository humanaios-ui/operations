from __future__ import annotations

import csv
import io
import statistics
from collections import defaultdict
from dataclasses import replace

from .models import DemandMetric, DemandQuery, DemandSnapshot, ResourceCandidate

SUBJECT_KINDS = {"MINE", "OPPORTUNITY", "RESOURCE_CLASS", "NEED"}
INTENT_CLASSES = {"NAME", "RESOURCE", "PROBLEM", "ELIGIBILITY", "ACTION"}


def validate_query_cluster(queries: list[DemandQuery]) -> list[DemandQuery]:
    seen: set[tuple[str, str, str]] = set()
    out: list[DemandQuery] = []
    for item in queries:
        query = " ".join(item.query.split()).strip()
        subject_kind = item.subject_kind.upper()
        intent_class = item.intent_class.upper()
        if not query:
            raise ValueError("demand query must not be empty")
        if subject_kind not in SUBJECT_KINDS:
            raise ValueError(f"unsupported subject_kind: {item.subject_kind}")
        if intent_class not in INTENT_CLASSES:
            raise ValueError(f"unsupported intent_class: {item.intent_class}")
        key = (query.casefold(), subject_kind, intent_class)
        if key in seen:
            continue
        seen.add(key)
        out.append(DemandQuery(query=query, subject_kind=subject_kind, intent_class=intent_class))
    return out


def _csv_rows(text: str) -> list[list[str]]:
    return [row for row in csv.reader(io.StringIO(text)) if any(cell.strip() for cell in row)]


def _parse_numeric(raw: str) -> tuple[float | None, float | None]:
    value = raw.strip().replace(",", "")
    if not value:
        return None, None
    if value.startswith("<"):
        try:
            return None, float(value[1:])
        except ValueError:
            return None, None
    try:
        return float(value), None
    except ValueError:
        return None, None


def parse_google_trends_csv(
    text: str,
    *,
    observed_at: str,
    geography: str = "",
) -> list[DemandMetric]:
    """Parse a Google Trends UI CSV export into evidence metrics.

    Google Trends values are relative interest indexes normalized to 0..100.
    They are never represented as user counts or absolute search volume here.
    """
    rows = _csv_rows(text)
    header_index = None
    for index, row in enumerate(rows):
        if row and row[0].strip().casefold() in {"week", "day", "date", "month", "time"}:
            header_index = index
            break
    if header_index is None:
        raise ValueError("could not locate Google Trends timeline header")

    header = rows[header_index]
    if len(header) < 2:
        raise ValueError("Google Trends export has no query columns")

    points: dict[str, list[tuple[str, float, str]]] = defaultdict(list)
    censored: dict[str, list[tuple[str, str, float]]] = defaultdict(list)
    for row in rows[header_index + 1 :]:
        if not row:
            continue
        period = row[0].strip()
        for i, query in enumerate(header[1:], start=1):
            if i >= len(row):
                continue
            raw = row[i].strip()
            value, below = _parse_numeric(raw)
            if value is not None:
                if not 0 <= value <= 100:
                    raise ValueError(f"Google Trends index outside 0..100: {value}")
                points[query.strip()].append((period, value, raw))
            elif below is not None:
                censored[query.strip()].append((period, raw, below))

    metrics: list[DemandMetric] = []
    for query in header[1:]:
        query = query.strip()
        series = points.get(query, [])
        if series:
            values = [item[1] for item in series]
            metrics.extend(
                [
                    DemandMetric(
                        "google_trends",
                        query,
                        "interest_mean",
                        "relative_index_0_100",
                        observed_at,
                        round(statistics.fmean(values), 4),
                        geography=geography,
                        period=f"{series[0][0]}..{series[-1][0]}",
                    ),
                    DemandMetric(
                        "google_trends",
                        query,
                        "interest_peak",
                        "relative_index_0_100",
                        observed_at,
                        max(values),
                        geography=geography,
                        period=f"{series[0][0]}..{series[-1][0]}",
                    ),
                    DemandMetric(
                        "google_trends",
                        query,
                        "interest_latest",
                        "relative_index_0_100",
                        observed_at,
                        series[-1][1],
                        raw_value=series[-1][2],
                        geography=geography,
                        period=series[-1][0],
                    ),
                ]
            )
        for period, raw, below in censored.get(query, []):
            metrics.append(
                DemandMetric(
                    "google_trends",
                    query,
                    "interest_point",
                    "relative_index_0_100",
                    observed_at,
                    value=None,
                    raw_value=raw,
                    geography=geography,
                    period=period,
                    censored_below=below,
                )
            )
    return metrics


def _normalized_header_map(fieldnames: list[str]) -> dict[str, str]:
    return {" ".join(name.replace("_", " ").split()).casefold(): name for name in fieldnames if name}


def parse_bing_keyword_csv(
    text: str,
    *,
    observed_at: str,
    geography: str = "",
) -> list[DemandMetric]:
    """Parse a Bing Keyword Research CSV export.

    Bing labels have changed over time, so the parser accepts current/general
    volume labels plus historical impression labels. Values remain search-event
    or impression counts; they are not deduplicated unique-user counts.
    """
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise ValueError("Bing keyword export has no header")
    headers = _normalized_header_map(reader.fieldnames)

    query_header = next((headers[x] for x in ("keyword", "query", "search term") if x in headers), None)
    if not query_header:
        raise ValueError("Bing keyword export has no keyword/query column")

    metric_aliases = {
        "search volume": "search_volume",
        "search count": "search_volume",
        "impressions": "impressions",
        "strict impressions": "strict_impressions",
        "appeared in search": "broad_impressions",
        "broad impressions": "broad_impressions",
        "broad match impressions": "broad_impressions",
    }
    metric_headers = [
        (headers[label], metric_name)
        for label, metric_name in metric_aliases.items()
        if label in headers
    ]
    if not metric_headers:
        raise ValueError("Bing keyword export has no supported volume/impression column")

    period_header = next((headers[x] for x in ("week", "date", "period", "month") if x in headers), None)
    metrics: list[DemandMetric] = []
    for row in reader:
        query = (row.get(query_header) or "").strip()
        if not query:
            continue
        period = (row.get(period_header) or "").strip() if period_header else ""
        for source_header, metric_name in metric_headers:
            raw = (row.get(source_header) or "").strip()
            value, below = _parse_numeric(raw)
            if value is None and below is None:
                continue
            metrics.append(
                DemandMetric(
                    provider="bing_keyword_research",
                    query=query,
                    metric=metric_name,
                    unit="search_events_or_impressions",
                    observed_at=observed_at,
                    value=value,
                    raw_value=raw,
                    geography=geography,
                    period=period,
                    censored_below=below,
                )
            )
    return metrics


def build_snapshot(
    *,
    subject_kind: str,
    query_cluster: list[DemandQuery],
    provider_metrics: list[DemandMetric],
    observed_at: str,
    notes: list[str] | None = None,
) -> DemandSnapshot:
    subject_kind = subject_kind.upper()
    if subject_kind not in SUBJECT_KINDS:
        raise ValueError(f"unsupported subject_kind: {subject_kind}")
    cluster = validate_query_cluster(query_cluster)
    mismatched = [item.query for item in cluster if item.subject_kind != subject_kind]
    if mismatched:
        raise ValueError(
            "snapshot subject_kind must match every query subject_kind; "
            f"mismatched queries: {mismatched}"
        )
    return DemandSnapshot(
        subject_kind=subject_kind,
        query_cluster=cluster,
        provider_metrics=provider_metrics,
        observed_at=observed_at,
        notes=list(notes or []),
    )


def attach_snapshot(resource: ResourceCandidate, snapshot: DemandSnapshot) -> ResourceCandidate:
    """Return a copy with observational demand evidence attached.

    This does not change route, status, eligibility, warrant, or authorization.
    """
    return replace(resource, demand_snapshots=[*resource.demand_snapshots, snapshot])


# ---------------------------------------------------------------------------
# Opportunity-demand normalization (DMD-*)
# ---------------------------------------------------------------------------

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Iterable

from .broker import BrokerOpportunity, BrokerRequirement, build_requirement
from .models import EvidenceRef

REQUIREMENT_MODES = {
    "REQUIRED",
    "OPTIONAL",
    "PREFERRED",
    "PROHIBITED",
    "CONDITIONAL",
    "SCORED",
}
SEMANTIC_CLASSES = {
    "CAPABILITY",
    "ELIGIBILITY",
    "CONSTRAINT",
    "PROHIBITION",
    "DELIVERABLE",
    "EVALUATION",
    "COMPLIANCE_CONTROL",
}


def _demand_canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _demand_stable_id(prefix: str, payload: Any) -> str:
    return f"{prefix}-" + _demand_canonical_sha256(payload)[:16].upper()


def _evidence_to_dict(rows: Iterable[EvidenceRef]) -> list[dict[str, Any]]:
    return [asdict(row) for row in rows]


def _evidence_from_dict(rows: Iterable[dict[str, Any]]) -> list[EvidenceRef]:
    return [EvidenceRef(**row) for row in rows]


@dataclass(frozen=True)
class DemandRequirementRecord:
    demand_requirement_id: str
    label: str
    mode: str
    semantic_class: str
    statement: str
    required_affordances: list[str]
    allowed_resource_types: list[str]
    condition: str
    score_weight: float | None
    brokerable: bool
    source_locator: str
    evidence: list[dict[str, Any]]
    authority_effect: str = "NONE"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DemandProfile:
    schema: str
    profile_id: str
    opportunity_id: str
    source_kind: str
    source_identity: str
    source_url: str
    objective: str
    deadline: str | None
    requirements: list[DemandRequirementRecord]
    constraints: list[str]
    eligibility_predicates: list[str]
    prohibitions: list[str]
    deliverables: list[str]
    evaluation_criteria: list[dict[str, Any]]
    value_signals: list[str]
    submission_surface: str
    source_metadata: dict[str, Any]
    evidence: list[dict[str, Any]]
    authority_effect: str = "NONE"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["requirements"] = [row.to_dict() for row in self.requirements]
        return payload


def make_demand_requirement(
    *,
    label: str,
    mode: str,
    semantic_class: str,
    statement: str,
    evidence: Iterable[EvidenceRef],
    required_affordances: Iterable[str] = (),
    allowed_resource_types: Iterable[str] = (),
    condition: str = "",
    score_weight: float | None = None,
    brokerable: bool | None = None,
    source_locator: str = "",
) -> DemandRequirementRecord:
    normalized_mode = mode.strip().upper()
    normalized_class = semantic_class.strip().upper()
    if normalized_mode not in REQUIREMENT_MODES:
        raise ValueError(f"unsupported demand requirement mode: {normalized_mode}")
    if normalized_class not in SEMANTIC_CLASSES:
        raise ValueError(f"unsupported demand semantic class: {normalized_class}")
    rows = _evidence_to_dict(evidence)
    if not rows:
        raise ValueError("demand requirement requires evidence")
    if score_weight is not None and score_weight < 0:
        raise ValueError("score_weight cannot be negative")
    if normalized_mode == "SCORED" and score_weight is None:
        raise ValueError("SCORED demand requirement requires score_weight")
    if normalized_mode != "SCORED" and score_weight is not None:
        raise ValueError("score_weight is only valid for SCORED requirements")

    affordances = sorted({str(x).strip() for x in required_affordances if str(x).strip()})
    resource_types = sorted({str(x).strip() for x in allowed_resource_types if str(x).strip()})
    if brokerable is None:
        brokerable = normalized_class in {
            "CAPABILITY",
            "DELIVERABLE",
            "COMPLIANCE_CONTROL",
        } and normalized_mode != "PROHIBITED"
    if brokerable and not affordances:
        raise ValueError("brokerable demand requirement requires affordances")

    payload = {
        "label": label.strip(),
        "mode": normalized_mode,
        "semantic_class": normalized_class,
        "statement": statement.strip(),
        "required_affordances": affordances,
        "allowed_resource_types": resource_types,
        "condition": condition.strip(),
        "score_weight": score_weight,
        "brokerable": bool(brokerable),
        "source_locator": source_locator.strip(),
        "evidence": rows,
    }
    return DemandRequirementRecord(
        demand_requirement_id=_demand_stable_id("DMR", payload),
        label=payload["label"],
        mode=normalized_mode,
        semantic_class=normalized_class,
        statement=payload["statement"],
        required_affordances=affordances,
        allowed_resource_types=resource_types,
        condition=payload["condition"],
        score_weight=score_weight,
        brokerable=bool(brokerable),
        source_locator=payload["source_locator"],
        evidence=rows,
    )


def build_demand_profile(
    *,
    opportunity: BrokerOpportunity,
    source_kind: str,
    source_identity: str,
    source_url: str,
    objective: str,
    requirements: Iterable[DemandRequirementRecord],
    evidence: Iterable[EvidenceRef],
    deadline: str | None = None,
    constraints: Iterable[str] = (),
    eligibility_predicates: Iterable[str] = (),
    prohibitions: Iterable[str] = (),
    deliverables: Iterable[str] = (),
    evaluation_criteria: Iterable[dict[str, Any]] = (),
    value_signals: Iterable[str] = (),
    submission_surface: str = "",
    source_metadata: dict[str, Any] | None = None,
) -> DemandProfile:
    reqs = list(requirements)
    rows = _evidence_to_dict(evidence)
    if not reqs:
        raise ValueError("demand profile requires at least one requirement")
    if not rows:
        raise ValueError("demand profile requires evidence")
    for req in reqs:
        if req.authority_effect != "NONE":
            raise ValueError("demand requirements cannot grant authority")

    serialized_requirements = [row.to_dict() for row in reqs]
    normalized_constraints = sorted(
        {str(x).strip() for x in constraints if str(x).strip()}
    )
    normalized_eligibility = sorted(
        {str(x).strip() for x in eligibility_predicates if str(x).strip()}
    )
    normalized_prohibitions = sorted(
        {str(x).strip() for x in prohibitions if str(x).strip()}
    )
    normalized_deliverables = sorted(
        {str(x).strip() for x in deliverables if str(x).strip()}
    )
    normalized_value_signals = sorted(
        {str(x).strip() for x in value_signals if str(x).strip()}
    )
    criteria = list(evaluation_criteria)
    metadata = dict(source_metadata or {})
    identity_payload = {
        "schema": "humanaios.demand-profile.v1",
        "opportunity_id": opportunity.opportunity_id,
        "source_kind": source_kind.strip().upper(),
        "source_identity": source_identity.strip(),
        "source_url": source_url.strip(),
        "objective": objective.strip(),
        "deadline": deadline,
        "requirements": serialized_requirements,
        "constraints": normalized_constraints,
        "eligibility_predicates": normalized_eligibility,
        "prohibitions": normalized_prohibitions,
        "deliverables": normalized_deliverables,
        "evaluation_criteria": criteria,
        "value_signals": normalized_value_signals,
        "submission_surface": submission_surface.strip(),
        "source_metadata": metadata,
        "evidence": rows,
    }
    return DemandProfile(
        schema="humanaios.demand-profile.v1",
        profile_id=_demand_stable_id("DMD", identity_payload),
        opportunity_id=opportunity.opportunity_id,
        source_kind=source_kind.strip().upper(),
        source_identity=source_identity.strip(),
        source_url=source_url.strip(),
        objective=objective.strip(),
        deadline=deadline,
        requirements=reqs,
        constraints=normalized_constraints,
        eligibility_predicates=normalized_eligibility,
        prohibitions=normalized_prohibitions,
        deliverables=normalized_deliverables,
        evaluation_criteria=criteria,
        value_signals=normalized_value_signals,
        submission_surface=submission_surface.strip(),
        source_metadata=metadata,
        evidence=rows,
        authority_effect="NONE",
    )


def validate_demand_profile(profile: DemandProfile) -> None:
    if profile.schema != "humanaios.demand-profile.v1":
        raise ValueError("unsupported demand profile schema")
    if profile.authority_effect != "NONE":
        raise ValueError("demand profile cannot grant authority")
    if not profile.requirements:
        raise ValueError("demand profile requires requirements")
    requirement_ids = [row.demand_requirement_id for row in profile.requirements]
    if len(requirement_ids) != len(set(requirement_ids)):
        raise ValueError("demand requirement IDs must be unique")
    for row in profile.requirements:
        if row.mode not in REQUIREMENT_MODES:
            raise ValueError("invalid requirement mode")
        if row.semantic_class not in SEMANTIC_CLASSES:
            raise ValueError("invalid semantic class")
        if row.semantic_class == "ELIGIBILITY" and row.brokerable:
            raise ValueError("eligibility predicates cannot become broker capability requirements")
        if row.mode == "PROHIBITED" and row.brokerable:
            raise ValueError("prohibited requirements cannot be brokered as capabilities")


def compile_broker_requirements(
    *,
    profile: DemandProfile,
    opportunity: BrokerOpportunity,
) -> list[BrokerRequirement]:
    validate_demand_profile(profile)
    if profile.opportunity_id != opportunity.opportunity_id:
        raise ValueError("demand profile is not bound to supplied opportunity")

    out: list[BrokerRequirement] = []
    for row in profile.requirements:
        if not row.brokerable:
            continue
        if row.semantic_class == "ELIGIBILITY":
            raise ValueError("eligibility predicate cannot compile into broker requirement")
        if row.mode == "PROHIBITED":
            raise ValueError("prohibited demand cannot compile into broker requirement")

        method_permission = "UNKNOWN"
        target_scope = "NOT_APPLICABLE"
        external_state_change = False
        if profile.source_kind in {"BUG_BOUNTY", "SECURITY_PROGRAM"}:
            method_permission = str(
                profile.source_metadata.get("method_permission_state") or "UNKNOWN"
            ).upper()
            target_scope = str(
                profile.source_metadata.get("target_scope_state") or "UNKNOWN"
            ).upper()
            external_state_change = bool(
                profile.source_metadata.get("external_state_change_allowed", False)
            )

        out.append(
            build_requirement(
                opportunity=opportunity,
                label=row.label,
                objective=row.statement,
                required_affordances=row.required_affordances,
                allowed_resource_types=row.allowed_resource_types,
                method_permission_state=method_permission,
                target_scope_state=target_scope,
                external_state_change_allowed=external_state_change,
                evidence=_evidence_from_dict(row.evidence),
            )
        )
    return out
