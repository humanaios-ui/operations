"""
OI-BRIDGE-01 Phase 1 — Delivery State Machine

Implements MESSAGE → DELIVERY → RESPONSE → CHALLENGE → EVIDENCE → DISPOSITION flow.
Tracks state transitions and timeout windows.
"""

from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional
from datetime import datetime, timezone, timedelta


class DeliveryState(Enum):
    """Delivery phase states."""
    MESSAGE = "MESSAGE"          # Received
    DELIVERY = "DELIVERY"        # Validated (signature + envelope parsing)
    RESPONSE = "RESPONSE"        # Node replied (or bridge escalated)
    CHALLENGE = "CHALLENGE"      # Other node challenged claim
    EVIDENCE = "EVIDENCE"        # Evidence provided
    DISPOSITION = "DISPOSITION"  # Z2 made decision
    CONTINUE = "CONTINUE"        # Node proceeding with token
    HUMAN_REQUIRED = "HUMAN_REQUIRED"  # Awaiting human (Z2)


@dataclass
class DeliveryRecord:
    """Record of message delivery through state machine."""
    message_id: str
    current_state: DeliveryState
    entered_at: str  # ISO8601 UTC timestamp
    timeout_at: Optional[str]  # ISO8601 UTC timestamp (48h default)
    signature_valid: bool
    signature_key_id: Optional[str]
    escalation_reason: Optional[str]
    disposition: Optional[str]  # CONTINUE, HUMAN_REQUIRED, HOLD


