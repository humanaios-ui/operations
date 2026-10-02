from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

OBSERVED_AVAILABLE = "OBSERVED_AVAILABLE"
OBSERVED_UNAVAILABLE = "OBSERVED_UNAVAILABLE"
NOT_SCANNED = "NOT_SCANNED"
PERMISSION_DENIED = "PERMISSION_DENIED"
UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class CapabilityEvidence:
    capability_id: str
    state: str
    required_tools: list[str]
    observed_tools: list[str]
    evidence_refs: list[str]
    missing_tools: list[str]
    coverage: float
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SecurityCapabilityProfile:
    schema: str = "humanaios.security-capability-profile.v1"
    source: str = "UNSPECIFIED"
    observed_at: str | None = None
    capabilities: dict[str, CapabilityEvidence] = field(default_factory=dict)
    omissions: list[dict[str, Any]] = field(default_factory=list)
    authority_effect: str = "NONE"

    def get(self, capability_id: str) -> CapabilityEvidence:
        return self.capabilities.get(
            capability_id,
            CapabilityEvidence(
                capability_id=capability_id,
                state=UNKNOWN,
                required_tools=[],
                observed_tools=[],
                evidence_refs=[],
                missing_tools=[],
                coverage=0.0,
                note="capability not represented in profile",
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "source": self.source,
            "observed_at": self.observed_at,
            "capabilities": {key: value.to_dict() for key, value in self.capabilities.items()},
            "omissions": self.omissions,
            "authority_effect": self.authority_effect,
        }


# These are review-capability prerequisites, not permission to interact with any target.
# They intentionally use ordinary development/inspection tools only.
CAPABILITY_REQUIREMENTS: dict[str, tuple[str, ...]] = {
    "web_http_review": ("python3", "curl"),
    "source_code_review": ("git", "python3"),
    "ai_model_review": ("python3", "ollama"),
    "android_app_review": ("adb", "java"),
    "ios_app_review": ("xcodebuild",),
    "network_scope_review": ("dedicated_receipt",),
    "local_executable_review": ("dedicated_receipt",),
    "windows_app_review": ("dedicated_receipt",),
}

# Capabilities that must remain UNKNOWN unless separately evidenced by a future,
# purpose-built receipt. The machine inventory alone is not enough.
REQUIRES_DEDICATED_RECEIPT = {
    "hardware_iot_review",
    "smart_contract_review",
    "other_asset_review",
}


def _tool_states(machine_graph: dict[str, Any]) -> dict[str, str]:
    states: dict[str, str] = {}
    for node in machine_graph.get("nodes", []):
        if not isinstance(node, dict) or node.get("type") != "Tool":
            continue
        observed = node.get("observed") or {}
        name = str(observed.get("name") or "").strip().casefold()
        if not name:
            continue
        states[name] = str(node.get("state") or UNKNOWN)
    return states


def _derive_capability(
    capability_id: str,
    required_tools: tuple[str, ...],
    states: dict[str, str],
) -> CapabilityEvidence:
    observed = [tool for tool in required_tools if states.get(tool) == OBSERVED_AVAILABLE]
    explicitly_unavailable = [
        tool for tool in required_tools if states.get(tool) == OBSERVED_UNAVAILABLE
    ]
    unknown = [tool for tool in required_tools if tool not in states or states.get(tool) in {UNKNOWN, NOT_SCANNED, PERMISSION_DENIED}]
    coverage = len(observed) / len(required_tools) if required_tools else 0.0

    if len(observed) == len(required_tools):
        state = OBSERVED_AVAILABLE
        note = "all required review-tool observations are available"
    elif explicitly_unavailable:
        state = OBSERVED_UNAVAILABLE
        note = "one or more required review tools were explicitly observed unavailable"
    else:
        state = UNKNOWN
        note = "required review-tool evidence is incomplete"

    return CapabilityEvidence(
        capability_id=capability_id,
        state=state,
        required_tools=list(required_tools),
        observed_tools=observed,
        evidence_refs=[f"machine-graph:tool:{tool}:{states.get(tool, UNKNOWN)}" for tool in required_tools],
        missing_tools=explicitly_unavailable + unknown,
        coverage=round(coverage, 4),
        note=note,
    )


def unknown_capability_profile(source: str = "NO_MACHINE_GRAPH") -> SecurityCapabilityProfile:
    profile = SecurityCapabilityProfile(source=source)
    for capability_id, required in CAPABILITY_REQUIREMENTS.items():
        profile.capabilities[capability_id] = CapabilityEvidence(
            capability_id=capability_id,
            state=UNKNOWN,
            required_tools=list(required),
            observed_tools=[],
            evidence_refs=[],
            missing_tools=list(required),
            coverage=0.0,
            note="no machine capability evidence supplied",
        )
    for capability_id in REQUIRES_DEDICATED_RECEIPT:
        profile.capabilities[capability_id] = CapabilityEvidence(
            capability_id=capability_id,
            state=UNKNOWN,
            required_tools=[],
            observed_tools=[],
            evidence_refs=[],
            missing_tools=[],
            coverage=0.0,
            note="requires dedicated capability receipt; machine inventory is insufficient",
        )
    return profile


def profile_from_machine_graph(machine_graph: dict[str, Any], *, source: str = "machine-graph") -> SecurityCapabilityProfile:
    if not isinstance(machine_graph, dict):
        raise ValueError("machine graph must be a JSON object")
    states = _tool_states(machine_graph)
    profile = SecurityCapabilityProfile(
        source=source,
        observed_at=str(machine_graph.get("observed_at") or "") or None,
        omissions=list(machine_graph.get("omissions") or []),
    )
    for capability_id, required in CAPABILITY_REQUIREMENTS.items():
        profile.capabilities[capability_id] = _derive_capability(capability_id, required, states)
    for capability_id in REQUIRES_DEDICATED_RECEIPT:
        profile.capabilities[capability_id] = CapabilityEvidence(
            capability_id=capability_id,
            state=UNKNOWN,
            required_tools=[],
            observed_tools=[],
            evidence_refs=[],
            missing_tools=[],
            coverage=0.0,
            note="requires dedicated capability receipt; machine inventory is insufficient",
        )
    return profile


def normalize_asset_type(asset_type: str) -> str:
    return "".join(ch for ch in asset_type.casefold() if ch.isalnum())


ASSET_CAPABILITY_MAP: dict[str, tuple[str, str, str]] = {
    "url": ("web_http_review", "WEB_REVIEW", "LOW"),
    "domain": ("web_http_review", "WEB_REVIEW", "LOW"),
    "wildcard": ("web_http_review", "WEB_REVIEW", "MEDIUM"),
    "sourcecode": ("source_code_review", "SOURCE_REVIEW", "MEDIUM"),
    "aimodel": ("ai_model_review", "AI_MODEL_REVIEW", "MEDIUM"),
    "cidr": ("network_scope_review", "NETWORK_SCOPE_REVIEW", "HIGH"),
    "ipaddress": ("network_scope_review", "NETWORK_SCOPE_REVIEW", "HIGH"),
    "androidapk": ("android_app_review", "ANDROID_APP_REVIEW", "HIGH"),
    "androidplaystore": ("android_app_review", "ANDROID_APP_REVIEW", "HIGH"),
    "googleplayappid": ("android_app_review", "ANDROID_APP_REVIEW", "HIGH"),
    "iosipa": ("ios_app_review", "IOS_APP_REVIEW", "HIGH"),
    "iosappstore": ("ios_app_review", "IOS_APP_REVIEW", "HIGH"),
    "iostestflight": ("ios_app_review", "IOS_APP_REVIEW", "HIGH"),
    "applestoreappid": ("ios_app_review", "IOS_APP_REVIEW", "HIGH"),
    "windowsmicrosoftstore": ("windows_app_review", "WINDOWS_APP_REVIEW", "HIGH"),
    "executable": ("local_executable_review", "EXECUTABLE_REVIEW", "HIGH"),
    "hardware": ("hardware_iot_review", "HARDWARE_REVIEW", "HIGH"),
    "hardwareiot": ("hardware_iot_review", "HARDWARE_REVIEW", "HIGH"),
    "smartcontract": ("smart_contract_review", "SMART_CONTRACT_REVIEW", "HIGH"),
    "otherasset": ("other_asset_review", "OTHER_REVIEW", "HIGH"),
    "other": ("other_asset_review", "OTHER_REVIEW", "HIGH"),
}


def capability_for_asset_type(asset_type: str) -> tuple[str, str, str]:
    normalized = normalize_asset_type(asset_type)
    return ASSET_CAPABILITY_MAP.get(
        normalized,
        ("other_asset_review", "OTHER_REVIEW", "HIGH"),
    )
