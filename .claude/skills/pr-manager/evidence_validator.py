"""OI-BRIDGE-01 evidence validator — simulated fixture boundary.

The current fetch/hash implementation is a fixture simulation. Matching the
fixture is recorded as consistency only and does not produce valid=True or a
VERIFIED receipt.
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
    fixture_consistent: bool = False
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

    def validate_evidence_reference(self, evidence_ref: Dict[str, Any]) -> EvidenceValidationResult:
        now = datetime.now(timezone.utc)
        source = evidence_ref.get("source")
        method = evidence_ref.get("method", "fetch_and_sha256")
        expected_hash = str(evidence_ref.get("expected_hash", "")).lower()

        if not source or not expected_hash:
            return EvidenceValidationResult(
                valid=False,
                reason="MISSING_FIELD: source or expected_hash",
                verified_at=now.isoformat(),
            )

        if method != "fetch_and_sha256":
            return EvidenceValidationResult(
                valid=False,
                reason=f"UNSUPPORTED_METHOD:{method}",
                verified_at=now.isoformat(),
            )

        observed_hash = hashlib.sha256(str(source).encode()).hexdigest()
        consistent = observed_hash.lower() == expected_hash.lower()
        candidate_id = f"evidence_candidate_{observed_hash[:16]}"

        if self.ledger_writer:
            self.ledger_writer.append_event(
                "EVIDENCE_VALIDATION_SIMULATED",
                {
                    "source": source,
                    "hash": observed_hash,
                    "candidate_id": candidate_id,
                    "fixture_consistent": consistent,
                    "verification_status": "SIMULATED",
                    "verification_method": "SIMULATED_FETCH_HASH",
                },
            )

        return EvidenceValidationResult(
            valid=False,
            fixture_consistent=consistent,
            evidence_ref=EvidenceReference(
                source=str(source),
                method="fetch_and_sha256",
                expected_hash=expected_hash,
                timestamp=evidence_ref.get("timestamp", now.isoformat()),
            ),
            observed_hash=observed_hash,
            reason="SIMULATED_VALIDATION_ONLY",
            token_issued=False,
            token_id=candidate_id,
            verified_at=now.isoformat(),
            verification_status="SIMULATED",
            verification_method="SIMULATED_FETCH_HASH",
        )

    def get_validation_receipt(self, token_id: str) -> Optional[Dict[str, Any]]:
        return {
            "receipt_id": token_id,
            "receipt_type": "EVIDENCE_VALIDATION",
            "verification_status": "SIMULATED",
            "verification_strength": "OBSERVED",
            "verification_method": "SIMULATED_FETCH_HASH",
            "issuer": "bridge-evidence-validator-stub",
            "issued_at": datetime.now(timezone.utc).isoformat(),
        }
