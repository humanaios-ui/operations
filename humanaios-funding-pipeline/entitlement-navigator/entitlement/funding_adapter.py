from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _candidate_sources_paths(start: Path | None = None) -> list[Path]:
    """Return likely canonical HumanAIOS funding-pipeline source paths."""
    here = (start or Path(__file__).resolve()).resolve()
    candidates: list[Path] = []
    for parent in [here, *here.parents]:
        candidates.append(parent / "data" / "sources.json")
        candidates.append(parent / "humanaios-funding-pipeline" / "data" / "sources.json")
    # Preserve order while removing duplicates.
    seen: set[Path] = set()
    out: list[Path] = []
    for path in candidates:
        if path not in seen:
            seen.add(path)
            out.append(path)
    return out


def discover_sources_path(start: Path | None = None) -> Path | None:
    """Locate the canonical funding pipeline dataset when installed inside operations."""
    for path in _candidate_sources_paths(start):
        if path.is_file():
            return path
    return None


def load_sources(path: str | Path | None = None) -> tuple[list[dict[str, Any]], Path]:
    """Load canonical funding sources without mutating them."""
    resolved = Path(path).expanduser().resolve() if path else discover_sources_path()
    if resolved is None:
        raise FileNotFoundError(
            "HumanAIOS funding sources were not found. Expected humanaios-funding-pipeline/data/sources.json."
        )
    raw = json.loads(resolved.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("Funding sources dataset must be a JSON array")
    return [item for item in raw if isinstance(item, dict)], resolved


def search_sources(
    keyword: str = "",
    *,
    native_only: bool = False,
    categories: list[str] | None = None,
    limit: int = 50,
    path: str | Path | None = None,
) -> dict[str, Any]:
    """
    Search the existing HumanAIOS funding dataset.

    Results are discovery candidates only. Existing tags can route investigation but
    do not constitute a deterministic eligibility decision.
    """
    rows, resolved = load_sources(path)
    needle = keyword.strip().lower()
    allowed = {str(x).strip() for x in (categories or []) if str(x).strip()}
    hits: list[dict[str, Any]] = []
    for row in rows:
        if native_only and row.get("native_eligible") is not True:
            continue
        if allowed and str(row.get("category") or "") not in allowed:
            continue
        haystack = " ".join(
            str(row.get(k) or "")
            for k in ("name", "sponsor", "category", "notes", "source", "trl_fit")
        ).lower()
        tags = " ".join(str(x) for x in (row.get("eligibility_tags") or [])).lower()
        if needle and needle not in haystack and needle not in tags:
            continue
        hits.append(
            {
                "name": row.get("name"),
                "sponsor": row.get("sponsor"),
                "category": row.get("category"),
                "url": row.get("url"),
                "award_size": row.get("award_size"),
                "deadline": row.get("deadline"),
                "status": row.get("status"),
                "native_eligible_tag": row.get("native_eligible"),
                "eligibility_tags": row.get("eligibility_tags") or [],
                "classification": "GENERAL_OPPORTUNITY",
                "eligibility_assessed": False,
                "evidence_source": "humanaios-funding-pipeline/data/sources.json",
                "note": (
                    "Discovered from the canonical HumanAIOS funding dataset. Existing eligibility tags "
                    "route research but do not establish applicant eligibility."
                ),
            }
        )
        if len(hits) >= max(1, min(int(limit), 200)):
            break
    return {
        "source_path": str(resolved),
        "result_count": len(hits),
        "results": hits,
    }
