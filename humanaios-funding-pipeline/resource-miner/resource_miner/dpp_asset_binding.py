from __future__ import annotations

from dataclasses import asdict, dataclass, field
import re
from typing import Any
from urllib.parse import urlparse


READY_STATE = "READY_FOR_POLICY_AND_METHOD_REVIEW"


@dataclass
class DPPAssetBinding:
    ready_rank: int
    scope_id: str
    asset_type: str
    policy_pattern: str
    binding_basis: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DPPBindingResult:
    schema: str = "humanaios.hackerone-dpp-asset-binding.v1"
    ready_entries: int = 0
    policy_asset_patterns: list[str] = field(default_factory=list)
    bindings: list[DPPAssetBinding] = field(default_factory=list)
    authority_effect: str = "NONE"
    execution_capability: str = "NONE"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["summary"] = {
            "ready_entries": self.ready_entries,
            "policy_asset_pattern_count": len(self.policy_asset_patterns),
            "dpp_asset_bound_entries": len(self.bindings),
            "candidate_ready_ranks": [item.ready_rank for item in self.bindings],
        }
        return data


def _dpp_asset_tier_section(policy: str) -> str:
    text = policy or ""
    lowered = text.casefold()
    start = lowered.find("data protection program")
    if start < 0:
        return ""

    asset_tiers = lowered.find("asset tiers", start)
    if asset_tiers < 0:
        return ""

    end = lowered.find("scope exclusions", asset_tiers)
    if end < 0:
        end = len(text)
    return text[asset_tiers:end]


def extract_dpp_asset_patterns(policy: str) -> list[str]:
    section = _dpp_asset_tier_section(policy)
    if not section:
        return []

    patterns: list[str] = []
    for raw in section.splitlines():
        line = raw.strip()
        if not line:
            continue
        normalized = line.casefold()
        if normalized in {"asset tiers", "tier 1", "tier 2", "tier 3"}:
            continue

        token = line.split("(", 1)[0].strip()
        token = token.split()[0] if token else ""
        if not token:
            continue

        is_url = token.startswith(("https://", "http://"))
        is_wildcard = token.startswith("*.") and "." in token[2:]
        is_numeric = token.isdigit() and len(token) >= 6
        is_package = token.casefold().startswith("com.") and token.count(".") >= 2
        is_domain = bool(
            re.fullmatch(r"[A-Za-z0-9*._-]+\.[A-Za-z0-9._-]+", token)
        )

        if is_url or is_wildcard or is_numeric or is_package or is_domain:
            patterns.append(token)

    seen: set[str] = set()
    ordered: list[str] = []
    for pattern in patterns:
        key = pattern.casefold()
        if key in seen:
            continue
        seen.add(key)
        ordered.append(pattern)
    return ordered


def _host(value: str) -> str:
    value = value.strip().casefold()
    parsed = urlparse(value if "://" in value else f"//{value}")
    return (parsed.hostname or value).rstrip(".")


def asset_matches_policy_pattern(identifier: str, pattern: str) -> tuple[bool, str]:
    asset = (identifier or "").strip()
    policy_pattern = (pattern or "").strip()
    if not asset or not policy_pattern:
        return False, ""

    if asset.casefold().rstrip("/") == policy_pattern.casefold().rstrip("/"):
        return True, "exact_policy_asset_match"

    if policy_pattern.startswith("*."):
        suffix = policy_pattern[1:].casefold()
        asset_host = _host(asset)
        if asset_host.endswith(suffix) and asset_host != policy_pattern[2:].casefold():
            return True, "wildcard_policy_asset_match"

    pattern_host = _host(policy_pattern)
    asset_host = _host(asset)
    if (
        "://" not in policy_pattern
        and "." in policy_pattern
        and asset_host == pattern_host
    ):
        return True, "host_policy_asset_match"

    return False, ""


def bind_ready_assets_to_dpp_policy(payload: dict[str, Any]) -> DPPBindingResult:
    programs = list((payload.get("portfolio") or {}).get("programs") or [])
    entries = list((payload.get("ranked_queue") or {}).get("entries") or [])

    policies: list[str] = []
    for program in programs:
        graph = program.get("graph") or {}
        policy = str(graph.get("policy") or "")
        if policy:
            policies.append(policy)

    patterns: list[str] = []
    for policy in policies:
        patterns.extend(extract_dpp_asset_patterns(policy))

    deduped: list[str] = []
    seen: set[str] = set()
    for pattern in patterns:
        key = pattern.casefold()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(pattern)

    result = DPPBindingResult(policy_asset_patterns=deduped)

    ready_rank = 0
    for entry in entries:
        if entry.get("review_state") != READY_STATE:
            continue
        ready_rank += 1
        result.ready_entries += 1

        identifier = str(entry.get("asset_identifier") or "")
        for pattern in deduped:
            matched, basis = asset_matches_policy_pattern(identifier, pattern)
            if not matched:
                continue
            result.bindings.append(
                DPPAssetBinding(
                    ready_rank=ready_rank,
                    scope_id=str(entry.get("scope_id") or ""),
                    asset_type=str(entry.get("asset_type") or ""),
                    policy_pattern=pattern,
                    binding_basis=basis,
                )
            )
            break

    return result
