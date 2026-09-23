"""OI-BRIDGE-01 Evidence Validator — standing-corrected prototype.

Current fetch/hash path is simulated. Therefore a matching simulated hash is NOT
allowed to become a VERIFIED receipt. The BridgeReceiptFeed must refuse this
result until a real external fetch/hash verifier replaces the stub.
"""

import hashlib
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime, timezone


@dataclass
class EvidenceReference:
    source: str
    method: str
    expected_hash: str
    timestamp: str


@dataclass
class EvidenceValidationResult:
    valid: bool
    evidence_ref: Optional[EvidenceReference] = None
    observed_hash: Optional[str] = None
    reason: Optional[str] = None
    token_issued: bool = False
    token_id: Optional[str] = None
    verified_at: Optional[str] = None
    verification_status: str = "UNVERIFIED"
    verification_method: str = "NONE"


class EvidenceValidator:
    def __init__(self, github_transport=None, ledger_writer=None):
        self.github_transport = github_transport
        self.ledger_writer = ledger_writer
        self.issued_tokens: dict[str, str] = {}

    def validate_evidence_reference(self, evidence_ref: Dict[str, Any]) -> EvidenceValidationResult:
        now = datetime.now(timezone.utc)
        source = evidence_ref.get("source")
        method = evidence_ref.get("method", "fetch_and_sha256")
        expected_hash = evidence_ref.get("expected_hash", "").lower()

        if not source or not expected_hash:
            return EvidenceValidationResult(
                valid=False,
                reason="MISSING_FIELD: source or expected_hash",
                verified_at=now.isoformat(),
            )

        if method == "fetch_and_sha256":
            return self._validate_fetch_hash(source, expected_hash, evidence_ref, now)

        return EvidenceValidationResult(
            valid=False,
            reason=f"UNSUPPORTED_METHOD: {method}",
            verified_at=now.isoformat(),
        )

    def _validate_fetch_hash(
        self,
        source: str,
        expected_hash: str,
        evidence_ref: Dict[str, Any],
        now: datetime,
    ) -> EvidenceValidationResult:
        # IMPORTANT: still simulated.
        observed_hash = self._simulate_fetch_hash(source)

        if observed_hash.lower() != expected_hash.lower():
            return EvidenceValidationResult(
                valid=False,
                evidence_ref=EvidenceReference(
                    source=source,
                    method="fetch_and_sha256",
                    expected_hash=expected_hash,
                    timestamp=evidence_ref.get("timestamp", now.isoformat()),
                ),
                observed_hash=observed_hash,
                reason="HASH_MISMATCH_SIMULATED_PATH",
                verified_at=now.isoformat(),
                verification_status="SIMULATED",
                verification_method="SIMULATED_FETCH_HASH",
            )

        # A successful simulation proves only that the test fixture is internally
        # consistent. It must NOT mint a VERIFIED receipt.
        candidate_id = f"evidence_candidate_{observed_hash[:16]}"

        if self.ledger_writer:
            self.ledger_writer.append_event("EVIDENCE_VALIDATION_SIMULATED", {
                "source": source,
                "hash": observed_hash,
                "candidate_id": candidate_id,
                "verification_status": "SIMULATED",
                "verification_method": "SIMULATED_FETCH_HASH",
            })

        return EvidenceValidationResult(
            valid=True,
            evidence_ref=EvidenceReference(
                source=source,
                method="fetch_and_sha256",
                expected_hash=expected_hash,
                timestamp=evidence_ref.get("timestamp", now.isoformat()),
            ),
            observed_hash=observed_hash,
            token_issued=False,
            token_id=candidate_id,
            verified_at=now.isoformat(),
            verification_status="SIMULATED",
            verification_method="SIMULATED_FETCH_HASH",
        )

    def _simulate_fetch_hash(self, source: str) -> str:
        return hashlib.sha256(source.encode()).hexdigest()

    def get_validation_receipt(self, token_id: str) -> Optional[Dict[str, Any]]:
        # Explicitly non-verifying receipt candidate. Consumers must reject it.
        return {
            "receipt_id": token_id,
            "receipt_type": "EVIDENCE_VALIDATION",
            "verification_status": "SIMULATED",
            "verification_strength": "OBSERVED",
            "verification_method": "SIMULATED_FETCH_HASH",
            "issuer": "bridge-evidence-validator-stub",
            "issued_at": datetime.now(timezone.utc).isoformat(),
        }
