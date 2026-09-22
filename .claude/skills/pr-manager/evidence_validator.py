"""
OI-BRIDGE-01 Phase 1 — Evidence Validator

Validates evidence references (hash matching, source verification).
Issues EVIDENCE_VALID_TOKEN receipts on successful validation.
"""

import hashlib
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime, timezone


@dataclass
class EvidenceReference:
    """Reference to external evidence."""
    source: str  # URL or local path
    method: str  # fetch_and_sha256, check_run_status, etc.
    expected_hash: str  # SHA256 expected value
    timestamp: str  # ISO8601 UTC


@dataclass
class EvidenceValidationResult:
    """Result from evidence validation."""
    valid: bool
    evidence_ref: Optional[EvidenceReference] = None
    observed_hash: Optional[str] = None
    reason: Optional[str] = None
    token_issued: bool = False
    token_id: Optional[str] = None
    verified_at: Optional[str] = None


class EvidenceValidator:
    """Validate evidence references and issue EVIDENCE_VALID_TOKENs."""

    def __init__(self, github_transport=None, ledger_writer=None):
        """
        Initialize evidence validator.

        Args:
            github_transport: GitHub API client for fetching evidence
            ledger_writer: NF_LEDGER writer for logging validation
        """
        self.github_transport = github_transport
        self.ledger_writer = ledger_writer
        self.issued_tokens: dict[str, str] = {}  # hash -> token_id

    def validate_evidence_reference(self, evidence_ref: Dict[str, Any]) -> EvidenceValidationResult:
        """
        Validate evidence reference (hash matching).

        Evidence schema:
        {
          "source": "https://github.com/humanaios-ui/operations/commit/abc123",
          "method": "fetch_and_sha256",
          "expected_hash": "aaaaaaa...",
          "timestamp": "2026-09-22T20:00:00Z"
        }

        Args:
            evidence_ref: Evidence reference dict

        Returns:
            EvidenceValidationResult with validation status
        """
        now = datetime.now(timezone.utc)

        # Extract fields
        source = evidence_ref.get("source")
        method = evidence_ref.get("method", "fetch_and_sha256")
        expected_hash = evidence_ref.get("expected_hash", "").lower()

        if not source or not expected_hash:
            return EvidenceValidationResult(
                valid=False,
                reason="MISSING_FIELD: source or expected_hash",
                verified_at=now.isoformat()
            )

        # Phase 1: Fetch and validate
        # Phase 2: Support multiple methods (check_run_status, issue_created, etc.)

        if method == "fetch_and_sha256":
            return self._validate_fetch_hash(source, expected_hash, evidence_ref, now)
        else:
            return EvidenceValidationResult(
                valid=False,
                reason=f"UNSUPPORTED_METHOD: {method}",
                verified_at=now.isoformat()
            )

    def _validate_fetch_hash(self, source: str, expected_hash: str,
                            evidence_ref: Dict[str, Any],
                            now: datetime) -> EvidenceValidationResult:
        """
        Validate evidence by fetching source and comparing SHA256.

        Args:
            source: Source URL or path
            expected_hash: Expected SHA256 hash
            evidence_ref: Full evidence reference
            now: Current timestamp

        Returns:
            EvidenceValidationResult
        """
        # Phase 1: Stub validation (always pass for testing)
        # Phase 2: Actually fetch from source and compute hash

        # Simulate hash computation
        observed_hash = self._simulate_fetch_hash(source)

        # Compare hashes
        if observed_hash.lower() != expected_hash.lower():
            return EvidenceValidationResult(
                valid=False,
                evidence_ref=EvidenceReference(
                    source=source,
                    method="fetch_and_sha256",
                    expected_hash=expected_hash,
                    timestamp=evidence_ref.get("timestamp", now.isoformat())
                ),
                observed_hash=observed_hash,
                reason=f"HASH_MISMATCH: expected {expected_hash[:16]}... got {observed_hash[:16]}...",
                verified_at=now.isoformat()
            )

        # Hash matches: issue EVIDENCE_VALID_TOKEN
        token_id = self._issue_evidence_valid_token(source, observed_hash, now)

        # Log to ledger
        if self.ledger_writer:
            self.ledger_writer.append_event("EVIDENCE_VALIDATED", {
                "source": source,
                "hash": observed_hash,
                "token_id": token_id,
            })

        return EvidenceValidationResult(
            valid=True,
            evidence_ref=EvidenceReference(
                source=source,
                method="fetch_and_sha256",
                expected_hash=expected_hash,
                timestamp=evidence_ref.get("timestamp", now.isoformat())
            ),
            observed_hash=observed_hash,
            token_issued=True,
            token_id=token_id,
            verified_at=now.isoformat()
        )

    def _simulate_fetch_hash(self, source: str) -> str:
        """
        Simulate fetching and hashing evidence.

        Phase 1: Return mock hash matching expected for testing.
        Phase 2: Actually fetch from GitHub/etc and compute real hash.

        Args:
            source: Source URL

        Returns:
            SHA256 hash (hex string)
        """
        # Phase 1 stub: return deterministic hash based on source
        # In tests, mock this to return different hashes for mismatch testing
        return hashlib.sha256(source.encode()).hexdigest()

    def _issue_evidence_valid_token(self, source: str, hash_value: str,
                                   now: datetime) -> str:
        """
        Issue EVIDENCE_VALID_TOKEN (cryptographic receipt).

        This is issued by the VALIDATING NODE, not by the bridge.
        Bridge verifies the token but does not upgrade it to authority.

        Args:
            source: Source URL
            hash_value: Validated hash
            now: Timestamp

        Returns:
            Token ID
        """
        # Generate token ID
        token_id = f"evidence_valid_token_{hash_value[:16]}"

        # Store token
        self.issued_tokens[hash_value] = token_id

        # Phase 2: Sign token with node's Ed25519 key and post receipt
        # For now, just return token ID

        return token_id

    def get_validation_receipt(self, token_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve validation receipt (EVIDENCE_VALID_TOKEN).

        Args:
            token_id: Token identifier

        Returns:
            Receipt dict or None if not found
        """
        # Phase 1: Stub
        # Phase 2: Fetch from ledger or token store
        return {
            "token_id": token_id,
            "token_type": "EVIDENCE_VALID",
            "issued_by": "bridge",  # Actually issued by validating node
            "issued_at": datetime.now(timezone.utc).isoformat(),
        }


if __name__ == "__main__":
    validator = EvidenceValidator()

    # Test evidence validation
    evidence = {
        "source": "https://github.com/humanaios-ui/operations/commit/abc123",
        "method": "fetch_and_sha256",
        "expected_hash": "abcdef1234567890" * 4,  # 64 hex chars
        "timestamp": "2026-09-22T20:00:00Z"
    }

    result = validator.validate_evidence_reference(evidence)
    print(f"Evidence valid: {result.valid}")
    print(f"Token issued: {result.token_issued} (ID: {result.token_id})")

    # Test mismatch
    evidence_bad = {
        "source": "https://github.com/humanaios-ui/operations/commit/abc123",
        "method": "fetch_and_sha256",
        "expected_hash": "0000000000000000" * 4,  # Doesn't match
        "timestamp": "2026-09-22T20:00:00Z"
    }

    result = validator.validate_evidence_reference(evidence_bad)
    print(f"Evidence mismatch: {not result.valid} ({result.reason})")
