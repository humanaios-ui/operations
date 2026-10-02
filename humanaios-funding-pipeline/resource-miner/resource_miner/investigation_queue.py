from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .hackerone_portfolio import HackerOnePortfolioSnapshot
from .security_capability import (
    OBSERVED_AVAILABLE,
    OBSERVED_UNAVAILABLE,
    SecurityCapabilityProfile,
    capability_for_asset_type,
)


@dataclass
class InvestigationQueueEntry:
    program_handle: str
    program_name: str
    scope_id: str
    asset_identifier: str
    asset_type: str
    eligible_for_submission: bool
    eligible_for_bounty: bool
    review_mode_candidate: str
    required_capability: str
    capability_state: str
    capability_coverage: float
    capability_evidence_refs: list[str]
    evidence_gaps: list[str]
    review_state: str
    authorization_state: str
    effort_class: str
    readiness_score: float
    ranking_rationale: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RankedInvestigationQueue:
    schema: str = "humanaios.hackerone-ranked-investigation-queue.v1"
    portfolio_observed_at: str = ""
    capability_source: str = ""
    entries: list[InvestigationQueueEntry] = field(default_factory=list)
    observation_failures: list[dict[str, Any]] = field(default_factory=list)
    authority_effect: str = "NONE"
    execution_capability: str = "NONE"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        counts: dict[str, int] = {}
        for entry in self.entries:
            counts[entry.review_state] = counts.get(entry.review_state, 0) + 1
        data["summary"] = {
            "entry_count": len(self.entries),
            "observation_failure_count": len(self.observation_failures),
            "review_state_counts": counts,
            "authorized_entry_count": 0,
        }
        return data


def _score(
    *,
    program_open: bool,
    submission_eligible: bool,
    bounty_eligible: bool,
    capability_coverage: float,
    capability_state: str,
) -> tuple[float, list[str]]:
    if not submission_eligible:
        return 0.0, ["asset is not eligible for submission"]

    score = 0.0
    rationale: list[str] = []

    # Readiness dominates the score. Reward eligibility is only a small signal.
    bounded_coverage = max(0.0, min(capability_coverage, 1.0))
    if capability_state == OBSERVED_AVAILABLE:
        capability_points = 50.0 * bounded_coverage
        rationale.append(f"evidenced capability contributes {capability_points:.1f}/50")
    elif capability_state == OBSERVED_UNAVAILABLE:
        capability_points = 10.0 * bounded_coverage
        rationale.append(f"partial prerequisites contribute {capability_points:.1f}/10; capability is unavailable")
    else:
        capability_points = 20.0 * bounded_coverage
        rationale.append(f"partial prerequisites contribute {capability_points:.1f}/20; capability remains unknown")
    score += capability_points

    if program_open:
        score += 20.0
        rationale.append("program submission state is open (+20)")
    else:
        rationale.append("program is not open (+0)")

    score += 15.0
    rationale.append("scope was observed in the current portfolio snapshot (+15)")

    if capability_state == OBSERVED_AVAILABLE:
        score += 10.0
        rationale.append("capability prerequisites are explicitly observed available (+10)")
    elif capability_state == OBSERVED_UNAVAILABLE:
        rationale.append("required capability was explicitly observed unavailable (+0)")
    else:
        rationale.append("capability evidence is incomplete (+0)")

    if bounty_eligible:
        score += 5.0
        rationale.append("asset is bounty-eligible (+5)")

    return round(score, 2), rationale


def build_ranked_queue(
    portfolio: HackerOnePortfolioSnapshot,
    capability_profile: SecurityCapabilityProfile,
    *,
    include_blocked: bool = True,
) -> RankedInvestigationQueue:
    queue = RankedInvestigationQueue(
        portfolio_observed_at=portfolio.observed_at,
        capability_source=capability_profile.source,
    )

    for program in portfolio.programs:
        if program.graph is None:
            queue.observation_failures.append(
                {
                    "handle": program.handle,
                    "state": program.state,
                    "error_type": program.error_type,
                    "error_detail": program.error_detail,
                }
            )
            continue

        graph = program.graph
        program_open = graph.submission_state.casefold() == "open"

        for asset in graph.assets:
            capability_id, mode, effort = capability_for_asset_type(asset.asset_type)
            evidence = capability_profile.get(capability_id)
            gaps = list(evidence.missing_tools)
            if not evidence.evidence_refs:
                gaps.append(f"no_evidence_ref:{capability_id}")
            if evidence.state != OBSERVED_AVAILABLE:
                gaps.append(f"capability_state:{evidence.state}")
            if not program_open:
                gaps.append(f"program_submission_state:{graph.submission_state}")
            if not asset.eligible_for_submission:
                gaps.append("asset_not_eligible_for_submission")

            score, rationale = _score(
                program_open=program_open,
                submission_eligible=asset.eligible_for_submission,
                bounty_eligible=asset.eligible_for_bounty,
                capability_coverage=evidence.coverage,
                capability_state=evidence.state,
            )

            if not asset.eligible_for_submission or not program_open:
                review_state = "BLOCKED_BY_SCOPE_STATE"
            elif evidence.state == OBSERVED_AVAILABLE:
                review_state = "READY_FOR_POLICY_AND_METHOD_REVIEW"
            elif evidence.state == OBSERVED_UNAVAILABLE:
                review_state = "CAPABILITY_UNAVAILABLE"
            else:
                review_state = "CAPABILITY_EVIDENCE_REQUIRED"

            entry = InvestigationQueueEntry(
                program_handle=graph.handle,
                program_name=graph.name,
                scope_id=asset.scope_id,
                asset_identifier=asset.asset_identifier,
                asset_type=asset.asset_type,
                eligible_for_submission=asset.eligible_for_submission,
                eligible_for_bounty=asset.eligible_for_bounty,
                review_mode_candidate=mode,
                required_capability=capability_id,
                capability_state=evidence.state,
                capability_coverage=evidence.coverage,
                capability_evidence_refs=list(evidence.evidence_refs),
                evidence_gaps=sorted(set(gaps)),
                review_state=review_state,
                # Ranking can never self-upgrade into permission.
                authorization_state="NOT_EVALUATED",
                effort_class=effort,
                readiness_score=score,
                ranking_rationale=rationale,
            )
            if include_blocked or review_state != "BLOCKED_BY_SCOPE_STATE":
                queue.entries.append(entry)

    queue.entries.sort(
        key=lambda item: (
            -item.readiness_score,
            item.program_handle.casefold(),
            item.asset_type.casefold(),
            item.asset_identifier.casefold(),
        )
    )
    return queue
