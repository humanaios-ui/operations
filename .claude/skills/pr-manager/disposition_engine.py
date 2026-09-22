"""
OI-BRIDGE-01 Phase 1 — DISPOSITION Engine

Implements three-path MESSAGE → DISPOSITION logic:
- Path A: Ordinary conversation (CONTINUE_WITHIN_SCOPE, no Z2)
- Path B: Claim promotion (HOLD until Z2 RATIFY_TOKEN)
- Path C: Consequential action (HOLD until Z2 or Z3 token)
- Path D: Ambiguous/sensitive (always HUMAN_REQUIRED)
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, List
from datetime import datetime, timezone


class DispositionPath(Enum):
    """Disposition routing paths."""
    PATH_A = "ORDINARY_CONVERSATION"       # CONTINUE_WITHIN_SCOPE
    PATH_B = "CLAIM_PROMOTION"             # HOLD until Z2 RATIFY
    PATH_C = "CONSEQUENTIAL_ACTION"        # HOLD until token
    PATH_D = "AMBIGUOUS_SENSITIVE"         # Always HUMAN_REQUIRED


@dataclass
class Disposition:
    """Z2 disposition decision."""
    message_id: str
    path: DispositionPath
    decision: str  # CONTINUE_WITHIN_SCOPE, HOLD, HUMAN_REQUIRED
    reason: str
    requires_token: bool
    requires_z2_review: bool
    decided_at: Optional[str] = None
    decided_by: Optional[str] = None


class DispositionEngine:
    """Route messages through three-path DISPOSITION logic."""

    # Pre-authorized collaborators (Z1, Z3 executors, trusted nodes)
    APPROVED_COLLABORATORS = [
        "claude-z1",
        "z3_executor",
        "test-adversary",
    ]

    def __init__(self, authority_validator=None, ledger_writer=None):
        """
        Initialize DISPOSITION engine.

        Args:
            authority_validator: Token validator instance
            ledger_writer: NF_LEDGER writer instance
        """
        self.authority_validator = authority_validator
        self.ledger_writer = ledger_writer

    def route_message(self, message_id: str, sender: str, body: dict,
                     epistemic: str) -> Disposition:
        """
        Route message through three-path logic.

        Args:
            message_id: Message identifier
            sender: Sender node ID
            body: Message body (dict)
            epistemic: Epistemic standing (CLAIMED, EVIDENCE_CHECKED, REGISTERED)

        Returns:
            Disposition with path and decision
        """
        now = datetime.now(timezone.utc)

        # Detect path based on message content + epistemic standing
        path = self._detect_path(body, epistemic, sender)

        # Apply path-specific logic
        if path == DispositionPath.PATH_A:
            return self._handle_path_a(message_id, sender, body, now)
        elif path == DispositionPath.PATH_B:
            return self._handle_path_b(message_id, sender, body, now)
        elif path == DispositionPath.PATH_C:
            return self._handle_path_c(message_id, sender, body, now)
        else:  # PATH_D
            return self._handle_path_d(message_id, sender, body, now)

    def _detect_path(self, body: dict, epistemic: str, sender: str) -> DispositionPath:
        """
        Detect which disposition path message should follow.

        Returns:
            DispositionPath (A/B/C/D)
        """
        # Check for consequential action keywords
        consequential_keywords = [
            "merge", "deploy", "revoke", "publish", "release",
            "close", "archive", "delete", "execute"
        ]

        body_text = str(body).lower()
        is_consequential = any(kw in body_text for kw in consequential_keywords)

        # Check for claim registration
        is_claim = "register" in body_text or "REGISTERED" in str(body)

        # Ambiguous/sensitive triggers
        ambiguous_keywords = ["security", "permission", "scope", "authority"]
        is_ambiguous = any(kw in body_text for kw in ambiguous_keywords)

        # Path detection logic
        if is_ambiguous:
            return DispositionPath.PATH_D

        if is_consequential:
            return DispositionPath.PATH_C

        if is_claim or epistemic in ["REGISTERED", "EVIDENCE_CHECKED"]:
            return DispositionPath.PATH_B

        # Default: ordinary conversation
        return DispositionPath.PATH_A

    def _handle_path_a(self, message_id: str, sender: str, body: dict,
                      now: datetime) -> Disposition:
        """
        Path A: Ordinary Conversation (CONTINUE_WITHIN_SCOPE)

        No authority required. Pre-authorized collaboration.
        Check: sender in approved_collaborators OR sender is Z2.
        Decision: CONTINUE_WITHIN_SCOPE.

        Returns:
            Disposition with CONTINUE_WITHIN_SCOPE decision
        """
        # Check authorization
        if sender not in self.APPROVED_COLLABORATORS and sender != "night-z2":
            return Disposition(
                message_id=message_id,
                path=DispositionPath.PATH_A,
                decision="HUMAN_REQUIRED",
                reason=f"SENDER_NOT_AUTHORIZED: {sender}",
                requires_token=False,
                requires_z2_review=True,
                decided_at=now.isoformat(),
            )

        # Log to ledger
        if self.ledger_writer:
            self.ledger_writer.append_disposition(
                message_id, "CONTINUE_WITHIN_SCOPE", "bridge"
            )

        return Disposition(
            message_id=message_id,
            path=DispositionPath.PATH_A,
            decision="CONTINUE_WITHIN_SCOPE",
            reason="Ordinary pre-authorized collaboration",
            requires_token=False,
            requires_z2_review=False,
            decided_at=now.isoformat(),
            decided_by="bridge",
        )

    def _handle_path_b(self, message_id: str, sender: str, body: dict,
                      now: datetime) -> Disposition:
        """
        Path B: Claim Promotion (Z2 RATIFY_TOKEN required)

        Message claims to register finding/hypothesis.
        Authority: Z2 RATIFY_TOKEN required.
        Decision: HOLD until token, then CONTINUE.

        Returns:
            Disposition with HOLD decision
        """
        # Log to ledger
        if self.ledger_writer:
            self.ledger_writer.append_escalation(
                message_id, "CLAIM_PROMOTION_AWAITING_RATIFY", "HOLD"
            )

        return Disposition(
            message_id=message_id,
            path=DispositionPath.PATH_B,
            decision="HOLD",
            reason="Awaiting Z2 RATIFY_TOKEN for claim promotion to REGISTERED",
            requires_token=True,
            requires_z2_review=True,
            decided_at=now.isoformat(),
            decided_by="bridge",
        )

    def _handle_path_c(self, message_id: str, sender: str, body: dict,
                      now: datetime) -> Disposition:
        """
        Path C: Consequential Action (Z2 or Z3 token required)

        Message contains: "merge PR", "deploy", "revoke permission", etc.
        Authority: Z2 RATIFY_TOKEN or Z3 machine capability.
        Decision: HUMAN_REQUIRED until token obtained.

        Returns:
            Disposition with HUMAN_REQUIRED decision
        """
        # Log escalation
        if self.ledger_writer:
            self.ledger_writer.append_escalation(
                message_id, "CONSEQUENTIAL_ACTION_AWAITING_TOKEN", "HUMAN_REQUIRED"
            )

        return Disposition(
            message_id=message_id,
            path=DispositionPath.PATH_C,
            decision="HUMAN_REQUIRED",
            reason="Consequential action requires Z2 RATIFY_TOKEN or Z3 capability",
            requires_token=True,
            requires_z2_review=True,
            decided_at=now.isoformat(),
            decided_by="bridge",
        )

    def _handle_path_d(self, message_id: str, sender: str, body: dict,
                      now: datetime) -> Disposition:
        """
        Path D: Ambiguous / Sensitive (always HUMAN_REQUIRED)

        Message lacks clear scope or changes security posture.
        Authority: Z2 human judgment (not automatable by token).
        Decision: HUMAN_REQUIRED → await Z2 decision.

        Returns:
            Disposition with HUMAN_REQUIRED decision
        """
        # Log escalation
        if self.ledger_writer:
            self.ledger_writer.append_escalation(
                message_id, "AMBIGUOUS_SENSITIVE_REQUIRES_JUDGMENT", "HUMAN_REQUIRED"
            )

        return Disposition(
            message_id=message_id,
            path=DispositionPath.PATH_D,
            decision="HUMAN_REQUIRED",
            reason="Ambiguous or security-sensitive message requires Z2 human judgment",
            requires_token=False,
            requires_z2_review=True,
            decided_at=now.isoformat(),
            decided_by="bridge",
        )


if __name__ == "__main__":
    engine = DispositionEngine()

    # Test Path A: Ordinary conversation
    disp = engine.route_message(
        "msg_001",
        "claude-z1",
        {"text": "Here's my analysis of the PR"},
        "CLAIMED"
    )
    print(f"Path A: {disp.decision} ({disp.reason})")

    # Test Path B: Claim promotion
    disp = engine.route_message(
        "msg_002",
        "claude-z1",
        {"claim": "This is a new finding", "register": True},
        "CLAIMED"
    )
    print(f"Path B: {disp.decision} ({disp.reason})")

    # Test Path C: Consequential action
    disp = engine.route_message(
        "msg_003",
        "claude-z1",
        {"action": "merge PR #445"},
        "CLAIMED"
    )
    print(f"Path C: {disp.decision} ({disp.reason})")

    # Test Path D: Ambiguous/sensitive
    disp = engine.route_message(
        "msg_004",
        "claude-z1",
        {"claim": "This changes security posture"},
        "CLAIMED"
    )
    print(f"Path D: {disp.decision} ({disp.reason})")
