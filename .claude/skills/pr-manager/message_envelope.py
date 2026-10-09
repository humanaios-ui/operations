"""
OI-BRIDGE-01 Phase 1 — Message Envelope Parser

Parses GitHub comment text into MessageEnvelope (v0.3 schema).
Extracts sender identity, timestamp, signature, body, state fields.
"""

import json
import re
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from datetime import datetime, timezone


@dataclass
class MessageEnvelope:
    """Message envelope per OI-BRIDGE-01 v0.3 schema."""
    message_id: str
    sender_node_id: str
    recipient_node_id: str
    timestamp: str  # ISO8601 UTC
    sender_signature: Optional[str]  # Ed25519 hex or None
    body: Dict[str, Any]
    visibility_state: str  # PRIVATE|BLIND|RELEASED_TO_COMMONS
    epistemic_standing: str  # CLAIMED|EVIDENCE_CHECKED|OBSERVED|REGISTERED
    delivery_state: str  # PENDING|DELIVERED|ACKNOWLEDGED


class MessageEnvelopeParser:
    """Parse GitHub comments into MessageEnvelope objects."""

    def __init__(self, repo_owner: str, repo_name: str):
        """
        Initialize message parser.

        Args:
            repo_owner: Repository owner
            repo_name: Repository name
        """
        self.repo_owner = repo_owner
        self.repo_name = repo_name

    def parse_github_comment(self, pr_number: int, comment_id: int,
                            author: str, body: str,
                            created_at: str) -> Optional[MessageEnvelope]:
        """
        Parse a GitHub comment into MessageEnvelope.

        Signature detection:
        - If comment body contains markdown code block with json containing "signature" key
        - Or extract from commit signature if available (Phase 2)

        Args:
            pr_number: PR number
            comment_id: GitHub comment ID
            author: Comment author (GitHub username)
            body: Comment text (may contain JSON payload + optional signature)
            created_at: Comment created_at timestamp (ISO8601)

        Returns:
            MessageEnvelope or None if parse fails
        """
        # Generate message_id from PR + comment
        message_id = f"{self.repo_owner}#{self.repo_name}#{pr_number}#comment#{comment_id}"

        # Parse comment body
        # Look for JSON payload in markdown code block
        json_payload = self._extract_json_payload(body)

        if not json_payload:
            # Comment is just text (governance decision, etc.)
            # Treat as visibility=BLIND (governance-only, not message protocol)
            json_payload = {"text": body}

        # Extract/infer fields
        sender_node_id = self._infer_sender(author)
        recipient_node_id = self._infer_recipient(body)
        sender_signature = self._extract_signature(body)
        visibility_state = self._infer_visibility(body, sender_node_id)
        epistemic_standing = self._infer_epistemic(body, sender_signature)

        # Create envelope
        envelope = MessageEnvelope(
            message_id=message_id,
            sender_node_id=sender_node_id,
            recipient_node_id=recipient_node_id,
            timestamp=created_at,
            sender_signature=sender_signature,
            body=json_payload,
            visibility_state=visibility_state,
            epistemic_standing=epistemic_standing,
            delivery_state="PENDING",
        )

        return envelope

    def _extract_json_payload(self, body: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from markdown code block."""
        # Look for ```json ... ``` or just ```{ ... }```
        match = re.search(r'```(?:json)?\s*(\{[^`]+\})\s*```', body, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                return None
        return None

    def _infer_sender(self, github_author: str) -> str:
        """
        Infer sender_node_id from GitHub author.

        Examples:
        - "claude-z1" → "claude-z1"
        - "humanaios-ui" + comment author check → determine actual author
        - "chatgpt-gpt-5.6-sol" → "chatgpt-gpt-5.6-sol"
        """
        # Phase 1: Direct mapping from GitHub username
        # Phase 2: Use principal mapping table for identity resolution

        if github_author == "humanaios-ui":
            # Could be Claude or ChatGPT via GitHub API
            # Actual author would be in comment body or principal_mapping table
            return "unknown-via-humanaios-ui"

        return github_author

    def _infer_recipient(self, body: str) -> str:
        """Infer recipient_node_id from comment text."""
        if "bridge" in body.lower():
            return "bridge"
        if "@night" in body.lower() or "z2" in body.lower():
            return "night-z2"
        return "bridge"  # default

    def _extract_signature(self, body: str) -> Optional[str]:
        """Extract Ed25519 signature from comment (hex string)."""
        # Look for signature: <128-char-hex> pattern
        match = re.search(r'signature[:\s]+([a-f0-9]{128})', body, re.IGNORECASE)
        if match:
            return match.group(1)
        return None

    def _infer_visibility(self, body: str, sender_node_id: str) -> str:
        """Infer visibility_state from comment markers."""
        if "COMMONS" in body or "PUBLIC" in body:
            return "RELEASED_TO_COMMONS"
        if "BLIND" in body:
            return "BLIND"
        return "PRIVATE"  # default

    def _infer_epistemic(self, body: str, signature: Optional[str]) -> str:
        """Infer epistemic_standing from content + signature."""
        if "REGISTERED" in body:
            return "REGISTERED"
        if "EVIDENCE_CHECKED" in body or "validated" in body.lower():
            return "EVIDENCE_CHECKED"
        if "OBSERVED" in body:
            return "OBSERVED"
        # Default to CLAIMED
        return "CLAIMED"


if __name__ == "__main__":
    parser = MessageEnvelopeParser("humanaios-ui", "operations")

    # Test comment
    test_body = """```json
{
  "claim": "CI is passing; ready to merge",
  "evidence": [{"type": "check_run", "id": "abc123"}]
}
```

Signature: abcdef123456789abcdef123456789abcdef123456789abcdef123456789abcdef123456789abcdef123456789abcdef123456789abcdef123456789abcdef123456789abcdef123456
"""

    envelope = parser.parse_github_comment(
        pr_number=445,
        comment_id=12345,
        author="claude-z1",
        body=test_body,
        created_at=datetime.now(timezone.utc).isoformat()
    )

    if envelope:
        print(json.dumps(asdict(envelope), indent=2))
    else:
        print("Failed to parse comment")
