from __future__ import annotations

import json
from copy import deepcopy
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
        # Discount observations are provenance, independent of description richness.
        observations = []
        for candidate in (existing, resource):
            offer = candidate.discount_offer
            if offer:
                for observation in offer.get("observations", [offer]):
                    if observation not in observations:
                        observations.append(deepcopy(observation))
        if observations:
            if len(observations) == 1:
                winner.discount_offer = observations[0]
            else:
                winner.discount_offer = {
                    "verification": "CONFLICTING_OBSERVATIONS",
                    "observations": observations,
                    "eligibility": "UNASSESSED", "code_status": "NOT_TESTED",
                }
            # Another source must not erase a hold or promote an unverified offer.
            winner.source_verification_status = "RECHECK_REQUIRED"
            winner.status = "UNVERIFIED"
            winner.eligibility_assessed = False
            winner.eligibility_status = "UNASSESSED"
            winner.last_verified_at = None
            winner.value_text = ""
            winner.cash_mentions_usd = []
        known = {(e.url, e.kind, e.claim, e.observed_at) for e in winner.evidence}
        for evidence in other.evidence:
            key = (evidence.url, evidence.kind, evidence.claim, evidence.observed_at)
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
