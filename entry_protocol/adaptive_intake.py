"""Adaptive START_HERE intake primitives.

This module accepts heterogeneous human/AI returns without requiring a fixed
HumanAIOS response schema. It is intentionally non-enforcing and privacy-minimal:
it classifies interaction form and evidence state but does not persist raw email,
resolve identities, retrieve remote links, or grant authority.

HumanAIOS adapts collection to the receiving collaboration; telemetry records the
adaptation rather than forcing the participant into a HumanAIOS-specific format.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
import re
from typing import Iterable, Sequence
from urllib.parse import urlparse


class ReturnForm(str, Enum):
    QUESTION = "QUESTION"
    OBSERVATION = "OBSERVATION"
    CHALLENGE = "CHALLENGE"
    PASTED_AI_OUTPUT = "PASTED_AI_OUTPUT"
    SHARED_AI_LINK = "SHARED_AI_LINK"
    FILE = "FILE"
    NATURAL_RETURN = "NATURAL_RETURN"


class EvidenceState(str, Enum):
    LINK_RECEIVED = "LINK_RECEIVED"
    CONTENT_CAPTURED = "CONTENT_CAPTURED"
    CONTENT_VERIFIED = "CONTENT_VERIFIED"


AI_HOST_HINTS = (
    "perplexity.ai",
    "chatgpt.com",
    "claude.ai",
    "gemini.google.com",
    "grok.com",
    "x.com/i/grok",
)

AI_OUTPUT_HINTS = (
    "ai_used:",
    "ai output",
    "begin ai output",
    "independent review result",
    "model:",
)

CHALLENGE_HINTS = (
    "challenge:",
    "falsifier",
    "disprove",
    "prove wrong",
    "test this claim",
)

OBSERVATION_HINTS = (
    "observation:",
    "i noticed",
    "we noticed",
    "finding:",
)

CORRECTION_HINTS = (
    "correction",
    "i forgot",
    "forgot to include",
    "missing link",
    "here is the link",
    "follow-up",
    "follow up",
)


@dataclass(frozen=True)
class IntakeObservation:
    """Privacy-minimized observation of one incoming message."""

    return_forms: tuple[str, ...]
    links: tuple[str, ...] = ()
    ai_link_hosts: tuple[str, ...] = ()
    attachment_count: int = 0
    possible_correction: bool = False
    raw_content_retained: bool = False
    fixed_schema_required: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AdaptiveEntryEvent:
    """Thread-local event assembled across one or more natural returns."""

    event_ref: str
    observations: list[IntakeObservation] = field(default_factory=list)
    evidence_states: list[str] = field(default_factory=list)
    adaptations: list[str] = field(default_factory=list)

    def append(self, observation: IntakeObservation) -> None:
        self.observations.append(observation)
        for form in observation.return_forms:
            adaptation = f"ACCEPT_RETURN_FORM:{form}"
            if adaptation not in self.adaptations:
                self.adaptations.append(adaptation)
        if observation.possible_correction:
            self.adaptations.append("EXTEND_PRIOR_EVENT_WITH_CORRECTION")
        if ReturnForm.SHARED_AI_LINK.value in observation.return_forms:
            self.mark_evidence(EvidenceState.LINK_RECEIVED)

    def mark_evidence(self, state: EvidenceState) -> None:
        """Advance evidence state monotonically; never imply later states."""

        order = [
            EvidenceState.LINK_RECEIVED.value,
            EvidenceState.CONTENT_CAPTURED.value,
            EvidenceState.CONTENT_VERIFIED.value,
        ]
        target = order.index(state.value)
        if not self.evidence_states:
            if state is not EvidenceState.LINK_RECEIVED:
                raise ValueError("content cannot be captured/verified before a link is received")
            self.evidence_states.append(state.value)
            return

        current = order.index(self.evidence_states[-1])
        if target < current:
            raise ValueError("evidence state cannot move backward")
        if target > current + 1:
            raise ValueError("evidence state cannot skip an intermediate state")
        if target == current:
            return
        self.evidence_states.append(state.value)

    def telemetry(self) -> dict:
        """Return protocol telemetry without raw message content or identity."""

        forms: list[str] = []
        hosts: list[str] = []
        corrections = 0
        attachments = 0
        for obs in self.observations:
            attachments += obs.attachment_count
            corrections += int(obs.possible_correction)
            for form in obs.return_forms:
                if form not in forms:
                    forms.append(form)
            for host in obs.ai_link_hosts:
                if host not in hosts:
                    hosts.append(host)

        return {
            "event_ref": self.event_ref,
            "message_count": len(self.observations),
            "return_forms": forms,
            "ai_link_hosts": hosts,
            "attachment_count": attachments,
            "correction_count": corrections,
            "evidence_states": list(self.evidence_states),
            "adaptations": list(self.adaptations),
            "raw_content_retained": False,
            "participant_identity_profiled": False,
        }


def _extract_links(text: str) -> tuple[str, ...]:
    return tuple(re.findall(r"https?://[^\s<>]+", text or ""))


def _ai_hosts(links: Iterable[str]) -> tuple[str, ...]:
    hosts: list[str] = []
    for link in links:
        host = (urlparse(link).hostname or "").lower()
        full = link.lower()
        if any(hint in host or hint in full for hint in AI_HOST_HINTS):
            if host and host not in hosts:
                hosts.append(host)
    return tuple(hosts)


def observe_return(
    text: str | None,
    *,
    attachment_count: int = 0,
) -> IntakeObservation:
    """Classify a natural return without requiring labels or retaining raw text.

    Multiple forms may be present at once. Unknown/ordinary replies are accepted
    as NATURAL_RETURN rather than rejected.
    """

    body = (text or "").strip()
    lowered = body.lower()
    links = _extract_links(body)
    ai_hosts = _ai_hosts(links)

    forms: list[ReturnForm] = []

    if "?" in body or lowered.startswith(("question:", "why ", "how ", "what ", "can ")):
        forms.append(ReturnForm.QUESTION)
    if any(hint in lowered for hint in OBSERVATION_HINTS):
        forms.append(ReturnForm.OBSERVATION)
    if any(hint in lowered for hint in CHALLENGE_HINTS):
        forms.append(ReturnForm.CHALLENGE)
    if any(hint in lowered for hint in AI_OUTPUT_HINTS):
        forms.append(ReturnForm.PASTED_AI_OUTPUT)
    if ai_hosts:
        forms.append(ReturnForm.SHARED_AI_LINK)
    if attachment_count > 0:
        forms.append(ReturnForm.FILE)

    if not forms:
        forms.append(ReturnForm.NATURAL_RETURN)

    possible_correction = any(hint in lowered for hint in CORRECTION_HINTS)

    return IntakeObservation(
        return_forms=tuple(form.value for form in forms),
        links=links,
        ai_link_hosts=ai_hosts,
        attachment_count=max(0, int(attachment_count)),
        possible_correction=possible_correction,
    )


def build_event(
    event_ref: str,
    observations: Sequence[IntakeObservation],
) -> AdaptiveEntryEvent:
    if not event_ref or not event_ref.strip():
        raise ValueError("event_ref is required")
    event = AdaptiveEntryEvent(event_ref=event_ref.strip())
    for observation in observations:
        event.append(observation)
    return event
