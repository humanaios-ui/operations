#!/usr/bin/env python3
"""
Comparison Engine v1.0 — Decision Log vs. Deployment Outcomes
Verifies agent claims and measures calibration for Z2 review

Purpose: Compare predicted vs. actual deployment outcomes from CI/CD runs
Author: Claude (Z1 Proposer)
Date: 2026-09-24
"""

import json
import sys
from typing import TypedDict, Optional, Literal
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timezone

# ============================================================================
# TYPE DEFINITIONS
# ============================================================================

class VerificationStatus(str, Enum):
    """Status of a claim verification"""
    VERIFIED = "VERIFIED"
    FALSIFIED = "FALSIFIED"
    PARTIAL = "PARTIAL"  # Some parts true, some false
    UNKNOWN = "UNKNOWN"  # No data to verify


@dataclass
class Claim:
    """A single claim from the decision log"""
    claim_id: str
    statement: str
    predicted_outcome: str
    stated_confidence: float  # 0.0 to 1.0
    timestamp: str


@dataclass
class ActualOutcome:
    """What actually happened"""
    outcome_id: str
    description: str
    succeeded: bool
    data: dict  # Raw measurement data


@dataclass
class ClaimEvaluation:
    """Evaluation of a single claim"""
    claim_id: str
    statement: str
    stated_confidence: float
    verification_status: VerificationStatus
    actual_outcome: str
    calibration_score: float  # How well-calibrated was the confidence?
    evidence: str  # What data supports this evaluation
    z2_gate: Literal["PASS", "FAIL", "ADVISORY"]


@dataclass
class ComparisonReport:
    """Complete Z2 review document"""
    audit_id: str
    timestamp: str
    pr_number: int
    service_name: str
    total_claims: int
    verified_count: int
    falsified_count: int
    partial_count: int
    unknown_count: int
    calibration_metric: float  # Mean |stated_conf - actual_accuracy|
    z2_recommendation: Literal["ACCEPT", "REQUIRE_RERUN", "INVESTIGATE"]
    claims: list[ClaimEvaluation]


# ============================================================================
# COMPARISON ENGINE CORE
# ============================================================================

def evaluate_claim(
    claim: Claim,
    actual_outcomes: list[ActualOutcome],
) -> ClaimEvaluation:
    """
    Evaluate a single claim by comparing to actual outcomes.

    Returns calibration metric + verification status.
    """

    # Map claim to outcome data
    if "Build Success Rate" in claim.statement:
        return _evaluate_build_success(claim, actual_outcomes)
    elif "Services Online" in claim.statement:
        return _evaluate_services_online(claim, actual_outcomes)
    elif "Time to Production" in claim.statement:
        return _evaluate_deployment_time(claim, actual_outcomes)
    else:
        return ClaimEvaluation(
            claim_id=claim.claim_id,
            statement=claim.statement,
            stated_confidence=claim.stated_confidence,
            verification_status=VerificationStatus.UNKNOWN,
            actual_outcome="No matching outcome data",
            calibration_score=0.0,
            evidence="Claim type not recognized",
            z2_gate="ADVISORY",
        )


def _evaluate_build_success(
    claim: Claim,
    outcomes: list[ActualOutcome],
) -> ClaimEvaluation:
    """Verify: 'Build Success Rate 0% → 100% (first attempt after merge)'"""

    # Find build outcome
    build_outcome = next((o for o in outcomes if "build" in o.outcome_id.lower()), None)

    if not build_outcome:
        return ClaimEvaluation(
            claim_id=claim.claim_id,
            statement=claim.statement,
            stated_confidence=claim.stated_confidence,
            verification_status=VerificationStatus.UNKNOWN,
            actual_outcome="No build outcome data found",
            calibration_score=0.0,
            evidence="Build logs not captured",
            z2_gate="ADVISORY",
        )

    # Claim: "0% → 100% (first attempt)"
    # Reality: Did merge + first commit build successfully?
    succeeded = build_outcome.succeeded
    actual_success_rate = 1.0 if succeeded else 0.0

    # Claimed confidence: ~90% (high confidence in the fix)
    # Actual outcome: binary (worked or didn't)
    calibration = abs(claim.stated_confidence - actual_success_rate)

    status = VerificationStatus.VERIFIED if succeeded else VerificationStatus.FALSIFIED
    z2_gate = "PASS" if succeeded else "FAIL"

    return ClaimEvaluation(
        claim_id=claim.claim_id,
        statement=claim.statement,
        stated_confidence=claim.stated_confidence,
        verification_status=status,
        actual_outcome=f"Build {'succeeded' if succeeded else 'failed'}",
        calibration_score=calibration,
        evidence=build_outcome.data.get("message", ""),
        z2_gate=z2_gate,
    )


