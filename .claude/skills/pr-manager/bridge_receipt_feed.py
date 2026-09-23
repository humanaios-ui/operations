"""Bridge/Evidence Graph receipt emitter for OI-BRIDGE-01 prototypes.

This module is a producer adapter. It writes typed receipt events into an
append-only hash chain consumed by tools.verified_receipts.VerifiedReceiptResolver.

It deliberately refuses simulated/stub verification methods.
Authority effect: NONE by itself.
"""

from datetime import datetime, timezone
from typing import Optional

from tools.verified_receipts import (
    DISALLOWED_METHODS,
    STRENGTH_RANK,
    append_receipt_event,
    read_receipt_events,
)


class BridgeReceiptFeed:
    def __init__(self, ledger_path: str):
        self.ledger_path = ledger_path

    def snapshot(self):
        """Return current receipt events and head.

        The returned head is a local observation; callers must compare/pin it
        through an independent channel before treating it as a trust anchor.
        """
        return read_receipt_events(self.ledger_path)

    def consume_receipt(
        self,
        *,
        receipt_id: str,
        consumed_by: str,
        subject: str,
        at: Optional[str] = None,
    ) -> str:
        return append_receipt_event(
            self.ledger_path,
            {
                "type": "RECEIPT_CONSUMED",
                "at": at or datetime.now(timezone.utc).isoformat(),
                "by": consumed_by,
                "receipt_id": receipt_id,
                "subject": subject,
            },
        )

    def emit_verified_receipt(
        self,
        *,
        receipt_id: str,
        receipt_type: str,
        subject: str,
        action: str,
        scope: str,
        issuer: str,
        authority_scope: str,
        verification_method: str,
        verification_strength: str,
        evidence_ref: str,
        one_time: bool = False,
        at: Optional[str] = None,
    ) -> str:
        method = verification_method.upper()
        strength = verification_strength.upper()

        if not receipt_id or not evidence_ref:
            raise ValueError("receipt_id and evidence_ref are required")
        if method in DISALLOWED_METHODS or not method:
            raise ValueError(f"verification method is not eligible for VERIFIED receipt: {method}")
        if strength not in STRENGTH_RANK:
            raise ValueError(f"unknown verification strength: {strength}")

        event = {
            "type": "RECEIPT_VERIFIED",
            "at": at or datetime.now(timezone.utc).isoformat(),
            "by": "bridge-receipt-feed",
            "receipt_id": receipt_id,
            "receipt_type": receipt_type,
            "subject": subject,
            "action": action,
            "scope": scope,
            "issuer": issuer,
            "authority_scope": authority_scope,
            "verification_status": "VERIFIED",
            "verification_strength": strength,
            "verification_method": method,
            "evidence_ref": evidence_ref,
            "one_time": bool(one_time),
        }
        return append_receipt_event(self.ledger_path, event)

    def emit_harmony_gate_receipt(
        self,
        *,
        receipt_id: str,
        gate: str,
        run_id: str,
        evidence_ref: str,
        verification_method: str,
        verification_strength: str = "OBSERVED",
        issuer: str = "bridge-evidence-graph",
    ) -> str:
        return self.emit_verified_receipt(
            receipt_id=receipt_id,
            receipt_type="HARMONY_GATE",
            subject=gate,
            action="ASSERT_GATE",
            scope=f"run:{run_id}",
            issuer=issuer,
            authority_scope="NONE",
            verification_method=verification_method,
            verification_strength=verification_strength,
            evidence_ref=evidence_ref,
            one_time=False,
        )

    def emit_interrogation_approval_receipt(
        self,
        *,
        receipt_id: str,
        question_id: str,
        approved: bool,
        evidence_ref: str,
        verification_method: str,
        issuer: str = "human-z2",
    ) -> str:
        # Automatic question-state transition is an authority-bearing act.
        if verification_method.upper() != "ED25519":
            raise ValueError(
                "interrogation approval receipts require ED25519 verification "
                "for automatic APPROVED/REJECTED transition"
            )

        return self.emit_verified_receipt(
            receipt_id=receipt_id,
            receipt_type="INTERROGATION_APPROVAL",
            subject=question_id,
            action="APPROVE_QUESTION" if approved else "REJECT_QUESTION",
            scope=f"interrogation:{question_id}",
            issuer=issuer,
            authority_scope="Z2_RATIFIER",
            verification_method="ED25519",
            verification_strength="CRYPTO_VERIFIED",
            evidence_ref=evidence_ref,
            one_time=True,
        )
