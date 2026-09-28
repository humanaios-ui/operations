from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import NeedMatch, ResourceCandidate


def load_needs(path: str | Path) -> list[dict[str, Any]]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Needs graph must be a JSON array")
    return data


def map_to_needs(resource: ResourceCandidate, needs: list[dict[str, Any]]) -> list[NeedMatch]:
    text = " ".join(
        [resource.title, resource.description, resource.sponsor, " ".join(resource.tags), " ".join(resource.resource_types)]
    ).lower()
    types = set(resource.resource_types)
    matches: list[NeedMatch] = []
    for need in needs:
        need_id = str(need.get("need_id") or "").strip()
        if not need_id:
            continue
        configured_types = {str(x) for x in need.get("resource_types", [])}
        signals = [str(x).lower() for x in need.get("signals", []) if str(x).strip()]
        type_hits = sorted(types & configured_types)
        signal_hits = sorted({s for s in signals if s in text})
        type_score = 0.45 if type_hits else 0.0
        signal_score = min(0.55, 0.11 * len(signal_hits))
        score = round(min(1.0, type_score + signal_score), 2)
        if score >= 0.2:
            matches.append(
                NeedMatch(
                    need_id=need_id,
                    label=str(need.get("label") or need_id),
                    score=score,
                    signals=[*(f"type:{x}" for x in type_hits), *(f"text:{x}" for x in signal_hits)],
                )
            )
    return sorted(matches, key=lambda x: (-x.score, x.need_id))