class DeliveryStateMachine:
    """Manages message delivery state transitions."""

    DELIVERY_TIMEOUT_HOURS = 48

    def __init__(self):
        """Initialize state machine."""
        self.records: dict[str, DeliveryRecord] = {}

    def receive_message(self, message_id: str) -> DeliveryRecord:
        """
        Create new delivery record (MESSAGE state).

        Args:
            message_id: Unique message identifier

        Returns:
            DeliveryRecord in MESSAGE state
        """
        now = datetime.now(timezone.utc)
        timeout = now + timedelta(hours=self.DELIVERY_TIMEOUT_HOURS)

        record = DeliveryRecord(
            message_id=message_id,
            current_state=DeliveryState.MESSAGE,
            entered_at=now.isoformat(),
            timeout_at=timeout.isoformat(),
            signature_valid=False,
            signature_key_id=None,
            escalation_reason=None,
            disposition=None,
        )

        self.records[message_id] = record
        return record

    def mark_delivery_success(self, message_id: str, key_id: str) -> DeliveryRecord:
        """
        Transition MESSAGE → DELIVERY (signature validation passed).

        Args:
            message_id: Message identifier
            key_id: Public key ID used for validation

        Returns:
            Updated DeliveryRecord
        """
        record = self.records.get(message_id)
        if not record:
            raise ValueError(f"Message not found: {message_id}")

        now = datetime.now(timezone.utc)
        record.current_state = DeliveryState.DELIVERY
        record.signature_valid = True
        record.signature_key_id = key_id
        record.entered_at = now.isoformat()

        return record

    def mark_delivery_failure(self, message_id: str, reason: str) -> DeliveryRecord:
        """
        Transition MESSAGE → HUMAN_REQUIRED (signature validation failed).

        Args:
            message_id: Message identifier
            reason: Failure reason (SIGNATURE_INVALID, PARSE_ERROR, etc.)

        Returns:
            Updated DeliveryRecord
        """
        record = self.records.get(message_id)
        if not record:
            raise ValueError(f"Message not found: {message_id}")

        now = datetime.now(timezone.utc)
        record.current_state = DeliveryState.HUMAN_REQUIRED
        record.escalation_reason = reason
        record.entered_at = now.isoformat()

        return record

    def mark_response_received(self, message_id: str) -> DeliveryRecord:
        """
        Transition DELIVERY → RESPONSE (node replied).

        Args:
            message_id: Message identifier

        Returns:
            Updated DeliveryRecord
        """
        record = self.records.get(message_id)
        if not record:
            raise ValueError(f"Message not found: {message_id}")

        if record.current_state != DeliveryState.DELIVERY:
            raise ValueError(f"Cannot transition {record.current_state} → RESPONSE")

        now = datetime.now(timezone.utc)
        record.current_state = DeliveryState.RESPONSE
        record.entered_at = now.isoformat()

        return record

    def mark_challenge_received(self, message_id: str) -> DeliveryRecord:
        """
        Transition RESPONSE → CHALLENGE (other node contested).

        Args:
            message_id: Message identifier

        Returns:
            Updated DeliveryRecord
        """
        record = self.records.get(message_id)
        if not record:
            raise ValueError(f"Message not found: {message_id}")

        now = datetime.now(timezone.utc)
        record.current_state = DeliveryState.CHALLENGE
        record.entered_at = now.isoformat()

        return record

    def mark_evidence_provided(self, message_id: str) -> DeliveryRecord:
        """
        Transition CHALLENGE → EVIDENCE (evidence references provided).

        Args:
            message_id: Message identifier

        Returns:
            Updated DeliveryRecord
        """
        record = self.records.get(message_id)
        if not record:
            raise ValueError(f"Message not found: {message_id}")

        now = datetime.now(timezone.utc)
        record.current_state = DeliveryState.EVIDENCE
        record.entered_at = now.isoformat()

        return record

    def mark_disposition_awaiting(self, message_id: str) -> DeliveryRecord:
        """
        Transition EVIDENCE → DISPOSITION (awaiting Z2 decision).

        Args:
            message_id: Message identifier

        Returns:
            Updated DeliveryRecord
        """
        record = self.records.get(message_id)
        if not record:
            raise ValueError(f"Message not found: {message_id}")

        now = datetime.now(timezone.utc)
        record.current_state = DeliveryState.DISPOSITION
        record.entered_at = now.isoformat()

        return record

    def mark_disposition_continue(self, message_id: str,
                                 disposition: str = "CONTINUE_WITHIN_SCOPE") -> DeliveryRecord:
        """
        Transition DISPOSITION → CONTINUE (Z2 approved, node may proceed).

        Args:
            message_id: Message identifier
            disposition: Type (CONTINUE_WITHIN_SCOPE, CONTINUE_WITH_TOKEN)

        Returns:
            Updated DeliveryRecord
        """
        record = self.records.get(message_id)
        if not record:
            raise ValueError(f"Message not found: {message_id}")

        now = datetime.now(timezone.utc)
        record.current_state = DeliveryState.CONTINUE
        record.disposition = disposition
        record.entered_at = now.isoformat()

        return record

    def mark_disposition_hold(self, message_id: str) -> DeliveryRecord:
        """
        Transition DISPOSITION → HUMAN_REQUIRED (awaiting Z2 token or decision).

        Args:
            message_id: Message identifier

        Returns:
            Updated DeliveryRecord
        """
        record = self.records.get(message_id)
        if not record:
            raise ValueError(f"Message not found: {message_id}")

        now = datetime.now(timezone.utc)
        record.current_state = DeliveryState.HUMAN_REQUIRED
        record.disposition = "HOLD"
        record.entered_at = now.isoformat()

        return record

    def check_timeout(self, message_id: str) -> bool:
        """
        Check if message has exceeded timeout window.

        Args:
            message_id: Message identifier

        Returns:
            True if timeout exceeded
        """
        record = self.records.get(message_id)
        if not record or not record.timeout_at:
            return False

        timeout = datetime.fromisoformat(record.timeout_at)
        now = datetime.now(timezone.utc)

        return now > timeout

    def get_record(self, message_id: str) -> Optional[DeliveryRecord]:
        """Retrieve delivery record by message ID."""
        return self.records.get(message_id)


if __name__ == "__main__":
    sm = DeliveryStateMachine()

    # Simulate message flow
    record = sm.receive_message("msg_001")
    print(f"Received: {record.current_state}")

    record = sm.mark_delivery_success("msg_001", "z1_pub_key_2026_09_22")
    print(f"Delivery OK: {record.current_state}, signed by {record.signature_key_id}")

    record = sm.mark_response_received("msg_001")
    print(f"Response: {record.current_state}")

    record = sm.mark_disposition_continue("msg_001")
    print(f"Final: {record.current_state}, disposition: {record.disposition}")
