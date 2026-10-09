"""
OI-BRIDGE-01 Phase 1 — Identity Resolver

Implements three-plane principal resolution and identity confusion (T7) detection.
Maps (transport_principal, content_author) → authority_scope.
Enforces three-plane separation invariant.
"""

import json
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime, timezone


@dataclass
class PrincipalMapping:
    """Three-plane principal identity mapping."""
    mapping_id: str
    transport_principal: str
    transport_identity_verified: bool
    content_author: str
    content_author_verified: bool
    human_principal: Optional[str] = None
    human_signature: Optional[str] = None
    speaker_identity_chain: list = None
    authority_effect: str = None
    authority_scope: str = None
    trusted_issuer: str = None


@dataclass
class ProvenanceEnvelope:
    """Provenance envelope extracted from message."""
    message_id: str
    transport_principal: str
    content_author: str
    human_principal: Optional[str] = None
    signature: Optional[str] = None
    timestamp: str = None


@dataclass
class IdentityResolutionResult:
    """Result from principal resolution."""
    mapping_id: str
    is_valid: bool
    authority_scope: str
    is_identity_confused: bool  # T7 test
    identity_confusion_reason: Optional[str] = None
    mapping: Optional[PrincipalMapping] = None
    resolved_at: str = None


class IdentityResolver:
    """Resolve principals from three-plane envelope and detect identity confusion (T7)."""

    def __init__(self, mapping_path: str = ".claude/skills/pr-manager/principal_mapping.json"):
        """
        Initialize identity resolver.

        Args:
            mapping_path: Path to principal mapping JSON
        """
        self.mapping_path = mapping_path
        self.mappings: Dict[str, PrincipalMapping] = {}
        self._load_mappings()

    def _load_mappings(self) -> None:
        """Load principal mappings from JSON file."""
        try:
            with open(self.mapping_path, 'r') as f:
                data = json.load(f)
                for mapping_dict in data.get("mappings", []):
                    mapping = PrincipalMapping(
                        mapping_id=mapping_dict["mapping_id"],
                        transport_principal=mapping_dict["transport_principal"],
                        transport_identity_verified=mapping_dict.get("transport_identity_verified", False),
                        content_author=mapping_dict["content_author"],
                        content_author_verified=mapping_dict.get("content_author_verified", False),
                        human_principal=mapping_dict.get("human_principal"),
                        human_signature=mapping_dict.get("human_signature"),
                        speaker_identity_chain=mapping_dict.get("speaker_identity_chain", []),
                        authority_effect=mapping_dict.get("authority_effect"),
                        authority_scope=mapping_dict.get("authority_scope"),
                        trusted_issuer=mapping_dict.get("trusted_issuer"),
                    )
                    self.mappings[mapping_dict["mapping_id"]] = mapping
        except Exception as e:
            raise Exception(f"IDENTITY_MAPPING_LOAD_FAILED: {e}")

    def resolve_provenance(self, provenance: ProvenanceEnvelope) -> IdentityResolutionResult:
        """
        Resolve principal identity from provenance envelope.

        Implements three-plane separation check:
        - If transport_principal ≠ content_author AND content_author ≠ human_principal
          → Identity confusion (T7 test case) → escalate to HUMAN_REQUIRED

        Args:
            provenance: ProvenanceEnvelope with transport, content, human principals

        Returns:
            IdentityResolutionResult with authority scope and T7 detection
        """
        now = datetime.now(timezone.utc).isoformat()

        # Find matching mapping by (transport_principal, content_author)
        matching_mapping = self._find_mapping(
            provenance.transport_principal,
            provenance.content_author
        )

        if not matching_mapping:
            return IdentityResolutionResult(
                mapping_id="UNKNOWN",
                is_valid=False,
                authority_scope="UNKNOWN",
                is_identity_confused=True,
                identity_confusion_reason="NO_MAPPING_FOUND",
                resolved_at=now
            )

        # Run T7 identity confusion test
        is_confused, confusion_reason = self._test_identity_confusion(
            matching_mapping, provenance
        )

        return IdentityResolutionResult(
            mapping_id=matching_mapping.mapping_id,
            is_valid=not is_confused and matching_mapping.transport_identity_verified,
            authority_scope=matching_mapping.authority_scope,
            is_identity_confused=is_confused,
            identity_confusion_reason=confusion_reason,
            mapping=matching_mapping,
            resolved_at=now
        )

    def _find_mapping(self, transport_principal: str, content_author: str) -> Optional[PrincipalMapping]:
        """
        Find mapping matching (transport_principal, content_author) pair.

        Returns:
            Matching PrincipalMapping or None
        """
        for mapping in self.mappings.values():
            if (mapping.transport_principal == transport_principal and
                mapping.content_author == content_author):
                return mapping
        return None

    def _test_identity_confusion(self, mapping: PrincipalMapping,
                                provenance: ProvenanceEnvelope) -> tuple[bool, Optional[str]]:
        """
        T7 Identity Confusion Test.

        Detects when three planes are inconsistent:
        - transport_principal ≠ content_author (allowed if content_author has human)
        - content_author ≠ human_principal (not allowed)
        - speaker_identity_chain contains null (chain break, indicates incomplete human oversight)

        Returns:
            (is_confused: bool, reason: Optional[str])
        """
        # Check: transport ≠ content (allowed if content is Z-node with authority)
        if mapping.transport_principal != mapping.content_author:
            if mapping.authority_scope in ["Z1_PROPOSER", "Z2_RATIFIER_FULL"]:
                # Z-nodes are allowed to differ from transport (they carry authority)
                pass
            else:
                # Non-Z-node with transport ≠ content requires human oversight
                if not mapping.human_principal:
                    return True, "TRANSPORT_CONTENT_MISMATCH_NO_HUMAN"

        # Check: chain break (null indicates no further actor, incomplete chain)
        if None in mapping.speaker_identity_chain:
            chain_index = mapping.speaker_identity_chain.index(None)
            if chain_index < 2:  # null before position 2 means incomplete
                return True, f"CHAIN_BREAK_AT_POSITION_{chain_index}"

        # Check: human_principal expected for non-Z scope
        if mapping.authority_scope not in ["Z1_PROPOSER", "Z2_RATIFIER_FULL"]:
            if not mapping.human_principal:
                return True, "NON_Z_NODE_NO_HUMAN_PRINCIPAL"

        # All checks passed: no identity confusion
        return False, None

    def get_authority_scope(self, transport_principal: str, content_author: str) -> str:
        """
        Get authority scope for (transport_principal, content_author) pair.

        Returns:
            Authority scope (Z1_PROPOSER, Z2_RATIFIER_FULL, REVIEW_ONLY, UNKNOWN)
        """
        mapping = self._find_mapping(transport_principal, content_author)
        if mapping:
            return mapping.authority_scope
        return "UNKNOWN"

    def is_z2_authorized(self, content_author: str) -> bool:
        """Check if content_author is Z2 (night-z2)."""
        for mapping in self.mappings.values():
            if (mapping.content_author == content_author and
                mapping.authority_scope == "Z2_RATIFIER_FULL"):
                return True
        return False

    def is_z1_authorized(self, content_author: str) -> bool:
        """Check if content_author is Z1 (claude-z1)."""
        for mapping in self.mappings.values():
            if (mapping.content_author == content_author and
                mapping.authority_scope == "Z1_PROPOSER"):
                return True
        return False