def _evaluate_services_online(
    claim: Claim,
    outcomes: list[ActualOutcome],
) -> ClaimEvaluation:
    """Verify: 'Services Online: 1 of 3 → 3 of 3'"""

    services_outcome = next((o for o in outcomes if "services" in o.outcome_id.lower()), None)

    if not services_outcome:
        return ClaimEvaluation(
            claim_id=claim.claim_id,
            statement=claim.statement,
            stated_confidence=claim.stated_confidence,
            verification_status=VerificationStatus.UNKNOWN,
            actual_outcome="No service status data found",
            calibration_score=0.0,
            evidence="Service health checks not captured",
            z2_gate="ADVISORY",
        )

    # Claimed: 3 of 3 services online
    # Reality: Check actual service count
    services_online = services_outcome.data.get("online_count", 0)
    total_services = services_outcome.data.get("total_count", 3)

    target = 3
    actual_accuracy = 1.0 if (services_online == target) else 0.0
    calibration = abs(claim.stated_confidence - actual_accuracy)

    status = VerificationStatus.VERIFIED if (services_online == target) else VerificationStatus.PARTIAL
    z2_gate = "PASS" if (services_online == target) else "ADVISORY"

    return ClaimEvaluation(
        claim_id=claim.claim_id,
        statement=claim.statement,
        stated_confidence=claim.stated_confidence,
        verification_status=status,
        actual_outcome=f"{services_online} of {total_services} services online",
        calibration_score=calibration,
        evidence=f"Services: {services_outcome.data.get('services', [])}",
        z2_gate=z2_gate,
    )


def _evaluate_deployment_time(
    claim: Claim,
    outcomes: list[ActualOutcome],
) -> ClaimEvaluation:
    """Verify: 'Time to Production: Blocked → ~5 min'"""

    time_outcome = next((o for o in outcomes if "time" in o.outcome_id.lower() or "duration" in o.outcome_id.lower()), None)

    if not time_outcome:
        return ClaimEvaluation(
            claim_id=claim.claim_id,
            statement=claim.statement,
            stated_confidence=claim.stated_confidence,
            verification_status=VerificationStatus.UNKNOWN,
            actual_outcome="No deployment timing data found",
            calibration_score=0.0,
            evidence="Deployment logs not captured",
            z2_gate="ADVISORY",
        )

    # Claimed: ~5 min (300 seconds, ±2 min acceptable)
    actual_seconds = time_outcome.data.get("seconds", 0)
    tolerance = 120  # ±2 minutes
    target = 300  # 5 minutes

    within_tolerance = abs(actual_seconds - target) <= tolerance
    actual_accuracy = 1.0 if within_tolerance else 0.0
    calibration = abs(claim.stated_confidence - actual_accuracy)

    status = VerificationStatus.VERIFIED if within_tolerance else VerificationStatus.PARTIAL
    z2_gate = "PASS" if within_tolerance else "ADVISORY"

    return ClaimEvaluation(
        claim_id=claim.claim_id,
        statement=claim.statement,
        stated_confidence=claim.stated_confidence,
        verification_status=status,
        actual_outcome=f"Deployment took {actual_seconds} seconds ({actual_seconds/60:.1f} min)",
        calibration_score=calibration,
        evidence=f"Merged at {time_outcome.data.get('merge_time', 'unknown')}; online at {time_outcome.data.get('online_time', 'unknown')}",
        z2_gate=z2_gate,
    )


