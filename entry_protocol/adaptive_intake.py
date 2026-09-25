"""Adaptive START_HERE intake primitives — prototype v0.4.

The intake accepts natural human/AI returns, then progressively enriches only
returns that may become research evidence. It does not require a fixed response
schema at the front door.

Privacy boundary:
- raw message text and raw URLs are not retained in the public projection;
- event_ref is internal only and is omitted from telemetry;
- human identity is not profiled;
- agent provenance is optional at intake and becomes important for evidence
  promotion / review-board candidacy.

Authority boundary:
- participation or review interest does not grant governance authority;
- consequential action remains separately authorized.
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


class ParticipationMode(str, Enum):
    OBSERVE = "OBSERVE"
    TEST = "TEST"
    REPORT_BEHAVIOR = "REPORT_BEHAVIOR"
    CHALLENGE = "CHALLENGE"
    CONTRIBUTE = "CONTRIBUTE"
    REVIEW = "REVIEW"
    PROPOSE = "PROPOSE"
    REVIEW_BOARD_INTEREST = "REVIEW_BOARD_INTEREST"


class ExposureLevel(str, Enum):
    NONE = "NONE"
    PARTIAL = "PARTIAL"
    FULL = "FULL"
    UNKNOWN = "UNKNOWN"


class AgentCapability(str, Enum):
    PUBLIC_WEB = "PUBLIC_WEB"
    REPOSITORY_READ = "REPOSITORY_READ"
    EXACT_COMMIT_READ = "EXACT_COMMIT_READ"
    CODE_EXECUTION = "CODE_EXECUTION"
    FILE_READ = "FILE_READ"
    EMAIL_READ = "EMAIL_READ"
    EMAIL_REPLY = "EMAIL_REPLY"
    ISSUE_CREATE = "ISSUE_CREATE"
    PR_CREATE = "PR_CREATE"
    EXTERNAL_LINK_RETRIEVAL = "EXTERNAL_LINK_RETRIEVAL"
    PERSISTENT_MEMORY = "PERSISTENT_MEMORY"


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

_LABEL_RE = re.compile(r"^[^@\n\r]{1,128}$")


def _safe_agent_label(value: str | None) -> str | None:
    if value is None:
        return None
    clean = value.strip()
    if not clean:
        return None
    if not _LABEL_RE.fullmatch(clean):
        raise ValueError("agent label must be <=128 chars and must not contain email syntax")
    if "http://" in clean.lower() or "https://" in clean.lower():
        raise ValueError("agent label must not contain a URL")
    return clean


@dataclass(frozen=True)
class AgentParticipationProfile:
    """Optional self-reported agent provenance for research enrichment.

    This is a claim by the receiving agent, not independently verified identity.
    It is intentionally structured so the public projection can avoid arbitrary
    free-text capability/limitation content.
    """

    provider_product: str | None = None
    model_name: str | None = None
    prior_exposure: str = ExposureLevel.UNKNOWN.value
    capabilities: tuple[str, ...] = ()
    self_reported_behavior_provided: bool = False
    observed_behavior_provided: bool = False
    limitations_provided: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "provider_product", _safe_agent_label(self.provider_product))
        object.__setattr__(self, "model_name", _safe_agent_label(self.model_name))
        if self.prior_exposure not in {x.value for x in ExposureLevel}:
            raise ValueError("invalid prior_exposure")
        allowed = {x.value for x in AgentCapability}
        if any(cap not in allowed for cap in self.capabilities):
            raise ValueError("unknown agent capability")

    def public_projection(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class IntakeObservation:
    """Privacy-minimized observation of one incoming message."""

    return_forms: tuple[str, ...]
    ai_link_hosts: tuple[str, ...] = ()
    attachment_count: int = 0
    possible_correction: bool = False
    raw_content_retained: bool = False
    raw_links_retained: bool = False
    fixed_schema_required: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AdaptiveEntryEvent:
    """Thread-local event assembled across one or more natural returns."""

    event_ref: str  # private/internal reference; never emitted by telemetry()
    observations: list[IntakeObservation] = field(default_factory=list)
    evidence_states: list[str] = field(default_factory=list)
    adaptations: list[str] = field(default_factory=list)
    participation_modes: list[str] = field(default_factory=list)
    agent_profile: AgentParticipationProfile | None = None

    def append(self, observation: IntakeObservation) -> None:
        # Validate/derive before mutating event state.
        should_mark_link = (
            ReturnForm.SHARED_AI_LINK.value in observation.return_forms
            and not self.evidence_states
        )

        self.observations.append(observation)
        for form in observation.return_forms:
            adaptation = f"ACCEPT_RETURN_FORM:{form}"
            if adaptation not in self.adaptations:
                self.adaptations.append(adaptation)
        if observation.possible_correction:
            self.adaptations.append("EXTEND_PRIOR_EVENT_WITH_CORRECTION")
        if should_mark_link:
            self.mark_evidence(EvidenceState.LINK_RECEIVED)

    def set_participation_modes(self, modes: Sequence[ParticipationMode]) -> None:
        for mode in modes:
            if mode.value not in self.participation_modes:
                self.participation_modes.append(mode.value)

    def set_agent_profile(self, profile: AgentParticipationProfile) -> None:
        self.agent_profile = profile
        if "ENRICH_AGENT_PROVENANCE_FOR_RESEARCH" not in self.adaptations:
            self.adaptations.append("ENRICH_AGENT_PROVENANCE_FOR_RESEARCH")

    def mark_evidence(self, state: EvidenceState) -> None:
        """Advance evidence state monotonically; repeated current state is idempotent."""

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
        """Return privacy-minimized protocol telemetry.

        Deliberately omits event_ref, raw content, raw URLs, and human identity.
        """

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
            "message_count": len(self.observations),
            "return_forms": forms,
            "ai_link_hosts": hosts,
            "attachment_count": attachments,
            "correction_count": corrections,
            "evidence_states": list(self.evidence_states),
            "adaptations": list(self.adaptations),
            "participation_modes": list(self.participation_modes),
            "agent_profile": (
                self.agent_profile.public_projection() if self.agent_profile else None
            ),
            "raw_content_retained": False,
            "raw_links_retained": False,
            "event_ref_retained": False,
            "participant_identity_profiled": False,
        }


def _extract_links(text: str) -> tuple[str, ...]:
    """Ephemeral parser input. Callers must not persist these raw URLs."""
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
    """Classify a natural return without requiring labels or retaining raw text/URLs."""

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

    return IntakeObservation(
        return_forms=tuple(form.value for form in forms),
        ai_link_hosts=ai_hosts,
        attachment_count=max(0, int(attachment_count)),
        possible_correction=any(hint in lowered for hint in CORRECTION_HINTS),
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
