"""Finding schema and JSON emission for P34-X temporal extractor."""

from dataclasses import dataclass, asdict, field
from typing import Optional, Dict, Any
from enum import Enum
import json


class TemporalCategory(str, Enum):
    """Contamination categories (subset of taxonomy for v1)."""
    F_DUR_EST = "F-DUR-EST"  # Duration estimate
    T_DATE_FUT = "T-DATE-FUT"  # Future date
    C_COMMIT_EXPLICIT = "C-COMMIT-EXPLICIT"  # Agent commissive


class TimexType(str, Enum):
    """TIMEX3 types (ISO 8601 extension)."""
    DATE = "DATE"
    TIME = "TIME"
    DURATION = "DURATION"
    SET = "SET"


class Severity(str, Enum):
    """Finding severity for v1."""
    ERROR = "ERROR"
    WARN = "WARN"
    INFO = "INFO"


@dataclass
class Span:
    """Character span in source text."""
    start: int
    end: int

    def to_dict(self):
        return asdict(self)


@dataclass
class EvidencePointer:
    """Reference to grounding evidence."""
    source: str  # "git" | "ledger" | "tool-transcript" | "quoted" | "human-attributed"
    ref: str  # Commit SHA, entry ID, trace ID, etc.
    signature: Optional[str] = None  # Optional digital signature (v1.5)
    attestation_time: Optional[str] = None  # RFC 3339 timestamp

    def to_dict(self):
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class SuggestedRewrite:
    """Event-driven rewrite template (6 fields)."""
    claim: str
    gating_authority: str  # "Z2" | "human" | null
    gating_condition: str
    expected_artifact: str
    evidence: str
    resource_cost: Optional[str] = None  # Omitted in v1.0; added in v1.5

    def to_dict(self):
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class TemporalFinding:
    """A single temporal finding (one span)."""
    span: Span
    text: str
    category: TemporalCategory
    timex3_type: TimexType
    normalized_value: Optional[str]
    speaker: str  # "agent" | "unknown" | "human" (v1.5)
    speaker_confidence: float  # 0.0–1.0
    grounded: bool
    evidence_pointer: Optional[EvidencePointer] = None
    exception_id: Optional[str] = None
    severity: Severity = Severity.WARN
    confidence: float = 0.5  # Recognizer heuristic score (0.0–1.0)

    def to_json(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        result = {
            "span": self.span.to_dict(),
            "text": self.text,
            "category": self.category.value,
            "timex3_type": self.timex3_type.value,
            "normalized_value": self.normalized_value,
            "speaker": self.speaker,
            "speaker_confidence": self.speaker_confidence,
            "grounded": self.grounded,
            "evidence_pointer": self.evidence_pointer.to_dict() if self.evidence_pointer else None,
            "exception_id": self.exception_id,
            "severity": self.severity.value,
            "confidence": self.confidence,
        }
        return result

    def to_json_string(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_json())


@dataclass
class ExtractionResult:
    """Result of extraction over a span of text."""
    findings: list[TemporalFinding] = field(default_factory=list)
    text: str = ""
    errors: list[str] = field(default_factory=list)  # Tool errors (not findings)

    def exit_code(self, fail_on: str = "error") -> int:
        """Compute exit code per lint convention.

        Args:
            fail_on: "error" or "warn" or "info"

        Returns:
            0 = clean (no findings at or above fail_on level)
            1 = findings at fail_on level
            2 = tool error
        """
        if self.errors:
            return 2

        severities = {Severity.ERROR: 3, Severity.WARN: 2, Severity.INFO: 1}
        fail_threshold = severities.get(Severity[fail_on.upper()], 2)

        for finding in self.findings:
            if severities[finding.severity] >= fail_threshold:
                return 1

        return 0

    def has_errors(self) -> bool:
        """True if any ERROR-level findings."""
        return any(f.severity == Severity.ERROR for f in self.findings)

    def has_warnings(self) -> bool:
        """True if any WARN-level findings."""
        return any(f.severity == Severity.WARN for f in self.findings)
