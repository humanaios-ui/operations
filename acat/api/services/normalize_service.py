from __future__ import annotations

from pathlib import Path

import yaml

from acat.normalization.dedupe import build_dedupe_key
from acat.normalization.flags import derive_quality_flags
from acat.normalization.purity import validate_submission_purity

NORMALIZATION_VERSION = "0.1.0"
_ALIAS_CACHE: dict[str, str] | None = None


def _load_alias_map() -> dict[str, str]:
    global _ALIAS_CACHE
    if _ALIAS_CACHE is not None:
        return _ALIAS_CACHE

    alias_path = Path(__file__).resolve().parents[2] / "normalization" / "agent_aliases.yml"
    data = yaml.safe_load(alias_path.read_text(encoding="utf-8")) or {}

    alias_map: dict[str, str] = {}
    for canonical, aliases in data.items():
        alias_map[canonical.strip().lower()] = canonical.strip().lower()
        for alias in aliases or []:
            alias_map[str(alias).strip().lower()] = canonical.strip().lower()

    _ALIAS_CACHE = alias_map
    return alias_map


def canonicalize_agent_name(agent_name: str | None) -> str:
    raw = (agent_name or "").strip().lower()
    if not raw:
        return "unknown"

    alias_map = _load_alias_map()
    return alias_map.get(raw, raw)


def normalize_phase1_payload(payload: dict) -> dict:
    validate_submission_purity(payload.get("submission_purity"))

    normalized = dict(payload)

    normalized["agent_name_raw"] = payload.get("agent_name")
    normalized["agent_name_canonical"] = canonicalize_agent_name(payload.get("agent_name"))
    normalized["normalization_version"] = NORMALIZATION_VERSION
    normalized["dedupe_key"] = build_dedupe_key(normalized)

    existing_flags = list(normalized.get("quality_flags", []))
    derived_flags = derive_quality_flags(normalized)
    normalized["quality_flags"] = sorted(set(existing_flags + derived_flags))

    return normalized
