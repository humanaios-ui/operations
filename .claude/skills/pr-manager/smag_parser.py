"""
OI-BRIDGE-01 Phase 1 — SMAG Parser

Structured Message Annotation Grammar (SMAG) parser.
Extracts claim structure, Brier scores, evidence, and metadata from messages.
Supports flexible decimal precision (0.5, 0.50, 0.500, etc.).
"""

import re
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone


@dataclass
class ClaimComponent:
    """Single claim component extracted from message."""
    claim_id: str
    claim_text: str
    claim_type: str  # HYPOTHESIS, PREDICTION, VERDICT, EVIDENCE
    brier_score: Optional[float] = None
    confidence: Optional[float] = None
    timestamp: Optional[str] = None
    source: Optional[str] = None


@dataclass
class StructuredMessage:
    """SMAG-parsed message structure."""
    message_id: str
    sender: str
    claims: List[ClaimComponent]
    evidence_refs: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    parsed_at: str


class SMAGParser:
    """Parse Structured Message Annotation Grammar (SMAG) format."""

    # Brier score pattern: supports flexible decimal precision
    # Matches: 0.5, 0.50, 0.500, 0.0, 1.0, etc.
    BRIER_PATTERN = r"brier[:\s]+([0-9]*\.?[0-9]+)"

    # Confidence pattern: percentage or decimal
    CONFIDENCE_PATTERN = r"confidence[:\s]+([0-9]*\.?[0-9]+)\s*%?"

    # Claim pattern: identifies claim boundaries
    CLAIM_PATTERN = r"(claim|hypothesis|prediction|verdict|evidence)[:\s]+([^\n]+)"

    # Evidence reference pattern
    EVIDENCE_PATTERN = r"evidence[:\s]+\{([^}]+)\}"

    def __init__(self):
        """Initialize SMAG parser."""
        self.brier_regex = re.compile(self.BRIER_PATTERN, re.IGNORECASE)
        self.confidence_regex = re.compile(self.CONFIDENCE_PATTERN, re.IGNORECASE)
        self.claim_regex = re.compile(self.CLAIM_PATTERN, re.IGNORECASE)
        self.evidence_regex = re.compile(self.EVIDENCE_PATTERN, re.IGNORECASE)

    def parse_message(self, message_id: str, sender: str, body: str) -> StructuredMessage:
        """
        Parse SMAG-formatted message.

        Expected format:
        ```
        claim: This is a prediction about behavior X
        brier: 0.65
        confidence: 85%
        evidence: {"source": "commit abc123", "type": "code_analysis"}
        ```

        Args:
            message_id: Message identifier
            sender: Sender node ID
            body: Message body text

        Returns:
            StructuredMessage with parsed claims and evidence
        """
        now = datetime.now(timezone.utc).isoformat()
        claims = []
        evidence_refs = []

        # Extract claims
        for match in self.claim_regex.finditer(body):
            claim_type = match.group(1).upper()
            claim_text = match.group(2).strip()

            # Extract brier and confidence for this claim
            brier_score = self._extract_brier(body)
            confidence = self._extract_confidence(body)

            claim = ClaimComponent(
                claim_id=f"{message_id}_claim_{len(claims)}",
                claim_text=claim_text,
                claim_type=claim_type,
                brier_score=brier_score,
                confidence=confidence,
                timestamp=now,
                source=sender,
            )
            claims.append(claim)

        # Extract evidence references
        for match in self.evidence_regex.finditer(body):
            evidence_json = match.group(1)
            try:
                import json
                evidence_ref = json.loads("{" + evidence_json + "}")
                evidence_refs.append(evidence_ref)
            except:
                # If not valid JSON, store as string
                evidence_refs.append({"raw": evidence_json})

        metadata = {
            "parsed_at": now,
            "claim_count": len(claims),
            "evidence_count": len(evidence_refs),
        }

        return StructuredMessage(
            message_id=message_id,
            sender=sender,
            claims=claims,
            evidence_refs=evidence_refs,
            metadata=metadata,
            parsed_at=now,
        )

    def _extract_brier(self, body: str) -> Optional[float]:
        """
        Extract Brier score from text (flexible decimal precision).

        Supports: 0.5, 0.50, 0.500, 0.0, 1.0, etc.

        Args:
            body: Message body

        Returns:
            Brier score (float) or None
        """
        match = self.brier_regex.search(body)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        return None

    def _extract_confidence(self, body: str) -> Optional[float]:
        """
        Extract confidence from text (percentage or decimal).

        Args:
            body: Message body

        Returns:
            Confidence (float, 0.0-1.0) or None
        """
        match = self.confidence_regex.search(body)
        if match:
            try:
                value = float(match.group(1))
                # If >= 1, assume it's a percentage
                if value > 1:
                    return value / 100.0
                return value
            except ValueError:
                return None
        return None

    def validate_brier(self, score: float) -> bool:
        """
        Validate Brier score (must be 0.0 ≤ score ≤ 1.0).

        Args:
            score: Brier score

        Returns:
            True if valid
        """
        return 0.0 <= score <= 1.0

    def validate_confidence(self, confidence: float) -> bool:
        """
        Validate confidence (must be 0.0 ≤ confidence ≤ 1.0).

        Args:
            confidence: Confidence value

        Returns:
            True if valid
        """
        return 0.0 <= confidence <= 1.0


if __name__ == "__main__":
    parser = SMAGParser()

    # Test flexible Brier precision
    message_body = """
    claim: This PR introduces a performance regression
    brier: 0.65
    confidence: 75%
    evidence: {"source": "commit abc123def456", "method": "benchmarking"}
    """

    result = parser.parse_message("msg_001", "claude-z1", message_body)
    print(f"Parsed {len(result.claims)} claim(s):")
    for claim in result.claims:
        print(f"  - {claim.claim_text} (brier: {claim.brier_score}, confidence: {claim.confidence})")
    print(f"Evidence refs: {result.evidence_refs}")

    # Test flexible decimal formats
    test_cases = [
        ("brier: 0.5", 0.5),
        ("brier: 0.50", 0.50),
        ("brier: 0.500", 0.500),
        ("brier: 0.0", 0.0),
        ("brier: 1.0", 1.0),
        ("brier: 0.123456", 0.123456),
    ]

    print("\nFlexible Brier precision tests:")
    for text, expected in test_cases:
        extracted = parser._extract_brier(text)
        status = "✓" if extracted == expected else "✗"
        print(f"  {status} {text} → {extracted} (expected {expected})")
