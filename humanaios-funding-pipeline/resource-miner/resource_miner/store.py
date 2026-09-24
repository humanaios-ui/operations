from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .models import ResourceCandidate


def dedupe(resources: Iterable[ResourceCandidate]) -> list[ResourceCandidate]:
    by_url: dict[str, ResourceCandidate] = {}
    for resource in resources:
        existing = by_url.get(resource.canonical_url)
        if existing is None:
            by_url[resource.canonical_url] = resource
            continue
        current_richness = len(existing.description) + len(existing.tags) * 10 + len(existing.cash_mentions_usd) * 20
        new_richness = len(resource.description) + len(resource.tags) * 10 + len(resource.cash_mentions_usd) * 20
        winner, other = (resource, existing) if new_richness > current_richness else (existing, resource)
        known = {(e.url, e.kind, e.claim) for e in winner.evidence}
        for evidence in other.evidence:
            key = (evidence.url, evidence.kind, evidence.claim)
            if key not in known:
                winner.evidence.append(evidence)
                known.add(key)
        by_url[resource.canonical_url] = winner
    return list(by_url.values())


def write_jsonl(path: str | Path, resources: Iterable[ResourceCandidate]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "".join(json.dumps(resource.to_dict(), ensure_ascii=False, sort_keys=True) + "\n" for resource in resources),
        encoding="utf-8",
    )
