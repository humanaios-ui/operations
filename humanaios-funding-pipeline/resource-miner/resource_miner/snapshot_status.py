"""Read-only reconciliation of stored Resource Miner candidates with curated source holds.

Historical snapshots are immutable evidence of prior discovery, not authority to
ignore subsequently recorded source failures. Only explicit held statuses from
the curated funding catalog may suppress an exact matching public source URL.
"""
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from .models import HELD_SOURCE_STATUSES

MAX_CATALOG_BYTES = 2_000_000
PUBLIC_FUNDING_SOURCE = "HumanAIOS Funding Pipeline"


def _exact_source_url(value: object) -> str | None:
    """Normalize origin case/fragment, preserving path and semantic query exactly."""
    if not isinstance(value, str) or not 1 <= len(value) <= 2000:
        return None
    try:
        parsed = urlsplit(value)
        if (parsed.scheme.lower() != "https" or not parsed.hostname or
                parsed.username is not None or parsed.password is not None or
                parsed.port not in (None, 443)):
            return None
        host = parsed.hostname.lower().rstrip(".")
        if not host or "." not in host:
            return None
        # Preserve semantic query values, path case, and path slash differences.
        return urlunsplit(("https", host, parsed.path, parsed.query, ""))
    except ValueError:
        return None


def reconcile_snapshot_source_holds(
    snapshot: list[dict], catalog_path: str | Path,
) -> tuple[list[dict], int]:
    """Overlay held source statuses without modifying snapshots or catalog.

    Missing or malformed catalog fails closed: stale snapshot search must not
    silently proceed while the source-health feedback cannot be inspected.
    A held observation does not establish that a posting is permanently closed.
    """
    path = Path(catalog_path)
    with path.open("rb") as handle:
        data = handle.read(MAX_CATALOG_BYTES + 1)
    if len(data) > MAX_CATALOG_BYTES:
        raise ValueError("Curated source catalog exceeds read limit")
    catalog = json.loads(data)
    if not isinstance(catalog, list) or not isinstance(snapshot, list):
        raise ValueError("Expected source catalog and stored snapshot arrays")

    holds: dict[str, str] = {}
    for source in catalog:
        if not isinstance(source, dict):
            continue
        status = source.get("source_verification_status")
        # No arbitrary user text, unreviewed statuses, or positive assertions.
        if not isinstance(status, str) or status not in HELD_SOURCE_STATUSES:
            continue
        url = _exact_source_url(source.get("url"))
        if url:
            # Conflicting negative statuses stay held rather than being cleared.
            holds[url] = "RECHECK_REQUIRED" if url in holds and holds[url] != status else status

    projection: list[dict] = []
    held_count = 0
    for row in snapshot:
        if not isinstance(row, dict):
            raise ValueError("Malformed candidate in stored snapshot")
        copy = dict(row)
        if row.get("source_name") == PUBLIC_FUNDING_SOURCE:
            original_url = (row.get("canonical_url") or row.get("source_url") or
                            row.get("primary_source_url"))
            url = _exact_source_url(original_url)
            if url in holds:
                copy["source_verification_status"] = holds[url]
                held_count += 1
        projection.append(copy)
    return projection, held_count
