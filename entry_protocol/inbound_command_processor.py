"""Inbound email command processor for the HumanAIOS digest/message-board surface.

Prototype only: this module parses already-segmented human-authored text into
bounded control events. It never executes external actions.

Privacy boundary:
- callers must keep raw email bodies, Gmail IDs, mailbox URLs, endpoint refs,
  and private identities in the private transport/evidence layer;
- public_projection() emits only bounded operational metadata.

Authority boundary:
- thread bookkeeping is Z1/reversible;
- Z2/Z3 language is held for explicit human authority and never executed here.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from difflib import SequenceMatcher
import re
from typing import Mapping


class ActorKind(str, Enum):
    HUMAN = "HUMAN"
    AGENT = "AGENT"
    UNKNOWN = "UNKNOWN"


class CommandKind(str, Enum):
    BEGIN_THREAD = "BEGIN_THREAD"
    UPDATE_THREAD = "UPDATE_THREAD"
    PAUSE_THREAD = "PAUSE_THREAD"
    RESUME_THREAD = "RESUME_THREAD"
    CLOSE_THREAD = "CLOSE_THREAD"
    STATUS = "STATUS"
    NATURAL_NOTE = "NATURAL_NOTE"
    UNKNOWN = "UNKNOWN"


class ThreadState(str, Enum):
    NEW = "NEW"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    CLOSED = "CLOSED"


class ResolutionState(str, Enum):
    RESOLVED = "RESOLVED"
    NEEDS_HUMAN = "NEEDS_HUMAN"
    NO_TARGET = "NO_TARGET"


class AuthorityLevel(str, Enum):
    Z1 = "Z1"
    Z2 = "Z2"
    Z3 = "Z3"


_QUOTED_REPLY_MARKERS = (
    re.compile(r"(?im)^\s*On .{1,200} wrote:\s*$"),
    re.compile(r"(?im)^\s*From:\s+.+$"),
    re.compile(r"(?im)^\s*-----Original Message-----\s*$"),
)

_SIGNATURE_MARKERS = (
    re.compile(r"(?im)^\s*--\s*$"),
    re.compile(r"(?im)^\s*Carly Anderson \(Night\)\s*$"),
)

_COMMAND_PATTERNS = (
    (
        CommandKind.BEGIN_THREAD,
        re.compile(
            r"\b(?:begin|start|open|activate|create)\b.{0,28}\bthread\b"
            r"|\bbegin\b.{0,20}\bactivate\b",
            re.I,
        ),
    ),
    (
        CommandKind.PAUSE_THREAD,
        re.compile(r"\b(?:pause|hold)\b.{0,24}\b(?:thread|track|item|workstream)?\b", re.I),
    ),
    (
        CommandKind.RESUME_THREAD,
        re.compile(r"\b(?:resume|continue|restart)\b.{0,24}\b(?:thread|track|item|workstream)?\b", re.I),
    ),
    (
        CommandKind.CLOSE_THREAD,
        re.compile(r"\b(?:close|complete|finish|resolve)\b.{0,24}\b(?:thread|track|item|workstream)?\b", re.I),
    ),
    (CommandKind.STATUS, re.compile(r"\b(?:status|progress|where are we|update me)\b", re.I)),
    (
        CommandKind.UPDATE_THREAD,
        re.compile(r"\b(?:update|track|record|append|add)\b.{0,28}\b(?:thread|progress|item|workstream|evidence)?\b", re.I),
    ),
)

_Z3_PATTERNS = (
    r"\bmerge\b",
    r"\bdeploy\b",
    r"\bpublish\b",
    r"\bsubmit\b",
    r"\bpurchase\b",
    r"\bbuy\b",
    r"\bapply\b",
    r"\bsend externally\b",
    r"\bchange account\b",
    r"\bcredential\b",
)
_Z2_PATTERNS = (
    r"\bratify\b",
    r"\bcanonical\b",
    r"\bpolicy\b",
    r"\bgovernance rule\b",
    r"\bsemantic change\b",
)

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_ITEM_ID_RE = re.compile(
    r"\b(?:"
    r"RM-\d{8}-\d{2}|CURR-\d{8}-\d{2}|MOVE-\d{8}-\d{2}|RQ-\d{8}-\d{2}|"
    r"PR-\d+|HARC-[A-Z0-9-]+|Q-[A-Z0-9-]+|THREAD-[A-Z0-9-]+"
    r")\b",
    re.I,
)
_URL_RE = re.compile(r"https?://\S+", re.I)
_EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")


def extract_new_text(raw_body: str) -> str:
    """Return the newest unquoted portion of an email body.

    This is deliberately conservative: it stops at common reply/history markers,
    drops quote-prefixed lines, and drops a recognized operator signature.
    """
    text = (raw_body or "").replace("\r\n", "\n")
    cut = len(text)
    for marker in _QUOTED_REPLY_MARKERS:
        match = marker.search(text)
        if match:
            cut = min(cut, match.start())
    text = text[:cut]

    kept = []
    for line in text.splitlines():
        if line.lstrip().startswith(">"):
            continue
        kept.append(line)
    text = "\n".join(kept)

    sig_cut = len(text)
    for marker in _SIGNATURE_MARKERS:
        match = marker.search(text)
        if match:
            sig_cut = min(sig_cut, match.start())
    return text[:sig_cut].strip()


def _tokens(value: str) -> set[str]:
    return set(_TOKEN_RE.findall((value or "").lower()))


def _title_score(query: str, title: str) -> float:
    query_norm = query.lower().strip()
    title_norm = title.lower().strip()
    query_tokens, title_tokens = _tokens(query_norm), _tokens(title_norm)
    if not query_tokens or not title_tokens:
        return 0.0
    overlap = len(query_tokens & title_tokens) / max(1, len(title_tokens))
    sequence = SequenceMatcher(None, query_norm, title_norm).ratio()
    contained = 1.0 if title_norm in query_norm else 0.0
    return max(contained, (0.65 * overlap) + (0.35 * sequence))


def resolve_target(
    text: str,
    item_catalog: Mapping[str, str],
) -> tuple[str | None, ResolutionState, tuple[str, ...]]:
    explicit = _ITEM_ID_RE.findall(text or "")
    if explicit:
        target = explicit[0].upper()
        # Explicit IDs are accepted even if the current catalog is stale. A later
        # state lookup can mark the item UNKNOWN rather than guessing a substitute.
        return target, ResolutionState.RESOLVED, tuple(x.upper() for x in explicit[1:])

    scored = sorted(
        ((_title_score(text, title), item_id.upper()) for item_id, title in item_catalog.items()),
        reverse=True,
    )
    if not scored or scored[0][0] < 0.48:
        return None, ResolutionState.NO_TARGET, ()

    best_score, best_id = scored[0]
    close = tuple(
        item_id
        for score, item_id in scored[1:4]
        if score >= best_score - 0.08 and score >= 0.45
    )
    if close:
        return None, ResolutionState.NEEDS_HUMAN, (best_id,) + close
    return best_id, ResolutionState.RESOLVED, ()


def classify_kind(text: str) -> CommandKind:
    clean = text or ""
    for kind, pattern in _COMMAND_PATTERNS:
        if pattern.search(clean):
            return kind
    if clean.strip():
        return CommandKind.NATURAL_NOTE
    return CommandKind.UNKNOWN


def classify_authority(text: str) -> AuthorityLevel:
    lower = (text or "").lower()
    if any(re.search(pattern, lower) for pattern in _Z3_PATTERNS):
        return AuthorityLevel.Z3
    if any(re.search(pattern, lower) for pattern in _Z2_PATTERNS):
        return AuthorityLevel.Z2
    return AuthorityLevel.Z1


def next_state(current: ThreadState, kind: CommandKind) -> ThreadState:
    if kind is CommandKind.BEGIN_THREAD:
        return ThreadState.ACTIVE if current in (ThreadState.NEW, ThreadState.ACTIVE) else current
    if kind is CommandKind.PAUSE_THREAD:
        return ThreadState.PAUSED if current is ThreadState.ACTIVE else current
    if kind is CommandKind.RESUME_THREAD:
        return ThreadState.ACTIVE if current is ThreadState.PAUSED else current
    if kind is CommandKind.CLOSE_THREAD:
        return ThreadState.CLOSED
    return current


@dataclass(frozen=True)
class CommandEvent:
    private_event_ref: str
    actor_kind: str
    command_kind: str
    target_item_id: str | None
    resolution_state: str
    candidate_item_ids: tuple[str, ...]
    current_state: str
    proposed_state: str
    authority_level: str
    execution_disposition: str
    tracking_requested: bool
    correction_detected: bool

    def public_projection(self) -> dict:
        """Privacy-minimized receipt suitable for a public Git projection."""
        out = asdict(self)
        out.pop("private_event_ref", None)
        return out


@dataclass
class InboundCommandProcessor:
    """In-memory prototype state machine.

    Durable private state belongs in the private ledger/adapter, not public Git.
    """

    item_catalog: Mapping[str, str]
    seen_private_event_refs: set[str] = field(default_factory=set)
    thread_states: dict[str, ThreadState] = field(default_factory=dict)

    def process(
        self,
        *,
        private_event_ref: str,
        raw_body: str,
        actor_kind: ActorKind = ActorKind.HUMAN,
    ) -> CommandEvent:
        if not private_event_ref:
            raise ValueError("private_event_ref is required")
        if private_event_ref in self.seen_private_event_refs:
            raise ValueError("replay detected for private_event_ref")

        new_text = extract_new_text(raw_body)
        kind = classify_kind(new_text)
        target, resolution, candidates = resolve_target(new_text, self.item_catalog)
        authority = classify_authority(new_text)

        # Only an explicitly segmented HUMAN span can create a control transition.
        actionable = (
            actor_kind is ActorKind.HUMAN
            and resolution is ResolutionState.RESOLVED
            and target is not None
        )
        current = self.thread_states.get(target or "", ThreadState.NEW)

        if authority is AuthorityLevel.Z1 and actionable:
            proposed = next_state(current, kind)
            disposition = "Z1_PROPOSED_TRANSITION"
        elif authority in (AuthorityLevel.Z2, AuthorityLevel.Z3):
            proposed = current
            disposition = "HOLD_FOR_HUMAN_AUTHORITY"
        elif actor_kind is not ActorKind.HUMAN:
            proposed = current
            disposition = "OBSERVATION_ONLY_NON_HUMAN"
        elif resolution is ResolutionState.NEEDS_HUMAN:
            proposed = current
            disposition = "NEEDS_TARGET_DISAMBIGUATION"
        else:
            proposed = current
            disposition = "NO_EXECUTABLE_TRANSITION"

        tracking_requested = bool(
            re.search(r"\btrack(?:ing)?\b|\bprogress\b|\bfollow\b", new_text, re.I)
        )
        correction = bool(
            re.search(r"\bcorrection\b|\bi forgot\b|\bactually\b|\binstead\b", new_text, re.I)
        )

        event = CommandEvent(
            private_event_ref=private_event_ref,
            actor_kind=actor_kind.value,
            command_kind=kind.value,
            target_item_id=target,
            resolution_state=resolution.value,
            candidate_item_ids=candidates,
            current_state=current.value,
            proposed_state=proposed.value,
            authority_level=authority.value,
            execution_disposition=disposition,
            tracking_requested=tracking_requested,
            correction_detected=correction,
        )

        # The prototype applies only reversible Z1 thread-state transitions.
        if disposition == "Z1_PROPOSED_TRANSITION" and target is not None:
            self.thread_states[target] = proposed

        self.seen_private_event_refs.add(private_event_ref)
        return event


def projection_contains_private_material(projection: Mapping[str, object]) -> bool:
    """Adversarial privacy lint for public projection tests."""
    blob = repr(dict(projection))
    return bool(
        _EMAIL_RE.search(blob)
        or _URL_RE.search(blob)
        or "private_event_ref" in blob
    )
