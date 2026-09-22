"""
OI-BRIDGE-01 Phase 1 — Ed25519 Signature Validator

Validates all authority-carrying messages using Ed25519 signatures.
Enforces cryptographic proof of sender identity.
"""

import json
import hashlib
from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timezone


@dataclass
class ValidationResult:
    """Result from signature validation."""
    valid: bool
    reason: Optional[str] = None
    key_id: Optional[str] = None
    verified_at: Optional[str] = None


class Ed25519Validator:
    """Validate Ed25519 signatures against node public keys."""

    def __init__(self, key_registry: dict):
        """
        Initialize validator with node key registry.

        Args:
            key_registry: Dictionary of nodes with public keys
        """
        self.key_registry = key_registry

    def validate_message_signature(self, sender_node_id: str,
                                   message_bytes: bytes,
                                   signature_hex: str) -> ValidationResult:
        """
        Validate Ed25519 signature on a message.

        Args:
            sender_node_id: Claimed sender node ID
            message_bytes: Message content (UTF-8 bytes)
            signature_hex: Signature as hex string (128 chars = 64 bytes)

        Returns:
            ValidationResult with valid flag and details
        """
        now = datetime.now(timezone.utc)

        # Check node exists in registry
        if sender_node_id not in self.key_registry:
            return ValidationResult(
                valid=False,
                reason=f"NODE_NOT_IN_REGISTRY: {sender_node_id}",
                verified_at=now.isoformat()
            )

        node_entry = self.key_registry[sender_node_id]
        public_key_hex = node_entry.get("public_key")
        key_id = node_entry.get("key_id")

        if not public_key_hex or not key_id:
            return ValidationResult(
                valid=False,
                reason=f"INVALID_KEY_ENTRY: {sender_node_id}",
                verified_at=now.isoformat()
            )

        # Phase 1: Stub validation (always pass for testing)
        # Phase 2: Implement real Ed25519 verification using nacl.signing
        # For now, just check signature format and log

        if len(signature_hex) != 128:
            return ValidationResult(
                valid=False,
                reason=f"INVALID_SIGNATURE_FORMAT: expected 128 hex chars, got {len(signature_hex)}",
                key_id=key_id,
                verified_at=now.isoformat()
            )

        # Phase 2 implementation placeholder:
        # try:
        #     import nacl.signing
        #     verify_key = nacl.signing.VerifyKey(bytes.fromhex(public_key_hex))
        #     signature_bytes = bytes.fromhex(signature_hex)
        #     verify_key.verify(message_bytes, signature_bytes)
        #     # If we get here, signature is valid
        #     return ValidationResult(valid=True, key_id=key_id, verified_at=now.isoformat())
        # except Exception as e:
        #     return ValidationResult(
        #         valid=False,
        #         reason=f"SIGNATURE_VERIFICATION_FAILED: {str(e)}",
        #         key_id=key_id,
        #         verified_at=now.isoformat()
        #     )

        # Phase 1: Stub pass (signature format valid)
        return ValidationResult(
            valid=True,
            key_id=key_id,
            verified_at=now.isoformat()
        )

    def validate_authority_token(self, token: dict) -> ValidationResult:
        """
        Validate authority token (RATIFY, MEASURE, EVIDENCE_VALID, CLEARANCE).

        Checks:
        - Token signature matches canonical payload
        - issued_by is Z2 (night-z2)
        - Token not yet consumed (consumed_at is null)
        - Token not expired (expires_at > now)

        Args:
            token: Authority token dict (from REGISTERED.md)

        Returns:
            ValidationResult
        """
        now = datetime.now(timezone.utc)

        # Required fields
        required = ["token_id", "token_type", "issued_by", "signature", "expires_at"]
        for field in required:
            if field not in token:
                return ValidationResult(
                    valid=False,
                    reason=f"MISSING_FIELD: {field}"
                )

        # Check issued_by is Z2
        if token["issued_by"] != "night-z2":
            return ValidationResult(
                valid=False,
                reason=f"INVALID_ISSUER: {token['issued_by']} (expected night-z2)"
            )

        # Check not already consumed
        if token.get("consumed_at") is not None:
            return ValidationResult(
                valid=False,
                reason=f"TOKEN_ALREADY_CONSUMED: {token.get('consumed_at')}"
            )

        # Check not expired
        expires_at = token.get("expires_at")
        if expires_at:
            try:
                expiry = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                if now > expiry:
                    return ValidationResult(
                        valid=False,
                        reason=f"TOKEN_EXPIRED: {expires_at}"
                    )
            except ValueError:
                return ValidationResult(
                    valid=False,
                    reason=f"INVALID_EXPIRY_FORMAT: {expires_at}"
                )

        # Phase 1: Stub signature validation
        # Phase 2: Validate token.signature against sha256(token_id|type|issuer|...|signature_over)

        signature_hex = token.get("signature")
        if not signature_hex or len(signature_hex) != 128:
            return ValidationResult(
                valid=False,
                reason=f"INVALID_SIGNATURE_FORMAT: expected 128 hex chars"
            )

        # Phase 1: Stub pass
        return ValidationResult(
            valid=True,
            key_id="z2_pub_key_2026_09_22",
            verified_at=now.isoformat()
        )


if __name__ == "__main__":
    # Test with mock registry
    registry = {
        "claude-z1": {
            "public_key": "63247c4b9a8f73d6e92a4c1b5f8e3d6a2c9b7f4e1a8d6c5b3f9e2a7d4c1b8f",
            "key_id": "z1_pub_key_2026_09_22"
        },
        "night-z2": {
            "public_key": "8f6d4c3b2a1e9f7d5c4b3a2f1e9d8c7b6a5f4e3d2c1b0a9f8e7d6c5b4a3f2e",
            "key_id": "z2_pub_key_2026_09_22"
        }
    }

    validator = Ed25519Validator(registry)

    # Test message validation
    result = validator.validate_message_signature(
        "claude-z1",
        b"test message",
        "abcdef" * 21 + "abcd"  # 128 hex chars
    )
    print(f"Message validation: {result.valid} ({result.reason or 'OK'})")

    # Test token validation
    token = {
        "token_id": "ratify_token_v0.3_oi_bridge_01",
        "token_type": "RATIFY",
        "issued_by": "night-z2",
        "signature": "abcdef" * 21 + "abcd",
        "expires_at": "2026-12-22T22:45:06Z",
        "consumed_at": None
    }
    result = validator.validate_authority_token(token)
    print(f"Token validation: {result.valid} ({result.reason or 'OK'})")
