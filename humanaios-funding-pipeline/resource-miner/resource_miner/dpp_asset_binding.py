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
    schema: str = "humanaios.hackerone-dpp-asset-binding.v2"
    ready_entries: int = 0
    policy_asset_patterns: list[str] = field(default_factory=list)
    bindings: list[DPPAssetBinding] = field(default_factory=list)
    dpp_policy_present: bool = False
    asset_tiers_heading_present: bool = False
    scope_exclusions_heading_present: bool = False
    asset_tier_section_length: int = 0
    extraction_state: str = "NOT_EVALUATED"
    authority_effect: str = "NONE"
    execution_capability: str = "NONE"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["summary"] = {
            "ready_entries": self.ready_entries,
            "policy_asset_pattern_count": len(self.policy_asset_patterns),
            "dpp_asset_bound_entries": len(self.bindings),
            "candidate_ready_ranks": [item.ready_rank for item in self.bindings],
            "dpp_policy_present": self.dpp_policy_present,
            "asset_tiers_heading_present": self.asset_tiers_heading_present,
            "scope_exclusions_heading_present": self.scope_exclusions_heading_present,
            "asset_tier_section_length": self.asset_tier_section_length,
            "extraction_state": self.extraction_state,
        }
        return data


def _dpp_asset_tier_section(policy: str) -> tuple[str, dict[str, Any]]:
    text = policy or ""
    lowered = text.casefold()

    dpp_present = "data protection program" in lowered
    asset_tiers = lowered.find("asset tiers")
    exclusions = lowered.find("scope exclusions", asset_tiers if asset_tiers >= 0 else 0)

    diagnostics: dict[str, Any] = {
        "dpp_policy_present": dpp_present,
        "asset_tiers_heading_present": asset_tiers >= 0,
        "scope_exclusions_heading_present": exclusions >= 0,
        "asset_tier_section_length": 0,
        "extraction_state": "NOT_EVALUATED",
    }

    if not dpp_present:
        diagnostics["extraction_state"] = "NO_DPP_POLICY"
        return "", diagnostics

    if asset_tiers < 0:
        diagnostics["extraction_state"] = "NO_ASSET_TIERS_SECTION"
        return "", diagnostics

    end = exclusions if exclusions >= 0 else len(text)
    section = text[asset_tiers:end]
    diagnostics["asset_tier_section_length"] = len(section)
    return section, diagnostics


def extract_dpp_asset_patterns(policy: str) -> tuple[list[str], dict[str, Any]]:
    section, diagnostics = _dpp_asset_tier_section(policy)
    if not section:
        return [], diagnostics

    # HackerOne policy text can arrive as plain text, Markdown, or HTML-ish
    # rich text. Restrict parsing to the Asset Tiers section, then recognize
    # asset-shaped tokens regardless of bullets or inline formatting.
    url_re = re.compile(r"https?://[^\s<>()\]\[{}\"']+", re.IGNORECASE)
    package_re = re.compile(
        r"(?<![A-Za-z0-9_.-])com\.(?:[A-Za-z0-9_-]+\.)+[A-Za-z0-9_-]+",
        re.IGNORECASE,
    )
    wildcard_re = re.compile(
        r"(?<![A-Za-z0-9_.-])\*\.(?:[A-Za-z0-9_-]+\.)+[A-Za-z0-9_-]+",
        re.IGNORECASE,
    )
    domain_re = re.compile(
        r"(?<![@A-Za-z0-9_-])(?:[A-Za-z0-9_-]+\.)+[A-Za-z]{2,}(?![A-Za-z0-9_-])",
        re.IGNORECASE,
    )
    numeric_re = re.compile(r"(?<!\d)\d{6,}(?!\d)")

    candidates: list[str] = []
    occupied: list[tuple[int, int]] = []

    def add_matches(regex: re.Pattern[str]) -> None:
        for match in regex.finditer(section):
            span = match.span()
            if any(not (span[1] <= a or span[0] >= b) for a, b in occupied):
                continue
            token = match.group(0).rstrip(".,;:")
            candidates.append(token)
            occupied.append(span)

    # Prefer specific/compound forms before generic domains.
    add_matches(url_re)
    add_matches(package_re)
    add_matches(wildcard_re)
    add_matches(domain_re)
    add_matches(numeric_re)

    seen: set[str] = set()
    ordered: list[str] = []
    for pattern in candidates:
        key = pattern.casefold().rstrip("/")
        if key in seen:
            continue
        seen.add(key)
        ordered.append(pattern)

    diagnostics["extraction_state"] = (
        "PATTERNS_EXTRACTED"
        if ordered
        else "ASSET_TIERS_PRESENT_ZERO_PATTERNS"
    )
    return ordered, diagnostics


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
    diagnostics_list: list[dict[str, Any]] = []
    for policy in policies:
        extracted, diagnostics = extract_dpp_asset_patterns(policy)
        patterns.extend(extracted)
        diagnostics_list.append(diagnostics)

    deduped: list[str] = []
    seen: set[str] = set()
    for pattern in patterns:
        key = pattern.casefold().rstrip("/")
        if key in seen:
            continue
        seen.add(key)
        deduped.append(pattern)

    states = [str(item.get("extraction_state") or "") for item in diagnostics_list]
    if "PATTERNS_EXTRACTED" in states:
        extraction_state = "PATTERNS_EXTRACTED"
    elif "ASSET_TIERS_PRESENT_ZERO_PATTERNS" in states:
        extraction_state = "ASSET_TIERS_PRESENT_ZERO_PATTERNS"
    elif "NO_ASSET_TIERS_SECTION" in states:
        extraction_state = "NO_ASSET_TIERS_SECTION"
    elif "NO_DPP_POLICY" in states:
        extraction_state = "NO_DPP_POLICY"
    else:
        extraction_state = "NO_POLICY_TEXT"

    result = DPPBindingResult(
        policy_asset_patterns=deduped,
        dpp_policy_present=any(bool(x.get("dpp_policy_present")) for x in diagnostics_list),
        asset_tiers_heading_present=any(
            bool(x.get("asset_tiers_heading_present")) for x in diagnostics_list
        ),
        scope_exclusions_heading_present=any(
            bool(x.get("scope_exclusions_heading_present")) for x in diagnostics_list
        ),
        asset_tier_section_length=sum(
            int(x.get("asset_tier_section_length") or 0) for x in diagnostics_list
        ),
        extraction_state=extraction_state,
    )

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
