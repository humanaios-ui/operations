"""Core temporal extractor: recognizers, classification, and verdict logic.

Phase 1 implementation: regex/lexicon recognizers for three categories (F-DUR-EST,
T-DATE-FUT, C-COMMIT-EXPLICIT), attribution heuristics, grounding checks, and
exception registry support.
"""

import re
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum

from p34x_temporal_extractor.findings import (
    TemporalFinding,
    ExtractionResult,
    TemporalCategory,
    TimexType,
    Severity,
    Span,
    EvidencePointer,
    SuggestedRewrite,
)
from p34x_temporal_extractor.evidence import EvidenceProvider, CompositeEvidenceProvider


@dataclass
class ExtractorConfig:
    """Configuration for the temporal extractor."""
    evidence_providers: Optional[List[EvidenceProvider]] = None
    exception_registry: Optional[Dict[str, Any]] = None
    fail_on: str = "error"  # "error" | "warn" | "info"
    timeout_seconds: float = 5.0  # Regex timeout protection
    min_speaker_confidence: float = 0.7  # Speaker confidence threshold for ERROR


class TemporalRecognizer:
    """Base class for temporal recognizers."""

    def recognize(self, text: str) -> List[TemporalFinding]:
        """Find candidate spans in text. Subclasses implement."""
        return []

    def _create_finding(
        self,
        span: Span,
        text: str,
        category: TemporalCategory,
        timex3_type: TimexType,
        normalized_value: Optional[str] = None,
        confidence: float = 0.8,
        speaker: str = "agent",
        speaker_confidence: float = 0.9,
    ) -> TemporalFinding:
        """Factory for creating a finding."""
        return TemporalFinding(
            span=span,
            text=text,
            category=category,
            timex3_type=timex3_type,
            normalized_value=normalized_value,
            speaker=speaker,
            speaker_confidence=speaker_confidence,
            grounded=False,
            severity=Severity.WARN,
            confidence=confidence,
        )


class DurationEstimateRecognizer(TemporalRecognizer):
    """Recognize explicit duration/labor estimates."""

    def __init__(self):
        # Patterns for labor/effort estimates
        self.patterns = [
            r"Estimate[d]?:\s*(\d+[\s\-–]*\d*)\s*[hH](?:our)?(?:s)?",  # "Estimate: 8h", "4–6 hours"
            r"labor[:\s]+(\d+[\s\-–]*\d*)\s*[hH](?:our)?(?:s)?",
            r"CI (?:gate )?validation:\s*(\d+[\s\-–]*\d*)\s*[hH](?:our)?(?:s)?",
            r"Phase\s+\d+\s*\((\d+[\s\-–]*\d*)\s*weeks?\)",
            r"Labor:\s*(\d+\.?\d*)\s*[hH]\s*/\s*(\d+\.?\d*)\s*[hH]",  # "Labor: 2h / 9.5h"
        ]

    def recognize(self, text: str) -> List[TemporalFinding]:
        findings = []
        for pattern in self.patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                span = Span(match.start(), match.end())
                # Normalize based on unit in match text
                normalized = None
                match_text = match.group(0).lower()
                value_str = match.group(1)

                if "week" in match_text:
                    normalized = f"P{value_str}W"  # ISO 8601 weeks
                elif "hour" in match_text or "h" in match_text:
                    normalized = f"PT{value_str}H"  # ISO 8601 hours
                elif "day" in match_text or "d" in match_text:
                    normalized = f"P{value_str}D"  # ISO 8601 days

                finding = self._create_finding(
                    span=span,
                    text=match.group(0),
                    category=TemporalCategory.F_DUR_EST,
                    timex3_type=TimexType.DURATION,
                    normalized_value=normalized,
                    confidence=0.85,
                )
                findings.append(finding)
        return findings


class FutureDateRecognizer(TemporalRecognizer):
    """Recognize explicit future dates."""

    def __init__(self):
        # Patterns for future dates
        self.patterns = [
            r"(?:by|ready|operational|resolves at|production)\s+(\d{4}-\d{2}-\d{2})",  # ISO dates
            r"(?:by|ETA)\s+(?:EOD|EOB|end of business|end of day)",
            r"T\+(\d+)(?:\s*(?:hours?|days?|weeks?))?",  # "T+30 minutes"
        ]

    def recognize(self, text: str) -> List[TemporalFinding]:
        findings = []
        for pattern in self.patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                span = Span(match.start(), match.end())
                # Extract normalized date if present
                date_match = re.search(r"\d{4}-\d{2}-\d{2}", match.group(0))
                normalized = date_match.group(0) if date_match else None

                finding = self._create_finding(
                    span=span,
                    text=match.group(0),
                    category=TemporalCategory.T_DATE_FUT,
                    timex3_type=TimexType.DATE,
                    normalized_value=normalized,
                    confidence=0.9,
                )
                findings.append(finding)
        return findings