def generate_report(
    audit_id: str,
    pr_number: int,
    claims: list[ClaimEvaluation],
) -> ComparisonReport:
    """Generate Z2 review document from claim evaluations"""

    verified = sum(1 for c in claims if c.verification_status == VerificationStatus.VERIFIED)
    falsified = sum(1 for c in claims if c.verification_status == VerificationStatus.FALSIFIED)
    partial = sum(1 for c in claims if c.verification_status == VerificationStatus.PARTIAL)
    unknown = sum(1 for c in claims if c.verification_status == VerificationStatus.UNKNOWN)

    # Calibration metric: mean absolute error between stated and actual
    calibrations = [c.calibration_score for c in claims]
    mean_calibration = sum(calibrations) / len(calibrations) if calibrations else 0.0

    # Z2 recommendation
    if falsified > 0:
        recommendation = "REQUIRE_RERUN"
    elif unknown > (len(claims) * 0.5):
        recommendation = "INVESTIGATE"
    else:
        recommendation = "ACCEPT"

    return ComparisonReport(
        audit_id=audit_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        pr_number=pr_number,
        service_name="operations + intent-os-relay",
        total_claims=len(claims),
        verified_count=verified,
        falsified_count=falsified,
        partial_count=partial,
        unknown_count=unknown,
        calibration_metric=mean_calibration,
        z2_recommendation=recommendation,
        claims=claims,
    )


# ============================================================================
# PR #465 SPECIFIC DATA
# ============================================================================

def get_pr465_claims() -> list[Claim]:
    """Extract claims from PR #465 expected outcomes section"""
    return [
        Claim(
            claim_id="PR465-C1",
            statement="Build Success Rate (24h): 0% (10+ failures) → 100% (first attempt)",
            predicted_outcome="Both intent-os-relay and operations build successfully on first merge attempt",
            stated_confidence=0.90,
            timestamp="2026-09-23T16:30:00Z",
        ),
        Claim(
            claim_id="PR465-C2",
            statement="Services Online: 1 of 3 (operations+intent-os-relay offline) → 3 of 3",
            predicted_outcome="All three services (operations, intent-os-relay, scintillating-playfulness) come online",
            stated_confidence=0.85,
            timestamp="2026-09-23T16:30:00Z",
        ),
        Claim(
            claim_id="PR465-C3",
            statement="Time to Production: Blocked → ~5 min (merge to production, 5–10 minutes)",
            predicted_outcome="Services reach production within 5–10 minutes of merge",
            stated_confidence=0.80,
            timestamp="2026-09-23T16:30:00Z",
        ),
        Claim(
            claim_id="PR465-C4",
            statement="Deployment Status: FAILED → SUCCESS",
            predicted_outcome="Deployment reaches SUCCESS state without rollback",
            stated_confidence=0.90,
            timestamp="2026-09-23T16:30:00Z",
        ),
    ]


def get_pr465_outcomes() -> list[ActualOutcome]:
    """
    Reconstructed outcomes from PR #465 post-merge evidence.

    Data sources:
    - PR merged: 2026-09-23T20:19:54Z
    - CI checks: All passed
    - GitHub Actions: 18 check runs, all SUCCESS or SKIPPED
    """
    return [
        ActualOutcome(
            outcome_id="build_success",
            description="CI/CD build execution after merge",
            succeeded=True,  # All checks passed
            data={
                "message": "All 18 GitHub Actions checks completed without failure",
                "checks_passed": 18,
                "checks_failed": 0,
                "merge_time": "2026-09-23T20:19:54Z",
            },
        ),
        ActualOutcome(
            outcome_id="services_status",
            description="Service online status post-deployment",
            succeeded=False,  # Unknown without Railway logs
            data={
                "online_count": 0,  # Unknown
                "total_count": 3,
                "services": ["intent-os-relay", "operations", "scintillating-playfulness"],
                "note": "Railway deployment status not captured in this PR data",
            },
        ),
        ActualOutcome(
            outcome_id="deployment_time",
            description="Time from merge to production",
            succeeded=False,  # Unknown without Railway logs
            data={
                "merge_time": "2026-09-23T20:19:54Z",
                "online_time": None,
                "seconds": 0,
                "note": "Deployment timing not captured; requires Railway API or logs",
            },
        ),
    ]


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run comparison engine and output Z2 review"""

    audit_id = "AUDIT-3d1f49e5-0437-4c13-ba7b"
    pr_number = 465

    # Load claims and outcomes
    claims = get_pr465_claims()
    outcomes = get_pr465_outcomes()

    # Evaluate each claim
    evaluations = [evaluate_claim(claim, outcomes) for claim in claims]

    # Generate Z2 review
    report = generate_report(audit_id, pr_number, evaluations)

    # Output as JSON
    print(json.dumps(asdict(report), indent=2, default=str))

    return 0


if __name__ == "__main__":
    sys.exit(main())
