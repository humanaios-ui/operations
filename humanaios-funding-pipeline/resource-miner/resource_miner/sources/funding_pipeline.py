from __future__ import annotations

import json
from pathlib import Path

from ..normalize import normalize_generic, utcnow_iso


def discover(path: str | Path):
    observed = utcnow_iso()
    rows = json.loads(Path(path).read_text(encoding="utf-8"))
    for row in rows if isinstance(rows, list) else []:
        url = str(row.get("url") or "")
        title = str(row.get("name") or "")
        if not url or not title:
            continue
        notes = str(row.get("notes") or "")
        value = str(row.get("award_size") or "")
        tags = [str(x) for x in row.get("eligibility_tags") or []]
        candidate = normalize_generic(
            title=title,
            url=url,
            source_name="HumanAIOS Funding Pipeline",
            discovery_method="canonical_funding_pipeline",
            description=" ".join(x for x in [value, notes] if x),
            sponsor=str(row.get("sponsor") or ""),
            tags=[str(row.get("category") or ""), *tags],
            body_text=notes,
            observed_at=observed,
            raw=row,
        )
        candidate.deadline = row.get("deadline") or candidate.deadline
        candidate.status = str(row.get("status") or candidate.status).upper()
        yield candidate
