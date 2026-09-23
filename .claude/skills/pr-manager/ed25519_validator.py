"""OI-BRIDGE-01 — Ed25519 detached-signature validator.

Real cryptographic verification only. Format checks do not produce valid=True.
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timezone
import hashlib


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    reason: Optional[str] = None
    key_id: Optional[str] = None
    signer_id: Optional[str] = None
    verified_at: Optional[str] = None
    verification_method: str = "NONE"
    verification_strength: str = "OBSERVED"
    message_sha256: Optional[str] = None
    signature_fingerprint: Optional[str] = None


class Ed25519Validator:
    """Validate detached Ed25519 signatures against an explicit public-key registry."""

    def __init__(self, key_registry: Optional[dict] = None):
        self.key_registry = key_registry or {}

    def validate_message_signature(
        self,
        sender_node_id: str,
        message_bytes: bytes,
        signature_hex: str,
    ) -> ValidationResult:
        now = datetime.now(timezone.utc).isoformat()
        digest = hashlib.sha256(message_bytes).hexdigest()

        node = self.key_registry.get(sender_node_id)
        if not node:
            return ValidationResult(
                valid=False,
                reason=f"NODE_NOT_IN_REGISTRY:{sender_node_id}",
                signer_id=sender_node_id,
                verified_at=now,
                message_sha256=digest,
            )

        public_key_hex = str(node.get("public_key") or "").strip()
        key_id = node.get("key_id")
        if not public_key_hex or not key_id:
            return ValidationResult(
                valid=False,
                reason=f"INVALID_KEY_ENTRY:{sender_node_id}",
                signer_id=sender_node_id,
                verified_at=now,
                message_sha256=digest,
            )

        try:
            public_key_bytes = bytes.fromhex(public_key_hex)
            signature_bytes = bytes.fromhex(str(signature_hex).strip())
        except ValueError:
            return ValidationResult(
                valid=False,
                reason="INVALID_HEX_ENCODING",
                key_id=key_id,
                signer_id=sender_node_id,
                verified_at=now,
                message_sha256=digest,
            )

        if len(public_key_bytes) != 32:
            return ValidationResult(
                valid=False,
                reason=f"INVALID_PUBLIC_KEY_LENGTH:{len(public_key_bytes)}",
                key_id=key_id,
                signer_id=sender_node_id,
                verified_at=now,
                message_sha256=digest,
            )
        if len(signature_bytes) != 64:
            return ValidationResult(
                valid=False,
                reason=f"INVALID_SIGNATURE_LENGTH:{len(signature_bytes)}",
                key_id=key_id,
                signer_id=sender_node_id,
                verified_at=now,
                message_sha256=digest,
            )

        try:
            from cryptography.exceptions import InvalidSignature
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        except ImportError:
            return ValidationResult(
                valid=False,
                reason="CRYPTO_BACKEND_UNAVAILABLE",
                key_id=key_id,
                signer_id=sender_node_id,
                verified_at=now,
                message_sha256=digest,
            )

        try:
            Ed25519PublicKey.from_public_bytes(public_key_bytes).verify(
                signature_bytes, message_bytes
            )
        except InvalidSignature:
            return ValidationResult(
                valid=False,
                reason="SIGNATURE_VERIFICATION_FAILED",
                key_id=key_id,
                signer_id=sender_node_id,
                verified_at=now,
                verification_method="ED25519",
                message_sha256=digest,
                signature_fingerprint=hashlib.sha256(signature_bytes).hexdigest(),
            )
        except ValueError as exc:
            return ValidationResult(
                valid=False,
                reason=f"INVALID_PUBLIC_KEY:{exc}",
                key_id=key_id,
                signer_id=sender_node_id,
                verified_at=now,
                message_sha256=digest,
            )

        return ValidationResult(
            valid=True,
            key_id=key_id,
            signer_id=sender_node_id,
            verified_at=now,
            verification_method="ED25519",
            verification_strength="CRYPTO_VERIFIED",
            message_sha256=digest,
            signature_fingerprint=hashlib.sha256(signature_bytes).hexdigest(),
        )

    def validate_authority_token(self, token: dict) -> ValidationResult:
        """Verify a signed authority-token payload using the issuer's public key."""
        now = datetime.now(timezone.utc)
        required = ["token_id", "token_type", "issued_by", "signature", "signature_over"]
        for field in required:
            if not token.get(field):
                return ValidationResult(valid=False, reason=f"MISSING_FIELD:{field}")

        if token.get("consumed_at") is not None:
            return ValidationResult(valid=False, reason="TOKEN_ALREADY_CONSUMED")

        expires_at = token.get("expires_at")
        if expires_at:
            try:
                expiry = datetime.fromisoformat(str(expires_at).replace("Z", "+00:00"))
            except ValueError:
                return ValidationResult(valid=False, reason="INVALID_EXPIRY_FORMAT")
            if now > expiry:
                return ValidationResult(valid=False, reason="TOKEN_EXPIRED")

        return self.validate_message_signature(
            str(token["issued_by"]),
            str(token["signature_over"]).encode("utf-8"),
            str(token["signature"]),
        )
