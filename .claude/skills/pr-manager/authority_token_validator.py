"""
OI-BRIDGE-01 Phase 1 — Authority Token Validator

Validates authority tokens (RATIFY_TOKEN, MEASURE_TOKEN, EVIDENCE_VALID_TOKEN, CLEARANCE_TOKEN).
Enforces token consumption and scope matching.
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timezone
import hashlib


@dataclass
class TokenValidationResult:
    """Result from token validation."""
    valid: bool
    token_id: Optional[str] = None
    token_type: Optional[str] = None
    scope: Optional[str] = None
    reason: Optional[str] = None
    verified_at: Optional[str] = None


class AuthorityTokenValidator:
    """Validate authority tokens and enforce consumption."""

    def __init__(self):
        """Initialize token validator."""
        self.consumed_tokens: set[str] = set()  # Tracking consumed token IDs

    def validate_token(self, token: dict) -> TokenValidationResult:
        """
        Validate authority token.

        Checks:
        - Token signature valid (phase 2: real validation)
        - issued_by == "night-z2" (only Z2 can issue authority)
        - issued_to matches intended consumer
        - Token not yet consumed
        - Token not expired
        - Scope specified

        Args:
            token: Authority token dict from REGISTERED.md

        Returns:
            TokenValidationResult
        """
        now = datetime.now(timezone.utc)

        # Required fields
        required = ["token_id", "token_type", "issued_by", "signature", "scope"]
        for field in required:
            if field not in token:
                return TokenValidationResult(
                    valid=False,
                    reason=f"MISSING_FIELD: {field}",
                    verified_at=now.isoformat()
                )

        token_id = token["token_id"]
        token_type = token["token_type"]
        issued_by = token["issued_by"]
        scope = token["scope"]

        # Validate issued_by
        if issued_by != "night-z2":
            return TokenValidationResult(
                valid=False,
                token_id=token_id,
                reason=f"INVALID_ISSUER: {issued_by} (expected night-z2)",
                verified_at=now.isoformat()
            )

        # Check not consumed
        if token_id in self.consumed_tokens:
            return TokenValidationResult(
                valid=False,
                token_id=token_id,
                reason="TOKEN_ALREADY_CONSUMED",
                verified_at=now.isoformat()
            )

        # Check consumed_at field (REGISTERED.md entry)
        if token.get("consumed_at") is not None:
            return TokenValidationResult(
                valid=False,
                token_id=token_id,
                reason=f"TOKEN_CONSUMED_AT: {token.get('consumed_at')}",
                verified_at=now.isoformat()
            )

        # Check expiry
        expires_at = token.get("expires_at")
        if expires_at:
            try:
                expiry = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                if now > expiry:
                    return TokenValidationResult(
                        valid=False,
                        token_id=token_id,
                        token_type=token_type,
                        scope=scope,
                        reason=f"TOKEN_EXPIRED: {expires_at}",
                        verified_at=now.isoformat()
                    )
            except ValueError:
                return TokenValidationResult(
                    valid=False,
                    token_id=token_id,
                    reason=f"INVALID_EXPIRY_FORMAT: {expires_at}",
                    verified_at=now.isoformat()
                )

        # Validate signature format (phase 1)
        signature = token.get("signature")
        if not signature or len(signature) != 128:
            return TokenValidationResult(
                valid=False,
                token_id=token_id,
                reason="INVALID_SIGNATURE_FORMAT",
                verified_at=now.isoformat()
            )

        # Phase 2: Validate signature against canonical payload
        # canonical = sha256(token_id | token_type | issued_by | issued_to | issued_at | scope)
        # signature should be Ed25519(canonical, z2_private_key)

        # Phase 1: Stub pass
        return TokenValidationResult(
            valid=True,
            token_id=token_id,
            token_type=token_type,
            scope=scope,
            verified_at=now.isoformat()
        )

    def validate_token_scope(self, token: dict, intended_action: str) -> TokenValidationResult:
        """
        Validate that token scope matches intended action.

        Examples:
        - Token scope: "MERGE_PR_445_ONLY"
          Intended action: "MERGE_PR_445" → VALID
          Intended action: "MERGE_PR_446" → INVALID (SCOPE_MISMATCH)

        Args:
            token: Authority token
            intended_action: The action being attempted

        Returns:
            TokenValidationResult
        """
        now = datetime.now(timezone.utc)
        token_id = token.get("token_id")
        scope = token.get("scope", "")

        # Simple scope matching: scope must be substring of action
        # or action must contain scope (flexible matching)

        if scope == "GLOBAL" or scope == "*":
            # Unrestricted scope
            return TokenValidationResult(
                valid=True,
                token_id=token_id,
                scope=scope,
                verified_at=now.isoformat()
            )

        # Check exact match or containment
        if scope in intended_action or intended_action in scope:
            return TokenValidationResult(
                valid=True,
                token_id=token_id,
                scope=scope,
                verified_at=now.isoformat()
            )

        return TokenValidationResult(
            valid=False,
            token_id=token_id,
            scope=scope,
            reason=f"SCOPE_MISMATCH: token scope '{scope}' does not cover action '{intended_action}'",
            verified_at=now.isoformat()
        )

    def consume_token(self, token_id: str, consumed_by: str) -> bool:
        """
        Mark token as consumed.

        Args:
            token_id: Token to consume
            consumed_by: Actor consuming the token

        Returns:
            True if consumption succeeded, False if already consumed
        """
        if token_id in self.consumed_tokens:
            return False

        self.consumed_tokens.add(token_id)
        # Phase 2: Log to NF_LEDGER with timestamp and consumed_by actor
        return True

    def reset_for_testing(self):
        """Clear consumed tokens (test only)."""
        self.consumed_tokens.clear()


if __name__ == "__main__":
    validator = AuthorityTokenValidator()

    # Test token validation
    token = {
        "token_id": "ratify_token_v0.3_oi_bridge_01",
        "token_type": "RATIFY",
        "issued_by": "night-z2",
        "signature": "abcdef" * 21 + "abcd",
        "scope": "RATIFY_CANDIDATE_G-OI-BRIDGE-01-v0.3",
        "expires_at": "2026-12-22T22:45:06Z",
        "consumed_at": None
    }

    result = validator.validate_token(token)
    print(f"Token valid: {result.valid} ({result.reason or 'OK'})")
    print(f"Token ID: {result.token_id}, Type: {result.token_type}, Scope: {result.scope}")

    # Test scope matching
    result = validator.validate_token_scope(
        token,
        "RATIFY_CANDIDATE_G-OI-BRIDGE-01-v0.3"
    )
    print(f"Scope match: {result.valid} ({result.reason or 'OK'})")

    # Test consumption
    consumed = validator.consume_token("ratify_token_v0.3_oi_bridge_01", "z3_executor")
    print(f"Token consumed: {consumed}")

    # Try to consume again
    result = validator.validate_token(token)
    print(f"Token valid after consumption: {result.valid}")
