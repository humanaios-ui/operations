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
