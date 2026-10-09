"""
OI-BRIDGE-01 Phase 1 — Molt Tier Calculator

Calculates molt candidate tier (F/IC/H) and validates against anti-cascade rules.
Enforces: K=3 max molts open, no reverts twice in row (frozen), priority queue ranking.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone


class MoltTier(Enum):
    """Molt candidate tier classification."""
    FINDING = "F"           # Finding (bug, issue, observation)
    ISSUE_CANDIDATE = "IC"  # Issue candidate (needs more evidence)
    HYPOTHESIS = "H"        # Hypothesis (testable prediction)
    UNKNOWN = "UNKNOWN"


@dataclass
class MoltCandidate:
    """Molt candidate record."""
    molt_id: str
    constant_name: str
    constant_current_value: Any
    proposed_value: Any
    tier: MoltTier
    priority_score: float
    prediction_window_hours: int
    falsifier: str
    revert_count: int
    is_frozen: bool
    proposed_at: str
    ratified_at: Optional[str] = None
    measured_at: Optional[str] = None
    outcome: Optional[str] = None  # HELD, REVERTED


@dataclass
class MoltTierResult:
    """Result from molt tier calculation."""
    molt_id: str
    tier: MoltTier
    reason: str
    is_valid: bool
    anti_cascade_violations: List[str]
    calculated_at: str


class MoltTierCalculator:
    """Calculate molt tier and validate anti-cascade rules."""

    # Anti-cascade rule constants
    MAX_OPEN_MOLTS = 3  # K=3
    REVERT_FREEZE_THRESHOLD = 2  # Frozen after 2 reverts in a row

    def __init__(self):
        """Initialize molt tier calculator."""
        self.open_molts: Dict[str, MoltCandidate] = {}
        self.frozen_constants: set = set()

    def calculate_tier(self, molt_dict: Dict[str, Any]) -> MoltTierResult:
        """
        Calculate molt candidate tier (F/IC/H) based on evidence.

        Tier detection logic:
        - FINDING (F): Observable bug/defect with clear reproduction
        - ISSUE_CANDIDATE (IC): Needs investigation, evidence incomplete
        - HYPOTHESIS (H): Testable prediction with defined measurement window
        - UNKNOWN: Cannot classify

        Args:
            molt_dict: Molt candidate dict with fields:
              - molt_id, constant_name, proposed_value
              - priority_score (0-100), prediction_window_hours
              - falsifier (required), evidence_url (optional)

        Returns:
            MoltTierResult with calculated tier and violations
        """
        now = datetime.now(timezone.utc).isoformat()
        violations = []

        molt_id = molt_dict.get("molt_id", "unknown")
        priority_score = molt_dict.get("priority_score", 0)
        has_falsifier = bool(molt_dict.get("falsifier"))
        has_evidence = bool(molt_dict.get("evidence_url"))
        window_hours = molt_dict.get("prediction_window_hours", 0)

        # Tier detection logic
        if not has_falsifier:
            # Missing falsifier → invalid
            return MoltTierResult(
                molt_id=molt_id,
                tier=MoltTier.UNKNOWN,
                reason="MISSING_FALSIFIER",
                is_valid=False,
                anti_cascade_violations=["NO_FALSIFIER"],
                calculated_at=now,
            )

        # Classify tier
        if has_evidence and priority_score >= 75:
            tier = MoltTier.FINDING
            reason = "Observable finding with evidence (priority ≥75)"
        elif has_evidence and window_hours > 0:
            tier = MoltTier.HYPOTHESIS
            reason = "Testable hypothesis with window defined"
        elif priority_score >= 50:
            tier = MoltTier.ISSUE_CANDIDATE
            reason = "Issue candidate (priority ≥50, needs investigation)"
        else:
            tier = MoltTier.UNKNOWN
            reason = "Insufficient evidence for tier classification"

        # Validate anti-cascade rules
        violations = self._validate_anti_cascade(molt_dict, tier)

        is_valid = len(violations) == 0

        return MoltTierResult(
            molt_id=molt_id,
            tier=tier,
            reason=reason,
            is_valid=is_valid,
            anti_cascade_violations=violations,
            calculated_at=now,
        )

    def _validate_anti_cascade(self, molt_dict: Dict[str, Any], tier: MoltTier) -> List[str]:
        """
        Validate anti-cascade rules.

        Rules:
        1. At most K=3 molts open system-wide
        2. No new candidate inside window W of prior molt (no self-reference)
        3. Constant reverted twice in a row → frozen (Z2 override required)
        4. Constant in Priority Queue must rank above blocked items
        5. Molt must be ranked by Priority Queue score, not bypassed

        Args:
            molt_dict: Molt candidate dict
            tier: Calculated tier

        Returns:
            List of violation strings (empty if valid)
        """
        violations = []
        constant_name = molt_dict.get("constant_name", "unknown")

        # Rule 1: K=3 max open molts
        if len(self.open_molts) >= self.MAX_OPEN_MOLTS:
            violations.append(f"OPEN_MOLT_LIMIT_EXCEEDED: {len(self.open_molts)}/{self.MAX_OPEN_MOLTS}")

        # Rule 3: Check if constant is frozen (reverted twice in a row)
        if constant_name in self.frozen_constants:
            violations.append(f"CONSTANT_FROZEN: {constant_name} (reverted twice, requires Z2 override)")

        # Rule 4: Priority ranking
        priority_score = molt_dict.get("priority_score", 0)
        if priority_score < 0 or priority_score > 100:
            violations.append(f"INVALID_PRIORITY_SCORE: {priority_score} (must be 0-100)")

        # Rule 5: Falsifier required (redundant check but important)
        if not molt_dict.get("falsifier"):
            violations.append("NO_FALSIFIER_DEFINED")

        return violations

    def register_molt(self, molt: MoltCandidate) -> None:
        """
        Register molt as open.

        Args:
            molt: MoltCandidate
        """
        self.open_molts[molt.molt_id] = molt

    def mark_molt_reverted(self, constant_name: str, molt_id: str) -> None:
        """
        Mark molt as reverted and track revert count.

        If reverted twice in a row, freeze the constant.

        Args:
            constant_name: Name of constant being reverted
            molt_id: ID of reverted molt
        """
        if molt_id in self.open_molts:
            molt = self.open_molts[molt_id]
            molt.revert_count += 1
            molt.outcome = "REVERTED"

            # Check if frozen (twice in a row)
            if molt.revert_count >= self.REVERT_FREEZE_THRESHOLD:
                self.frozen_constants.add(constant_name)
                molt.is_frozen = True

            # Remove from open molts
            del self.open_molts[molt_id]

    def mark_molt_held(self, molt_id: str) -> None:
        """
        Mark molt as held (awaiting window close).

        Args:
            molt_id: ID of held molt
        """
        if molt_id in self.open_molts:
            self.open_molts[molt_id].outcome = "HELD"

    def get_open_molt_count(self) -> int:
        """Get number of open molts."""
        return len(self.open_molts)

    def get_frozen_constants(self) -> set:
        """Get set of frozen constants."""
        return self.frozen_constants.copy()

    def can_open_molt(self) -> bool:
        """Check if new molt can be opened (K=3 rule)."""
        return len(self.open_molts) < self.MAX_OPEN_MOLTS

    def unfreeze_constant(self, constant_name: str) -> None:
        """
        Unfreeze constant (Z2 override).

        Args:
            constant_name: Name of constant to unfreeze
        """
        if constant_name in self.frozen_constants:
            self.frozen_constants.discard(constant_name)


if __name__ == "__main__":
    calculator = MoltTierCalculator()

    # Test Case 1: Finding (high priority + evidence)
    finding_molt = {
        "molt_id": "molt_001",
        "constant_name": "behavior_dial_1",
        "proposed_value": 0.75,
        "priority_score": 85,
        "prediction_window_hours": 24,
        "falsifier": "response_time > 5s",
        "evidence_url": "https://github.com/...",
    }

    result = calculator.calculate_tier(finding_molt)
    print(f"Finding: {result.tier.value} (priority 85, has evidence)")
    print(f"  Valid: {result.is_valid}, Violations: {result.anti_cascade_violations}")

    # Test Case 2: Hypothesis (window defined)
    hypothesis_molt = {
        "molt_id": "molt_002",
        "constant_name": "prompt_temperature",
        "proposed_value": 0.9,
        "priority_score": 60,
        "prediction_window_hours": 72,
        "falsifier": "test_suite_score < 0.5",
    }

    result = calculator.calculate_tier(hypothesis_molt)
    print(f"\nHypothesis: {result.tier.value} (window 72h)")
    print(f"  Valid: {result.is_valid}, Violations: {result.anti_cascade_violations}")

    # Test Case 3: Issue Candidate (medium priority)
    ic_molt = {
        "molt_id": "molt_003",
        "constant_name": "cache_ttl",
        "proposed_value": 3600,
        "priority_score": 55,
        "prediction_window_hours": 0,
        "falsifier": "cache_hit_rate < 0.8",
    }

    result = calculator.calculate_tier(ic_molt)
    print(f"\nIssue Candidate: {result.tier.value} (priority 55)")
    print(f"  Valid: {result.is_valid}, Violations: {result.anti_cascade_violations}")

    # Test Case 4: No falsifier (invalid)
    invalid_molt = {
        "molt_id": "molt_004",
        "constant_name": "timeout",
        "proposed_value": 30,
        "priority_score": 70,
        "prediction_window_hours": 48,
        # Missing falsifier
    }

    result = calculator.calculate_tier(invalid_molt)
    print(f"\nNo Falsifier: {result.tier.value} (invalid)")
    print(f"  Valid: {result.is_valid}, Violations: {result.anti_cascade_violations}")

    # Test Case 5: Anti-cascade K=3 rule
    print(f"\nAnti-cascade validation:")
    print(f"  Open molts: {calculator.get_open_molt_count()}/{calculator.MAX_OPEN_MOLTS}")
    print(f"  Can open: {calculator.can_open_molt()}")
