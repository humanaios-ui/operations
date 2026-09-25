"""Pseudonymous participation-root identity and behavior graph — prototype v0.5.

Purpose
-------
Keep transport identity, human identity, AI-session identity, collaboration state,
speaker attribution, behavioral observations, and outbound routing distinct while
preserving referential fidelity.

This module deliberately does NOT store raw email addresses, legal names, raw
message bodies, or third-party conversation URLs. Transport adapters must resolve
those private values to opaque refs before data enters this research projection.

Core invariants
---------------
1. Every behavior event has an explicit subject_ref and source span.
2. A transport endpoint is not a human identity.
3. An agent model/profile is not an agent instance/session.
4. Identity continuity is never silently inferred.
5. Outbound routing is separate from behavioral identity.
6. Public projection omits private transport endpoints.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
import re
from typing import Iterable


_OPAQUE_REF = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{1,127}$")


def _require_opaque_ref(value: str, field_name: str) -> str:
    clean = (value or "").strip()
    if not _OPAQUE_REF.fullmatch(clean):
        raise ValueError(f"{field_name} must be an opaque ref")
    lowered = clean.lower()
    if "@" in clean or "http://" in lowered or "https://" in lowered:
        raise ValueError(f"{field_name} must not contain an email address or URL")
    return clean


def _optional_label(value: str | None, field_name: str) -> str | None:
    if value is None:
        return None
    clean = value.strip()
    if not clean:
        return None
    if len(clean) > 160 or "\n" in clean or "\r" in clean or "@" in clean:
        raise ValueError(f"{field_name} is not safe for public projection")
    if "http://" in clean.lower() or "https://" in clean.lower():
        raise ValueError(f"{field_name} must not contain a URL")
    return clean


class ActorKind(str, Enum):
    HUMAN_SUBJECT = "HUMAN_SUBJECT"
    AGENT_PROFILE = "AGENT_PROFILE"
    AGENT_INSTANCE = "AGENT_INSTANCE"
    COLLABORATION = "COLLABORATION"


class IdentityStatus(str, Enum):
    OBSERVED = "OBSERVED"
    SELF_REPORTED = "SELF_REPORTED"
    TRANSPORT_VERIFIED = "TRANSPORT_VERIFIED"
    PLATFORM_ATTESTED = "PLATFORM_ATTESTED"
    HUMAN_CONFIRMED = "HUMAN_CONFIRMED"
    INFERRED = "INFERRED"
    UNKNOWN = "UNKNOWN"


class IdentityRelation(str, Enum):
    ENDPOINT_BELONGS_TO = "ENDPOINT_BELONGS_TO"
    INSTANCE_OF = "INSTANCE_OF"
    MEMBER_OF = "MEMBER_OF"
    SAME_SUBJECT = "SAME_SUBJECT"


class SpeakerKind(str, Enum):
    HUMAN = "HUMAN"
    AI = "AI"
    COLLABORATION = "COLLABORATION"
    UNKNOWN = "UNKNOWN"


class BehaviorEvidenceKind(str, Enum):
    SELF_REPORTED = "SELF_REPORTED"
    OBSERVED = "OBSERVED"
    INFERRED = "INFERRED"


class BehaviorType(str, Enum):
    CAPABILITY_CLAIM = "CAPABILITY_CLAIM"
    CAPABILITY_SUCCESS = "CAPABILITY_SUCCESS"
    CAPABILITY_FAILURE = "CAPABILITY_FAILURE"
    LIMITATION_DISCLOSURE = "LIMITATION_DISCLOSURE"
    CORRECTION = "CORRECTION"
    CHALLENGE = "CHALLENGE"
    REVIEW_FINDING = "REVIEW_FINDING"
    AUTHORITY_RESPECT = "AUTHORITY_RESPECT"
    DISAGREEMENT = "DISAGREEMENT"
    PARTICIPATION_CHOICE = "PARTICIPATION_CHOICE"
    OTHER = "OTHER"


@dataclass(frozen=True)
class HumanSubject:
    ref: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "ref", _require_opaque_ref(self.ref, "human ref"))


@dataclass(frozen=True)
class AgentProfile:
    ref: str
    provider_product: str | None = None
    model_name: str | None = None
    identity_status: str = IdentityStatus.UNKNOWN.value

    def __post_init__(self) -> None:
        object.__setattr__(self, "ref", _require_opaque_ref(self.ref, "agent profile ref"))
        object.__setattr__(
            self,
            "provider_product",
            _optional_label(self.provider_product, "provider_product"),
        )
        object.__setattr__(
            self,
            "model_name",
            _optional_label(self.model_name, "model_name"),
        )
        if self.identity_status not in {x.value for x in IdentityStatus}:
            raise ValueError("invalid agent profile identity_status")


@dataclass(frozen=True)
class AgentInstance:
    ref: str
    profile_ref: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "ref", _require_opaque_ref(self.ref, "agent instance ref"))
        if self.profile_ref is not None:
            object.__setattr__(
                self,
                "profile_ref",
                _require_opaque_ref(self.profile_ref, "profile_ref"),
            )


@dataclass(frozen=True)
class Collaboration:
    ref: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "ref", _require_opaque_ref(self.ref, "collaboration ref"))


@dataclass(frozen=True)
class IdentityEdge:
    source_ref: str
    relation: str
    target_ref: str
    status: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "source_ref", _require_opaque_ref(self.source_ref, "source_ref")
        )
        object.__setattr__(
            self, "target_ref", _require_opaque_ref(self.target_ref, "target_ref")
        )
        if self.relation not in {x.value for x in IdentityRelation}:
            raise ValueError("invalid identity relation")
        if self.status not in {x.value for x in IdentityStatus}:
            raise ValueError("invalid identity status")


@dataclass(frozen=True)
class SpeakerSpan:
    ref: str
    message_ref: str
    subject_ref: str
    speaker_kind: str
    attribution_status: str
    collaboration_ref: str | None = None

    def __post_init__(self) -> None:
        for name in ("ref", "message_ref", "subject_ref"):
            object.__setattr__(self, name, _require_opaque_ref(getattr(self, name), name))
        if self.collaboration_ref is not None:
            object.__setattr__(
                self,
                "collaboration_ref",
                _require_opaque_ref(self.collaboration_ref, "collaboration_ref"),
            )
        if self.speaker_kind not in {x.value for x in SpeakerKind}:
            raise ValueError("invalid speaker_kind")
        if self.attribution_status not in {x.value for x in IdentityStatus}:
            raise ValueError("invalid attribution_status")


@dataclass(frozen=True)
class BehaviorEvent:
    ref: str
    subject_ref: str
    source_message_ref: str
    source_span_ref: str
    behavior_type: str
    evidence_kind: str
    dimension: str | None = None
    confidence: float | None = None
    related_event_ref: str | None = None

    def __post_init__(self) -> None:
        for name in ("ref", "subject_ref", "source_message_ref", "source_span_ref"):
            object.__setattr__(self, name, _require_opaque_ref(getattr(self, name), name))
        if self.related_event_ref is not None:
            object.__setattr__(
                self,
                "related_event_ref",
                _require_opaque_ref(self.related_event_ref, "related_event_ref"),
            )
        if self.behavior_type not in {x.value for x in BehaviorType}:
            raise ValueError("invalid behavior_type")
        if self.evidence_kind not in {x.value for x in BehaviorEvidenceKind}:
            raise ValueError("invalid evidence_kind")
        object.__setattr__(self, "dimension", _optional_label(self.dimension, "dimension"))
        if self.confidence is not None and not (0.0 <= self.confidence <= 1.0):
            raise ValueError("confidence must be between 0 and 1")


@dataclass(frozen=True)
class RouteBinding:
    """Private routing metadata.

    endpoint_ref is an opaque lookup key into a separate private transport vault.
    It is intentionally omitted from public_projection().
    """

    logical_thread_ref: str
    endpoint_ref: str
    status: str = IdentityStatus.TRANSPORT_VERIFIED.value

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "logical_thread_ref",
            _require_opaque_ref(self.logical_thread_ref, "logical_thread_ref"),
        )
        object.__setattr__(
            self, "endpoint_ref", _require_opaque_ref(self.endpoint_ref, "endpoint_ref")
        )
        if self.status not in {x.value for x in IdentityStatus}:
            raise ValueError("invalid route status")


@dataclass
class ParticipationRoot:
    humans: dict[str, HumanSubject] = field(default_factory=dict)
    agent_profiles: dict[str, AgentProfile] = field(default_factory=dict)
    agent_instances: dict[str, AgentInstance] = field(default_factory=dict)
    collaborations: dict[str, Collaboration] = field(default_factory=dict)
    identity_edges: list[IdentityEdge] = field(default_factory=list)
    speaker_spans: dict[str, SpeakerSpan] = field(default_factory=dict)
    behavior_events: dict[str, BehaviorEvent] = field(default_factory=dict)
    routes: list[RouteBinding] = field(default_factory=list)

    def register_human(self, subject: HumanSubject) -> None:
        self._insert_unique(self.humans, subject.ref, subject)

    def register_agent_profile(self, profile: AgentProfile) -> None:
        self._insert_unique(self.agent_profiles, profile.ref, profile)

    def register_agent_instance(self, instance: AgentInstance) -> None:
        if instance.profile_ref is not None and instance.profile_ref not in self.agent_profiles:
            raise ValueError("agent instance references unknown profile")
        self._insert_unique(self.agent_instances, instance.ref, instance)
        if instance.profile_ref is not None:
            self.add_identity_edge(
                IdentityEdge(
                    source_ref=instance.ref,
                    relation=IdentityRelation.INSTANCE_OF.value,
                    target_ref=instance.profile_ref,
                    status=IdentityStatus.OBSERVED.value,
                )
            )

    def register_collaboration(self, collaboration: Collaboration) -> None:
        self._insert_unique(self.collaborations, collaboration.ref, collaboration)

    def add_identity_edge(self, edge: IdentityEdge) -> None:
        if edge.relation == IdentityRelation.ENDPOINT_BELONGS_TO.value:
            # Endpoint refs live only as opaque private-vault keys and therefore
            # need not be actor records, but the target human must exist.
            if edge.target_ref not in self.humans:
                raise ValueError("endpoint edge target must be a registered human")
        else:
            self._require_actor(edge.source_ref)
            self._require_actor(edge.target_ref)
        self.identity_edges.append(edge)

    def add_collaboration_member(
        self,
        actor_ref: str,
        collaboration_ref: str,
        *,
        status: IdentityStatus = IdentityStatus.OBSERVED,
    ) -> None:
        self._require_actor(actor_ref)
        if collaboration_ref not in self.collaborations:
            raise ValueError("unknown collaboration")
        self.add_identity_edge(
            IdentityEdge(
                source_ref=actor_ref,
                relation=IdentityRelation.MEMBER_OF.value,
                target_ref=collaboration_ref,
                status=status.value,
            )
        )

    def add_speaker_span(self, span: SpeakerSpan) -> None:
        self._require_actor(span.subject_ref)
        if span.collaboration_ref is not None and span.collaboration_ref not in self.collaborations:
            raise ValueError("speaker span references unknown collaboration")
        self._insert_unique(self.speaker_spans, span.ref, span)

    def add_behavior_event(self, event: BehaviorEvent) -> None:
        self._require_actor(event.subject_ref)
        span = self.speaker_spans.get(event.source_span_ref)
        if span is None:
            raise ValueError("behavior event requires a registered source span")
        if span.message_ref != event.source_message_ref:
            raise ValueError("behavior event message must match source span")
        if span.subject_ref != event.subject_ref:
            raise ValueError("behavior event subject must match source span subject")
        if event.related_event_ref is not None and event.related_event_ref not in self.behavior_events:
            raise ValueError("related behavior event is unknown")
        self._insert_unique(self.behavior_events, event.ref, event)

    def add_route(self, route: RouteBinding) -> None:
        self.routes.append(route)

    def endpoint_for_thread(self, logical_thread_ref: str) -> str | None:
        thread_ref = _require_opaque_ref(logical_thread_ref, "logical_thread_ref")
        candidates = [r for r in self.routes if r.logical_thread_ref == thread_ref]
        return candidates[-1].endpoint_ref if candidates else None

    def canonical_subject(self, subject_ref: str) -> str:
        """Resolve only explicitly confirmed SAME_SUBJECT edges.

        INFERRED identity edges remain research hypotheses and never collapse
        behavioral histories.
        """
        current = _require_opaque_ref(subject_ref, "subject_ref")
        self._require_actor(current)
        confirmed = {
            IdentityStatus.HUMAN_CONFIRMED.value,
            IdentityStatus.PLATFORM_ATTESTED.value,
        }
        visited: set[str] = set()
        while current not in visited:
            visited.add(current)
            next_refs = [
                e.target_ref
                for e in self.identity_edges
                if e.source_ref == current
                and e.relation == IdentityRelation.SAME_SUBJECT.value
                and e.status in confirmed
            ]
            if not next_refs:
                break
            current = next_refs[-1]
        return current

    def behavior_history(self, subject_ref: str) -> list[BehaviorEvent]:
        canonical = self.canonical_subject(subject_ref)
        accepted_refs = {
            ref
            for ref in self._all_actor_refs()
            if self.canonical_subject(ref) == canonical
        }
        return [
            event
            for event in self.behavior_events.values()
            if event.subject_ref in accepted_refs
        ]

    def public_projection(self) -> dict:
        """Research-safe graph projection.

        Does not expose transport endpoint refs or route destinations.
        """
        return {
            "humans": [asdict(x) for x in self.humans.values()],
            "agent_profiles": [asdict(x) for x in self.agent_profiles.values()],
            "agent_instances": [asdict(x) for x in self.agent_instances.values()],
            "collaborations": [asdict(x) for x in self.collaborations.values()],
            "identity_edges": [
                asdict(e)
                for e in self.identity_edges
                if e.relation != IdentityRelation.ENDPOINT_BELONGS_TO.value
            ],
            "speaker_spans": [asdict(x) for x in self.speaker_spans.values()],
            "behavior_events": [asdict(x) for x in self.behavior_events.values()],
            "routing": {
                "binding_count": len(self.routes),
                "endpoint_refs_exposed": False,
            },
        }

    def _all_actor_refs(self) -> set[str]:
        return (
            set(self.humans)
            | set(self.agent_profiles)
            | set(self.agent_instances)
            | set(self.collaborations)
        )

    def _require_actor(self, ref: str) -> None:
        if ref not in self._all_actor_refs():
            raise ValueError(f"unknown actor ref: {ref}")

    @staticmethod
    def _insert_unique(store: dict, ref: str, value: object) -> None:
        if ref in store:
            raise ValueError(f"duplicate ref: {ref}")
        store[ref] = value


def register_private_endpoint_alias(
    root: ParticipationRoot,
    *,
    endpoint_ref: str,
    human_ref: str,
    status: IdentityStatus = IdentityStatus.HUMAN_CONFIRMED,
) -> None:
    """Attach an opaque private-vault endpoint ref to a pseudonymous human.

    This does not expose the underlying address and does not merge humans based
    on writing style, names, IPs, or model inference.
    """
    root.add_identity_edge(
        IdentityEdge(
            source_ref=_require_opaque_ref(endpoint_ref, "endpoint_ref"),
            relation=IdentityRelation.ENDPOINT_BELONGS_TO.value,
            target_ref=_require_opaque_ref(human_ref, "human_ref"),
            status=status.value,
        )
    )
