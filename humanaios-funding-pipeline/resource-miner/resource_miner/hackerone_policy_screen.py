from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .normalize import utcnow_iso


@dataclass
class PolicyScreenMatch:
    candidate_index: int
    program_handle: str
    program_name: str
    classification: str
    matched_phrases: list[str]
    submission_state: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PolicyScreenResult:
    schema: str = "humanaios.hackerone-policy-screen.v1"
    observed_at: str = ""
    programs_observed: int = 0
    matches: list[PolicyScreenMatch] = field(default_factory=list)
    authority_effect: str = "NONE"
    execution_capability: str = "NONE"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["summary"] = {
            "programs_observed": self.programs_observed,
            "explicit_dpp_passive_matches": sum(
                1 for item in self.matches
                if item.classification == "DPP_PASSIVE_EXPLICIT"
            ),
            "other_passive_policy_signals": sum(
                1 for item in self.matches
                if item.classification == "PASSIVE_POLICY_SIGNAL"
            ),
            "match_count": len(self.matches),
        }
        return data


DPP_TERMS = (
    "data protection program",
    "data protection",
)

PASSIVE_TERMS = (
    "passive monitoring and recon",
    "passive monitoring",
    "passive reconnaissance",
    "passive recon",
    "read-only verification",
    "publicly accessible data exposure",
)


def _classify_policy(policy: str) -> tuple[str | None, list[str]]:
    normalized = " ".join((policy or "").casefold().split())
    if not normalized:
        return None, []

    dpp_hits = [term for term in DPP_TERMS if term in normalized]
    passive_hits = [term for term in PASSIVE_TERMS if term in normalized]

    if dpp_hits and passive_hits:
        return "DPP_PASSIVE_EXPLICIT", sorted(set(dpp_hits + passive_hits))
    if passive_hits:
        return "PASSIVE_POLICY_SIGNAL", sorted(set(passive_hits))
    return None, []


def screen_program_policies(
    client: Any,
    *,
    page_size: int = 100,
    max_programs: int | None = None,
) -> PolicyScreenResult:
    """Screen account-visible HackerOne program policy metadata only.

    This performs no structured-scope requests and no target interaction.
    """
    rows = client.list_programs(page_size=page_size)
    if max_programs is not None:
        rows = rows[: max(max_programs, 0)]

    result = PolicyScreenResult(
        observed_at=utcnow_iso(),
        programs_observed=len(rows),
    )

    candidate_index = 0
    for row in rows:
        attrs = row.get("attributes") or {}
        policy = str(attrs.get("policy") or "")
        classification, matched = _classify_policy(policy)
        if classification is None:
            continue

        handle = str(attrs.get("handle") or "").strip()
        if not handle:
            continue

        candidate_index += 1
        result.matches.append(
            PolicyScreenMatch(
                candidate_index=candidate_index,
                program_handle=handle,
                program_name=str(attrs.get("name") or handle).strip(),
                classification=classification,
                matched_phrases=matched,
                submission_state=str(attrs.get("submission_state") or "unknown"),
            )
        )

    return result
