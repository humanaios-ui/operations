"""Typed verified-receipt producer for OI-BRIDGE-01.

Authority effect: NONE by itself. Automatic authority-bearing receipts require
an already-valid cryptographic verifier result bound to the exact payload.
"""

from datetime import datetime, timezone
from typing import Optional
import hashlib

from ed25519_validator import ValidationResult
from tools.verified_receipts import (
    ALLOWED_VERIFICATION_METHODS,
    STRENGTH_RANK,
    ReceiptRequirement,
    append_receipt_event,
    canonical_verification_method,
    consume_receipt_atomic,
)


def canonical_interrogation_approval_payload(
    question_id: str,
    approved: bool,
    issuer: str = "human-z2",
) -> bytes:
    action = "APPROVE_QUESTION" if approved else "REJECT_QUESTION"
    return (
        f"INTERROGATION_APPROVAL|{question_id}|{action}|"
        f"{issuer}|Z2_RATIFIER"
    ).encode("utf-8")


class BridgeReceiptFeed:
    def __init__(self, ledger_path: str):
        self.ledger_path = ledger_path

    def consume_receipt(
        self,
        *,
        receipt_id: str,
        requirement: ReceiptRequirement,
        expected_head_hash: str,
        consumed_by: str,
        subject: str,
    ) -> str:
        return consume_receipt_atomic(
            self.ledger_path,
            receipt_id=receipt_id,
            requirement=requirement,
            expected_head_hash=expected_head_hash,
            consumed_by=consumed_by,
            subject=subject,
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
        method = canonical_verification_method(verification_method)
        strength = str(verification_strength or "").strip().upper()

        if not receipt_id or not evidence_ref:
            raise ValueError("receipt_id and evidence_ref are required")
        if method not in ALLOWED_VERIFICATION_METHODS:
            raise ValueError(f"unsupported verification method: {method or 'EMPTY'}")
        if strength not in STRENGTH_RANK:
            raise ValueError(f"unknown verification strength: {strength}")

        return append_receipt_event(
            self.ledger_path,
            {
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
            },
        )

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
        verification_result: ValidationResult,
        issuer: str = "human-z2",
    ) -> str:
        payload = canonical_interrogation_approval_payload(
            question_id, approved, issuer
        )
        expected_digest = hashlib.sha256(payload).hexdigest()

        if not verification_result.valid:
            raise ValueError("cryptographic verification did not pass")
        if verification_result.verification_method != "ED25519":
            raise ValueError("approval proof must come from Ed25519 verifier")
        if verification_result.verification_strength != "CRYPTO_VERIFIED":
            raise ValueError("approval proof is not CRYPTO_VERIFIED")
        if verification_result.signer_id != issuer:
            raise ValueError("approval proof signer does not match issuer")
        if verification_result.message_sha256 != expected_digest:
            raise ValueError("approval proof is not bound to this question/decision")
        if not verification_result.key_id or not verification_result.signature_fingerprint:
            raise ValueError("approval proof lacks key/fingerprint provenance")

        action = "APPROVE_QUESTION" if approved else "REJECT_QUESTION"
        evidence_ref = (
            f"ed25519:{verification_result.key_id}:"
            f"{verification_result.signature_fingerprint}"
        )
        return self.emit_verified_receipt(
            receipt_id=receipt_id,
            receipt_type="INTERROGATION_APPROVAL",
            subject=question_id,
            action=action,
            scope=f"interrogation:{question_id}",
            issuer=issuer,
            authority_scope="Z2_RATIFIER",
            verification_method="ED25519",
            verification_strength="CRYPTO_VERIFIED",
            evidence_ref=evidence_ref,
            one_time=True,
        )
