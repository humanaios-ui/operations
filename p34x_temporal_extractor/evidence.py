"""Evidence grounding interface and implementations.

Red team requirement: grounding must be based on signed, append-only,
independently-attested evidence. This module defines the interface and
provides initial git/ledger implementations.

In v1, evidence providers are optional backends; in v1.5, signature
verification is mandatory for blocking verdicts.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any
import re
from datetime import datetime


@dataclass
class EvidenceRecord:
    """A grounded evidence record."""
    source: str  # "git" | "ledger" | "tool-transcript"
    ref: str  # Reference ID (SHA, entry ID, trace ID)
    value: str  # The evidence value itself
    signature: Optional[str] = None  # Digital signature (v1.5)
    algorithm: Optional[str] = None  # Signature algorithm ("sha256-rsa", etc.)
    attestation_time: Optional[str] = None  # RFC 3339 timestamp
    signed: bool = False  # Whether signature has been verified

    def is_trustworthy(self) -> bool:
        """In v1, trust everything. In v1.5, require signature."""
        # TODO v1.5: require self.signed and self.signature is not None
        return True


class EvidenceProvider(ABC):
    """Abstract base class for evidence resolution."""

    @abstractmethod
    def resolve(self, value: str, context: Optional[Dict[str, Any]] = None) -> Optional[EvidenceRecord]:
        """Resolve a temporal value against evidence.

        Args:
            value: The temporal value to ground (e.g., "2026-09-23", "4–6 hours")
            context: Optional context (source file, section, etc.)

        Returns:
            EvidenceRecord if grounded, None otherwise
        """
        pass

    @abstractmethod
    def name(self) -> str:
        """Human-readable provider name."""
        pass


class GitLogProvider(EvidenceProvider):
    """Resolve timestamps against git commit log.

    In v1, this is a stub that checks if a date appears in any commit message
    of the current repo. In v1.5, require commit signing.
    """

    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path

    def resolve(self, value: str, context: Optional[Dict[str, Any]] = None) -> Optional[EvidenceRecord]:
        """Check if value appears in git log."""
        # TODO: implement `git log --all --grep=<value>` + return commit SHA
        # For now, return None (unimplemented)
        return None

    def name(self) -> str:
        return "git-log"


class LedgerProvider(EvidenceProvider):
    """Resolve timestamps against the HumanAIOS ledger.

    Checks REGISTERED.md for molt windows and IC closure entries.
    In v1.5, validate against signed ledger entries (NF_LEDGER.jsonl).
    """

    def __init__(self, ledger_path: str = "REGISTERED.md"):
        self.ledger_path = ledger_path
        self._molt_windows: Dict[str, str] = {}
        self._load_molt_windows()

    def _load_molt_windows(self):
        """Parse REGISTERED.md for molt window dates."""
        # TODO: Parse REGISTERED.md and extract molt window dates
        # For now, load some known windows as a stub
        self._molt_windows = {
            "2026-09-23": "molt_id=f7a49f667c09f1f6",
        }

    def resolve(self, value: str, context: Optional[Dict[str, Any]] = None) -> Optional[EvidenceRecord]:
        """Check if value matches a ratified molt window."""
        # Match ISO dates
        iso_date_pattern = r"\d{4}-\d{2}-\d{2}"
        match = re.search(iso_date_pattern, value)
        if not match:
            return None

        date = match.group(0)
        if date in self._molt_windows:
            return EvidenceRecord(
                source="ledger",
                ref=self._molt_windows[date],
                value=value,
                attestation_time=datetime.now().isoformat() + "Z",
            )

        return None

    def name(self) -> str:
        return "ledger"


class ToolTranscriptProvider(EvidenceProvider):
    """Resolve timestamps against tool call transcripts.

    Checks the MCP trace logs for tool timestamps and measurements.
    In v1.5, validate trace signatures.
    """

    def __init__(self, traces_path: str = ".claude/tool_traces"):
        self.traces_path = traces_path

    def resolve(self, value: str, context: Optional[Dict[str, Any]] = None) -> Optional[EvidenceRecord]:
        """Check if value appears in tool transcripts."""
        # TODO: Load .claude/tool_traces/*.jsonl and search
        return None

    def name(self) -> str:
        return "tool-transcript"


class CompositeEvidenceProvider(EvidenceProvider):
    """Composite provider that tries multiple backends in order."""

    def __init__(self, providers: list[EvidenceProvider]):
        self.providers = providers

    def resolve(self, value: str, context: Optional[Dict[str, Any]] = None) -> Optional[EvidenceRecord]:
        """Try each provider in order; return first match."""
        for provider in self.providers:
            record = provider.resolve(value, context)
            if record:
                return record
        return None

    def name(self) -> str:
        return "composite:" + ",".join(p.name() for p in self.providers)


# Stub implementations (v1 baseline)

class QuotedSourceProvider(EvidenceProvider):
    """Evidence from quoted external sources (SLAs, user text, documents).

    In v1, this is a marker only. In v1.5, validate quote spans.
    """

    def resolve(self, value: str, context: Optional[Dict[str, Any]] = None) -> Optional[EvidenceRecord]:
        # Check if context indicates a quote
        if context and context.get("is_quoted"):
            return EvidenceRecord(
                source="quoted",
                ref=context.get("source_ref", "user-input"),
                value=value,
            )
        return None

    def name(self) -> str:
        return "quoted"


class HumanAttributedProvider(EvidenceProvider):
    """Evidence for human-attributed language (Z2 decisions, user deadlines).

    Stub for v1.5: requires role tagging + speaker attribution.
    """

    def resolve(self, value: str, context: Optional[Dict[str, Any]] = None) -> Optional[EvidenceRecord]:
        # Check if context indicates human speaker
        if context and context.get("speaker") == "human":
            return EvidenceRecord(
                source="human-attributed",
                ref=context.get("speaker_id", "unknown"),
                value=value,
            )
        return None

    def name(self) -> str:
        return "human-attributed"