if __name__ == "__main__":
    resolver = IdentityResolver()

    # Test Case 1: Z1 (Claude) proposer
    provenance_z1 = ProvenanceEnvelope(
        message_id="msg_001",
        transport_principal="humanaios-ui",
        content_author="claude-z1",
    )
    result = resolver.resolve_provenance(provenance_z1)
    print(f"Z1 Resolution: {result.mapping_id} → {result.authority_scope} (confused: {result.is_identity_confused})")

    # Test Case 2: ChatGPT with incomplete chain (T7 identity confusion)
    provenance_chatgpt = ProvenanceEnvelope(
        message_id="msg_002",
        transport_principal="humanaios-ui",
        content_author="chatgpt-gpt-5.6-sol",
    )
    result = resolver.resolve_provenance(provenance_chatgpt)
    print(f"ChatGPT Resolution: {result.mapping_id} → {result.authority_scope} (confused: {result.is_identity_confused}, reason: {result.identity_confusion_reason})")

    # Test Case 3: Z2 (Night) with full chain
    provenance_z2 = ProvenanceEnvelope(
        message_id="msg_003",
        transport_principal="humanaios-ui",
        content_author="night-z2",
        human_principal="carly.r.anderson",
    )
    result = resolver.resolve_provenance(provenance_z2)
    print(f"Z2 Resolution: {result.mapping_id} → {result.authority_scope} (confused: {result.is_identity_confused})")

    # Test authority checks
    print(f"\nAuthority Checks:")
    print(f"  Is 'night-z2' Z2? {resolver.is_z2_authorized('night-z2')}")
    print(f"  Is 'claude-z1' Z1? {resolver.is_z1_authorized('claude-z1')}")
