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
    succeeded: Optional[bool]  # None when data not captured
    data: dict  # Raw measurement data


@dataclass
class ClaimEvaluation:
    """Evaluation of a single claim"""
    claim_id: str
    statement: str
    stated_confidence: float
    verification_status: VerificationStatus
    actual_outcome: str
    calibration_score: Optional[float]  # None when data not captured
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
    calibration_metric: Optional[float]  # Mean |stated_conf - actual_accuracy|; None if no measurable claims
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
    """Verify: 'Build Success Rate 0% → 100% (first attempt after merge)'

    PR #465 claims BOTH intent-os-relay and operations build successfully.
    We need Railway/Nixpacks evidence, not just CI gates passing.
    """

    # Find build outcomes for BOTH services
    required_services = {"intent-os-relay", "operations"}
    build_outcomes = {
        o.outcome_id: o
        for o in outcomes
        if any(svc in o.outcome_id.lower() for svc in required_services)
    }

    if not build_outcomes:
        return ClaimEvaluation(
            claim_id=claim.claim_id,
            statement=claim.statement,
            stated_confidence=claim.stated_confidence,
            verification_status=VerificationStatus.UNKNOWN,
            actual_outcome="No Railway build outcome data found for either service",
            calibration_score=None,
            evidence="Nix/Railpack build logs not captured; CI gates passing ≠ service build success",
            z2_gate="ADVISORY",
        )

    # Claim: "Both services build on first attempt"
    # Reality: Check both intent-os-relay AND operations
    # If any outcome is None (unverified), return UNKNOWN
    if any(o.succeeded is None for o in build_outcomes.values()):
        return ClaimEvaluation(
            claim_id=claim.claim_id,
            statement=claim.statement,
            stated_confidence=claim.stated_confidence,
            verification_status=VerificationStatus.UNKNOWN,
            actual_outcome="Build status unknown (data not captured for one or more services)",
            calibration_score=None,
            evidence="Railway/Nixpacks build logs not accessible",
            z2_gate="ADVISORY",
        )

    all_succeeded = all(o.succeeded for o in build_outcomes.values())
    actual_success_rate = 1.0 if all_succeeded else 0.0

    calibration = abs(claim.stated_confidence - actual_success_rate) if build_outcomes else None

    status = VerificationStatus.VERIFIED if all_succeeded else VerificationStatus.FALSIFIED
    z2_gate = "PASS" if all_succeeded else "FAIL"

    services_status = ", ".join(
        f"{svc.split('-')[0]}: {'✅' if outcome.succeeded else '❌'}"
        for svc, outcome in build_outcomes.items()
    )

    return ClaimEvaluation(
        claim_id=claim.claim_id,
        statement=claim.statement,
        stated_confidence=claim.stated_confidence,
        verification_status=status,
        actual_outcome=f"Build status: {services_status}",
        calibration_score=calibration,
        evidence=f"Checked {len(build_outcomes)} service(s); all succeeded: {all_succeeded}",
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
    services_online = services_outcome.data.get("online_count")
    total_services = services_outcome.data.get("total_count", 3)

    # If online_count is None, data not captured
    if services_online is None:
        return ClaimEvaluation(
            claim_id=claim.claim_id,
            statement=claim.statement,
            stated_confidence=claim.stated_confidence,
            verification_status=VerificationStatus.UNKNOWN,
            actual_outcome="Service online count not captured",
            calibration_score=None,
            evidence="Railway deployment status not captured",
            z2_gate="ADVISORY",
        )

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
    actual_seconds = time_outcome.data.get("seconds")

    if actual_seconds is None:
        return ClaimEvaluation(
            claim_id=claim.claim_id,
            statement=claim.statement,
            stated_confidence=claim.stated_confidence,
            verification_status=VerificationStatus.UNKNOWN,
            actual_outcome="Deployment timing data not captured",
            calibration_score=None,
            evidence="Online timestamp missing; cannot calculate deployment time",
            z2_gate="ADVISORY",
        )

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

    # Calibration metric: mean absolute error (only measured/verified claims)
    # Exclude UNKNOWN outcomes and None scores (unverifiable claims don't contribute)
    measurable_calibrations = [
        c.calibration_score for c in claims
        if c.calibration_score is not None
        and c.verification_status != VerificationStatus.UNKNOWN
    ]
    mean_calibration = (
        sum(measurable_calibrations) / len(measurable_calibrations)
        if measurable_calibrations else None
    )

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

    CRITICAL GAP: We have CI gate evidence (GitHub Actions), NOT Railway/Nix build evidence.
    CI gates passing does NOT prove services built successfully.

    Data sources:
    - PR merged: 2026-09-23T20:19:54Z
    - CI checks: All 18 passed (quality/security/governance gates only)
    - Railway builds: NOT CAPTURED (this is the data gap)
    - Service health: NOT CAPTURED
    """
    return [
        ActualOutcome(
            outcome_id="ci_gates_passed",
            description="GitHub Actions CI gates (not Railway builds)",
            succeeded=True,  # All checks passed
            data={
                "message": "All 18 GitHub Actions checks completed",
                "note": "CI gates ≠ Railway service builds. Need Nix/Railpack logs.",
                "checks_passed": 18,
                "checks_failed": 0,
                "merge_time": "2026-09-23T20:19:54Z",
            },
        ),
        ActualOutcome(
            outcome_id="intent-os-relay_build",
            description="intent-os-relay Railway build status",
            succeeded=None,  # UNKNOWN - not captured
            data={
                "service": "intent-os-relay",
                "status": "UNKNOWN",
                "note": "Railpack build logs not accessible",
            },
        ),
        ActualOutcome(
            outcome_id="operations_build",
            description="operations Railway build status",
            succeeded=None,  # UNKNOWN - not captured
            data={
                "service": "operations",
                "status": "UNKNOWN",
                "note": "Nixpacks build logs not accessible",
            },
        ),
        ActualOutcome(
            outcome_id="services_status",
            description="Service online status post-deployment",
            succeeded=None,  # Unknown without Railway logs
            data={
                "online_count": None,
                "total_count": 3,
                "services": ["intent-os-relay", "operations", "scintillating-playfulness"],
                "note": "Railway deployment status not captured",
            },
        ),
        ActualOutcome(
            outcome_id="deployment_time",
            description="Time from merge to production",
            succeeded=None,  # Unknown without Railway logs
            data={
                "merge_time": "2026-09-23T20:19:54Z",
                "online_time": None,
                "seconds": None,
                "note": "Deployment timing not captured",
            },
        ),
    ]


# ============================================================================
# MARKDOWN RENDERING
# ============================================================================

def render_markdown_report(report: ComparisonReport) -> str:
    """Render ComparisonReport as markdown (Z2 review format)"""
    lines = [
        "# Z2 Review: PR #465 Decision Log vs. Deployment Outcomes",
        f"**Generated by Comparison Engine v1.0**",
        f"**Audit ID:** {report.audit_id}",
        f"**Date:** {report.timestamp}",
        "",
        "## Executive Summary",
        "",
        f"| Metric | Result |",
        f"|--------|--------|",
        f"| Claims Verified | {report.verified_count} of {report.total_claims} |",
        f"| Claims Falsified | {report.falsified_count} of {report.total_claims} |",
        f"| Claims Partial | {report.partial_count} of {report.total_claims} |",
        f"| Claims Unknown | {report.unknown_count} of {report.total_claims} |",
        f"| Calibration (MAE) | {report.calibration_metric:.2f if report.calibration_metric is not None else 'N/A'} |",
        f"| **Z2 Recommendation** | **{report.z2_recommendation}** |",
        "",
        "## Detailed Claim Analysis",
        "",
    ]

    for claim in report.claims:
        status_icon = "✅" if claim.verification_status == VerificationStatus.VERIFIED else \
                      "❌" if claim.verification_status == VerificationStatus.FALSIFIED else \
                      "⚠️" if claim.verification_status == VerificationStatus.PARTIAL else "❓"

        lines.extend([
            f"### {status_icon} {claim.claim_id}: {claim.verification_status.value}",
            "",
            f"**Statement:** {claim.statement}",
            f"**Stated Confidence:** {claim.stated_confidence:.0%}",
            f"**Actual Outcome:** {claim.actual_outcome}",
            f"**Calibration Score:** {claim.calibration_score:.2f if claim.calibration_score is not None else 'N/A'}",
            f"**Evidence:** {claim.evidence}",
            f"**Z2 Gate:** {claim.z2_gate}",
            "",
        ])

    return "\n".join(lines)


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

    # Also generate markdown report (for reproducibility)
    markdown = render_markdown_report(report)
    with open("Z2_REVIEW_PR465_COMPARISON.md", "w") as f:
        f.write(markdown)

    return 0


if __name__ == "__main__":
    sys.exit(main())