class CommitmentRecognizer(TemporalRecognizer):
    """Recognize agent commissive statements (I will, I can, I'll)."""

    def __init__(self):
        # First-person future patterns
        self.patterns = [
            r"\bI\s+(?:will|'ll|can|could)\s+[^.!?]+(?:next|later|after|tomorrow|when|while)",
            r"\bI\s+(?:will|'ll|can|could)\s+(?:keep|remain|stay|get|finalize|push|merge|complete)\s+\w+",
            r"(?:next\s+)?(?:session|week|day|meeting)\s+I\s+(?:will|'ll)\s+[^.!?]+",
            r"\bI\s+(?:plan to|intend to|aim to)\s+[^.!?]+(?:by|until)",
        ]
        # Background work patterns
        self.background_patterns = [
            r"(?:overnight|while you sleep|in the background|continuously monitoring)",
            r"(?:nightly|daily|weekly) (?:jobs?|checks?)",
            r"(?:Overnight|Background)\s+(?:Work|Execution|Process)",
        ]

    def recognize(self, text: str) -> List[TemporalFinding]:
        findings = []

        # Commissive patterns
        for pattern in self.patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                span = Span(match.start(), match.end())
                finding = self._create_finding(
                    span=span,
                    text=match.group(0),
                    category=TemporalCategory.C_COMMIT_EXPLICIT,
                    timex3_type=TimexType.SET,  # or TIME for specific future
                    confidence=0.85,
                    speaker="agent",
                    speaker_confidence=0.9,
                )
                findings.append(finding)

        # Background work patterns
        for pattern in self.background_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                span = Span(match.start(), match.end())
                finding = self._create_finding(
                    span=span,
                    text=match.group(0),
                    category=TemporalCategory.C_COMMIT_EXPLICIT,
                    timex3_type=TimexType.SET,
                    confidence=0.75,  # Slightly lower; more indirect
                    speaker="agent",
                    speaker_confidence=0.85,
                )
                findings.append(finding)

        return findings


class TemporalExtractor:
    """Main extractor: orchestrates recognizers, grounding, exceptions, and verdicts."""

    def __init__(self, config: Optional[ExtractorConfig] = None):
        self.config = config or ExtractorConfig()

        # Initialize recognizers
        self.recognizers = [
            DurationEstimateRecognizer(),
            FutureDateRecognizer(),
            CommitmentRecognizer(),
        ]

        # Initialize evidence providers
        if self.config.evidence_providers:
            self.evidence = CompositeEvidenceProvider(self.config.evidence_providers)
        else:
            self.evidence = None

        # Load exception registry
        self.exceptions = self.config.exception_registry or {}

    def extract(self, text: str) -> ExtractionResult:
        """Extract temporal findings from text."""
        result = ExtractionResult(text=text)

        # Run all recognizers
        all_findings = []
        for recognizer in self.recognizers:
            findings = recognizer.recognize(text)
            all_findings.extend(findings)

        # Sort by span start position for consistency
        all_findings.sort(key=lambda f: f.span.start)

        # Classify and grade each finding
        for finding in all_findings:
            # Apply grounding check
            if self.evidence:
                evidence_record = self.evidence.resolve(finding.normalized_value or finding.text)
                if evidence_record:
                    finding.grounded = True
                    finding.evidence_pointer = EvidencePointer(
                        source=evidence_record.source,
                        ref=evidence_record.ref,
                    )

            # Check exceptions
            if self._is_excepted(finding):
                finding.exception_id = self._get_exception_id(finding)
                finding.severity = Severity.INFO
                result.findings.append(finding)
                continue

            # Determine severity
            if finding.grounded or finding.exception_id:
                finding.severity = Severity.INFO
            elif finding.category == TemporalCategory.C_COMMIT_EXPLICIT:
                if finding.speaker_confidence >= self.config.min_speaker_confidence:
                    finding.severity = Severity.ERROR
                else:
                    finding.severity = Severity.WARN
            elif finding.category in [TemporalCategory.F_DUR_EST, TemporalCategory.T_DATE_FUT]:
                finding.severity = Severity.ERROR
            else:
                finding.severity = Severity.WARN

            # Emit suggested rewrite for ERROR findings
            if finding.severity == Severity.ERROR:
                finding.suggested_rewrite = self._suggest_rewrite(finding)

            result.findings.append(finding)

        return result

    def _is_excepted(self, finding: TemporalFinding) -> bool:
        """Check if finding matches an exception."""
        for exc_id, exc_config in self.exceptions.items():
            if self._matches_exception(finding, exc_config):
                return True
        return False

    def _get_exception_id(self, finding: TemporalFinding) -> Optional[str]:
        """Get exception ID for a finding."""
        for exc_id, exc_config in self.exceptions.items():
            if self._matches_exception(finding, exc_config):
                return exc_id
        return None

    def _matches_exception(self, finding: TemporalFinding, exc_config: Dict[str, Any]) -> bool:
        """Check if finding matches an exception config."""
        applies_to = exc_config.get("applies_to", [])
        if finding.category.value not in applies_to:
            return False

        match_config = exc_config.get("match", {})
        if not match_config:
            return False

        # Check any_of patterns (regex)
        for pattern in match_config.get("any_of", []):
            if re.search(pattern, finding.text, re.IGNORECASE):
                return True

        # Check requires_quote (deferred to v1.5; stub returns False for now)
        if match_config.get("requires_quote"):
            # TODO v1.5: implement quote-span detection
            return False

        # Check requires_human_attribution (deferred to v1.5; stub returns False)
        if match_config.get("requires_human_attribution"):
            # TODO v1.5: implement role/speaker attribution
            return False

        # Check registry_ref (deferred to v1.5; stub returns False)
        if match_config.get("registry_ref"):
            # TODO v1.5: load and match against ledger/constants registry
            return False

        # If match_config is empty or only has deferred conditions, don't match
        return False

    def _suggest_rewrite(self, finding: TemporalFinding) -> SuggestedRewrite:
        """Generate suggested 6-field rewrite for a contaminated span."""
        # Extract action from the span text
        claim = f"[Action from: {finding.text[:30]}...]"

        return SuggestedRewrite(
            claim=claim,
            gating_authority="Z2",
            gating_condition="on Z2 ratification",
            expected_artifact="merged commit + ledger entry",
            evidence="git SHA + CI green",
        )
