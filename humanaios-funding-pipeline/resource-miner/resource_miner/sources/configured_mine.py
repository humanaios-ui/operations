from __future__ import annotations

import hashlib
import urllib.request
from typing import Any, Callable

from ..models import EvidenceRef, ResourceMine
from ..normalize import normalize_generic, utcnow_iso

MAX_OBSERVATION_BYTES = 1_048_576
Transport = Callable[[str], dict[str, Any]]


def _default_transport(url: str) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "HumanAIOS-ResourceMiner/0.1"},
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        body = response.read(MAX_OBSERVATION_BYTES + 1)
        if len(body) > MAX_OBSERVATION_BYTES:
            raise ValueError("configured mine observation exceeded byte limit")
        return {
            "status": int(getattr(response, "status", 200)),
            "final_url": str(response.geturl()),
            "content_type": str(response.headers.get("Content-Type") or ""),
            "body": body,
        }


def discover(
    mine: ResourceMine,
    *,
    transport: Transport = _default_transport,
):
    """Re-observe configured bounded opportunities without broad crawling."""
    observed = utcnow_iso()
    rows = mine.config.get("opportunities") or []
    if not isinstance(rows, list):
        raise ValueError("configured_mine opportunities must be a list")

    for row in rows:
        if not isinstance(row, dict):
            continue
        title = str(row.get("title") or "").strip()
        url = str(row.get("url") or "").strip()
        opportunity_kind = str(
            row.get("opportunity_kind") or "configured_opportunity"
        ).strip()
        if not title or not url:
            continue

        observation: dict[str, Any] = {}
        evidence: list[EvidenceRef] = []
        if row.get("observe_url", True):
            result = transport(url)
            body = result.get("body") or b""
            if not isinstance(body, (bytes, bytearray)):
                raise ValueError("configured mine transport body must be bytes")
            digest = hashlib.sha256(bytes(body)).hexdigest()
            observation = {
                "http_status": result.get("status"),
                "final_url": result.get("final_url"),
                "content_type": result.get("content_type"),
                "content_sha256": digest,
                "observed_bytes": len(body),
            }
            evidence.append(
                EvidenceRef(
                    url=url,
                    kind="mine_observation",
                    observed_at=observed,
                    claim=(
                        "Configured opportunity endpoint observed; "
                        f"content_sha256={digest}"
                    ),
                )
            )

        candidate = normalize_generic(
            title=title,
            url=url,
            source_name=mine.name,
            discovery_method="persistent_mine:configured",
            description=str(row.get("description") or ""),
            sponsor=str(row.get("sponsor") or mine.name),
            tags=[str(x) for x in row.get("tags") or []],
            body_text=str(row.get("body_text") or ""),
            observed_at=observed,
            source_category=str(row.get("source_category") or "") or None,
            mine_name=mine.name,
            mine_url=mine.canonical_url,
            opportunity_identity=str(row.get("opportunity_identity") or url),
            opportunity_kind=opportunity_kind,
            opportunity_source_kind="configured_endpoint",
            raw={"configured": row, "observation": observation},
        )
        candidate.evidence.extend(evidence)
        yield candidate
