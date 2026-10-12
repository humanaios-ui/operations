"""
humanaios_core.py — HumanAIOS governance conformance model (v0.1)

Layer 0 conformance fixture for the concept-to-code stack. The proposed
HumanAIOS Core Machine (HCM) is the machine encoding; this module is a pure
model used to test whether governance examples conform to the documented
Z1 → Z2 → Z3 sequence.

CLAUDE.md, SEED.md and SESSION_RITUALS.md state the core concept of this
repository in prose. This module states it as code, so it can be run, tested
and falsified:

    A machine (Z1) may PROPOSE, and every proposal carries a falsifier and a
    pinned SHA. A modeled Z2 RATIFY transition produces an unkeyed sha256 hash
    over the candidate, a claimed identity, the time and the decision. Identity
    authenticity is external to this module. A modeled Z3 EXECUTE transition
    requires an ACCEPT hash and a caller-supplied CI status. Retries are bounded
    (anti-cascade: K=3, one open
    molt per constant, freeze after two reverts). Every session opens by
    pinning live state (§A) and closes by reconciling every claim against the
    tree (§B.0 / B.6). What is not in the ledger did not happen, and the gap
    between what was claimed and what the tree shows is the finding.

That last sentence is also ACAT's core measurement (SEED.md §3): the gap
between what a system claims about itself and what it does under test. The
governance conformance model and the research instrument are the same shape.

Nothing here decides anything on its own authority, authenticates an identity,
performs an external action, or supplies HCM authority evidence. The precedence of refusals
is the doctrine as written in CLAUDE.md ("Decision Routing", "Anti-cascade
rules", "§A / §B"), and it is not meant to be tuned per call site. The hash
formula is CLAUDE.md's, segment for segment:

    sha256(candidate | by=<signer> | at=<timestamp> | decision=ACCEPT|EDIT|REJECT)
    sha256(candidate | by=<signer> | at=<timestamp> | decision=... | contest_response=<reason>)

CLAUDE.md writes the `by=` segment as `by=Night`. "Night" is the ratifier's
display name (Z2_DISPLAY_NAME); the claimed identity that is hashed and checked
must be one of the two configured Z2 identities. `ratify()` validates only the
supplied value. It does not authenticate the caller. Protected infrastructure
must authenticate identity independently.

Stdlib only. `python3 humanaios_core.py --smoke-test` walks one candidate
through the full gate and exercises every refusal once.
"""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Iterable, Mapping, Sequence

__all__ = [
    "AUTHORIZED_Z2_IDENTITIES",
    "AUTHORITY_EFFECT",
    "CALLOUTS",
    "DECISION_WINDOW",
    "K_OPEN_MOLTS",
    "REVERTS_TO_FREEZE",
    "URGENT_WINDOW",
    "Action",
    "Candidate",
    "Decision",
    "Event",
    "GateRefused",
    "HCM_TRANSLATION_FIXTURE",
    "Ledger",
    "Ratification",
    "Receipt",
    "Z2_DISPLAY_NAME",
    "Zone",
    "anti_cascade",
    "callout_route",
    "can",
    "contest",
    "execute",
    "propose",
    "ratification_hash",
    "ratify",
    "reconcile",
    "session_close",
    "session_open",
    "verify_ratification",
    "window_state",
]

TOOL_NAME = "humanaios_core"
TOOL_VERSION = "0.1.0"
TOOL_CATEGORY = "validation_tool"
TOOL_SESSION = "CORE_CONCEPT_MAPPING.md"
TOOL_ZONE = 1


# ── Constants (CLAUDE.md, ratified values; a change here is a molt, not an edit) ──

#: The two Z2 identities ratified under Q-Z2-DUAL-AUTHORITY-GOVERNANCE-01 — the
#: same allowlist z2_ratification_gate.yml checks. Nothing else signs.
AUTHORIZED_Z2_IDENTITIES: frozenset[str] = frozenset(
    {"carly.r.anderson@gmail.com", "aioshuman@gmail.com"}
)
#: The ratifier's display name, as CLAUDE.md's formula writes the `by=` segment.
#: A label for humans; not accepted as a signer identity.
Z2_DISPLAY_NAME = "Night"
AUTHORITY_EFFECT = "NONE"
DECISION_WINDOW = timedelta(hours=48)  # routine decisions; after it, Z1 may contest
URGENT_WINDOW = timedelta(hours=24)  # urgent items: 24h or less
K_OPEN_MOLTS = 3  # anti-cascade rule 3
REVERTS_TO_FREEZE = 2  # anti-cascade rule 4

#: Substantive-falsifier check, same list ci_gates.FalsifierLintGate rejects.
_NON_FALSIFIERS = frozenset({"", "tbd", "n/a", "none", "unknown"})

#: Semantic translation fixture for the proposed HCM v0.1 instruction set.
#: This mapping does not compile a program or satisfy HCM authority checks.
HCM_TRANSLATION_FIXTURE: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {
        "propose": ("PIN_CONTEXT", "OBSERVE", "CLAIM", "CHALLENGE", "WARRANT"),
        "ratify": ("IMPORT_AUTHORITY",),
        "execute": ("RECORD_ACTION",),
        "session_close": ("RECORD_OUTCOME", "CLOSE"),
    }
)


# ── Roles and actions ───────────────────────────────────────────────────────


class Zone(Enum):
    """The three roles. A zone is a capability set, not a rank."""

    Z1 = "Z1"  # proposer (Claude, practice teams)
    Z2 = "Z2"  # ratifier (Night) — the serial gate
    Z3 = "Z3"  # executor (per ZONE_REGISTRY.md)


class Action(Enum):
    PROPOSE = "PROPOSE"
    RATIFY = "RATIFY"
    EXECUTE = "EXECUTE"
    CONTEST = "CONTEST"


#: CLAUDE.md "Cannot do (by design)": Z2 neither proposes nor executes; Z1 and Z3
#: do not ratify. The table is the whole authority model; nothing else grants.
_CAPABILITIES: Mapping[Zone, frozenset[Action]] = {
    Zone.Z1: frozenset({Action.PROPOSE, Action.CONTEST}),
    Zone.Z2: frozenset({Action.RATIFY}),
    Zone.Z3: frozenset({Action.EXECUTE, Action.CONTEST}),
}


def can(zone: Zone, action: Action) -> bool:
    """Does this zone hold this capability? Absence is refusal rather than a default."""
    return action in _CAPABILITIES[zone]


class GateRefused(Exception):
    """A step in the serial gate was refused. The message names the doctrine."""


def _require_aware(value: datetime, label: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise GateRefused(f"{label} must be timezone-aware")


def _require(zone: Zone, action: Action) -> None:
    if not can(zone, action):
        raise GateRefused(f"{zone.value} cannot {action.value}: not in its capability set (CLAUDE.md)")


# ── Candidate: the unit Z1 proposes ─────────────────────────────────────────


class Decision(Enum):
    ACCEPT = "ACCEPT"
    EDIT = "EDIT"
    REJECT = "REJECT"


@dataclass(frozen=True)
class Candidate:
    """A candidate block (F / IC / H / MOLT / Q). Frozen: a ratified thing remains immutable."""

    candidate_id: str
    kind: str  # F | IC | H | MOLT | Q
    body: str
    falsifier: str  # required by falsifier_lint.yml; the shape of the void around the claim
    pinned_sha: str  # REGISTERED.md SHA read live this session (IC-030)
    proposed_by: str
    proposed_at: datetime

    def __post_init__(self) -> None:
        _require_aware(self.proposed_at, "proposed_at")

    def canonical(self) -> str:
        """Deterministic serialization covered by the modeled Z2 hash."""
        return json.dumps(
            {
                "candidate_id": self.candidate_id,
                "kind": self.kind,
                "body": self.body,
                "falsifier": self.falsifier,
                "pinned_sha": self.pinned_sha,
                "proposed_by": self.proposed_by,
                "proposed_at": self.proposed_at.isoformat(),
            },
            sort_keys=True,
        )


def _falsifier_is_substantive(falsifier: str) -> bool:
    return falsifier.strip().lower() not in _NON_FALSIFIERS


def propose(
    zone: Zone,
    candidate_id: str,
    kind: str,
    body: str,
    falsifier: str,
    pinned_sha: str,
    proposed_by: str,
    now: datetime,
    ledger: Ledger | None = None,
) -> Candidate:
    """Z1 proposes. Refused without a substantive falsifier or a pinned SHA.

    Decision Routing steps 1–4: read REGISTERED.md live and pin it (IC-030),
    create the block, include the falsifier (falsifier_lint.yml), submit.
    With a `ledger`, the accepted proposal is written as a PROPOSE row; a
    refusal writes nothing.
    """
    _require(zone, Action.PROPOSE)
    _require_aware(now, "proposal timestamp")
    if not _falsifier_is_substantive(falsifier):
        raise GateRefused(
            f"{candidate_id}: falsifier missing or non-substantive (falsifier doctrine; "
            "a claim that cannot be shown false claims nothing)"
        )
    if not pinned_sha or not pinned_sha.strip():
        raise GateRefused(f"{candidate_id}: no pinned REGISTERED.md SHA (IC-030: live-fetch, pin, do not reason from cache)")
    if kind not in {"F", "IC", "H", "MOLT", "Q"}:
        raise GateRefused(f"{candidate_id}: unknown candidate kind {kind!r} (F | IC | H | MOLT | Q)")
    candidate = Candidate(candidate_id, kind, body, falsifier, pinned_sha, proposed_by, now)
    if ledger is not None:
        ledger.append("PROPOSE", now, proposed_by, {"candidate_id": candidate_id, "kind": kind, "pinned_sha": pinned_sha})
    return candidate


# ── Ratification: the Z2 serial gate ────────────────────────────────────────


@dataclass(frozen=True)
class Ratification:
    """One RATIFY event. Append-only: a changed mind is a new event with a new hash."""

    candidate_id: str
    by: str
    at: datetime
    decision: Decision
    hash: str
    contest_response: str | None = None
    reason: str = ""

    def __post_init__(self) -> None:
        _require_aware(self.at, "ratification timestamp")


def ratification_hash(
    candidate: Candidate, by: str, at: datetime, decision: Decision, contest_response: str | None = None
) -> str:
    """CLAUDE.md's formula, segment for segment:

    sha256(candidate | by=<signer> | at=<timestamp> | decision=<decision>[ | contest_response=<reason>])

    <signer> is a claimed Z2 identity supplied by the caller. This unkeyed hash
    does not authenticate that caller (CLAUDE.md writes the segment as
    `by=Night`, the ratifier's display name; see Z2_DISPLAY_NAME).
    """
    _require_aware(at, "ratification timestamp")
    hashable = f"{candidate.canonical()} | by={by} | at={at.isoformat()} | decision={decision.value}"
    if contest_response is not None:
        hashable += f" | contest_response={contest_response}"
    return hashlib.sha256(hashable.encode("utf-8")).hexdigest()


def ratify(
    zone: Zone,
    candidate: Candidate,
    by: str,
    at: datetime,
    decision: Decision,
    reason: str = "",
    contest_response: str | None = None,
    ledger: Ledger | None = None,
) -> Ratification:
    """Model a Z2 transition for an allowed claimed identity.

    Decision Routing steps 5–9: ACCEPT → CI merges and Z3 executes; EDIT → Z1
    revises and resubmits; REJECT → reason documented, Z1 may re-propose or
    contest within 48h. A REJECT without a documented reason is refused. The
    display name "Night" is refused as a signer: only the two ratified
    identities are accepted as values. The caller is not authenticated here.
    With a `ledger`, the modeled hash is written as a RATIFY row; a refusal
    writes nothing.
    """
    _require(zone, Action.RATIFY)
    _require_aware(at, "ratification timestamp")
    if by not in AUTHORIZED_Z2_IDENTITIES:
        raise GateRefused(
            f"{by!r} is not an authorized Z2 identity (Q-Z2-DUAL-AUTHORITY-GOVERNANCE-01); "
            "a display name is a label, not a signature"
        )
    if decision is Decision.REJECT and not reason.strip():
        raise GateRefused(f"{candidate.candidate_id}: REJECT requires a documented reason (Decision Routing step 9)")
    digest = ratification_hash(candidate, by, at, decision, contest_response)
    ratification = Ratification(candidate.candidate_id, by, at, decision, digest, contest_response, reason)
    if ledger is not None:
        ledger.append(
            "RATIFY", at, by,
            {"candidate_id": candidate.candidate_id, "decision": decision.value, "hash": digest,
             "contested": contest_response is not None, "reason": reason},
        )
    return ratification


def verify_ratification(candidate: Candidate, ratification: Ratification) -> bool:
    """Recompute the unkeyed hash. This checks consistency, not identity."""
    if ratification.candidate_id != candidate.candidate_id:
        return False
    if ratification.by not in AUTHORIZED_Z2_IDENTITIES:
        return False
    expected = ratification_hash(
        candidate, ratification.by, ratification.at, ratification.decision, ratification.contest_response
    )
    return expected == ratification.hash


# ── Windows and contest ─────────────────────────────────────────────────────


def window_state(candidate: Candidate, now: datetime, decided: bool, urgent: bool = False) -> str:
    """OPEN while the Z2 window runs; DECIDED once signed; EXPIRED when it closes unsigned.

    An EXPIRED window is a GAP callout and the trigger for the contest route.
    """
    _require_aware(now, "window timestamp")
    if decided:
        return "DECIDED"
    window = URGENT_WINDOW if urgent else DECISION_WINDOW
    return "OPEN" if now - candidate.proposed_at <= window else "EXPIRED"


def contest(
    zone: Zone,
    candidate: Candidate,
    prior: Ratification | None,
    now: datetime,
    contest_reason: str,
) -> str:
    """Z1 (or Z3, on a GAUGE) requests an Admiral re-read. Returns the callout text.

    Allowed when a verified REJECT on *this* candidate is contested within 48h
    of its signature, or when the 48h window closed with no decision at all.
    A `prior` that does not verify against the candidate (forged, or signed
    for another candidate) is refused, as is a contest dated before the
    rejection it contests. Does not mutate `prior`: the Admiral answers with a
    *new* RATIFY event carrying `contest_response`.
    """
    _require(zone, Action.CONTEST)
    _require_aware(now, "contest timestamp")
    if not contest_reason.strip():
        raise GateRefused(f"{candidate.candidate_id}: a contest without a reason is not a contest")
    if prior is None:
        if window_state(candidate, now, decided=False) != "EXPIRED":
            raise GateRefused(
                f"{candidate.candidate_id}: Z2 window still open; wait for the decision or the window"
            )
        return f"IC beyond 48h / Z2 decision contested: {candidate.candidate_id} — no decision inside window"
    if not verify_ratification(candidate, prior):
        raise GateRefused(
            f"{candidate.candidate_id}: the prior ratification does not verify against this candidate; "
            "nothing to contest"
        )
    if prior.decision is not Decision.REJECT:
        raise GateRefused(f"{candidate.candidate_id}: only a REJECT is contestable; {prior.decision.value} is not")
    elapsed = now - prior.at
    if elapsed < timedelta(0):
        raise GateRefused(f"{candidate.candidate_id}: contest is dated before the REJECT it contests")
    if elapsed > DECISION_WINDOW:
        raise GateRefused(f"{candidate.candidate_id}: contest window (48h after REJECT) has closed; re-propose instead")
    return f"IC beyond 48h / Z2 decision contested: {candidate.candidate_id} — {contest_reason}"


# ── Execution: Z3 under hash ────────────────────────────────────────────────


@dataclass(frozen=True)
class Event:
    """A ledger row. `prev_hash` chains it to the row before (NF_LEDGER discipline)."""

    kind: str  # PROPOSE | RATIFY | EXECUTE | VERDICT | CALLOUT | RECEIPT
    at: datetime
    by: str
    payload: Mapping[str, Any]
    prev_hash: str
    hash: str


class Ledger:
    """Append-only, hash-chained. Edit a prior line and `verify()` fails."""

    GENESIS = hashlib.sha256(b"humanaios-core-genesis").hexdigest()

    def __init__(self) -> None:
        self._events: list[Event] = []

    @staticmethod
    def _digest(kind: str, at: datetime, by: str, payload: Mapping[str, Any], prev_hash: str) -> str:
        body = json.dumps({"kind": kind, "at": at.isoformat(), "by": by, "payload": payload}, sort_keys=True, default=str)
        return hashlib.sha256(f"{prev_hash}|{body}".encode("utf-8")).hexdigest()

    def append(self, kind: str, at: datetime, by: str, payload: Mapping[str, Any]) -> Event:
        _require_aware(at, "event timestamp")
        prev = self._events[-1].hash if self._events else self.GENESIS
        normalized = json.loads(json.dumps(payload, sort_keys=True, default=str))
        ev = Event(kind, at, by, normalized, prev, self._digest(kind, at, by, normalized, prev))
        self._events.append(ev)
        return ev

    def events(self, kind: str | None = None) -> list[Event]:
        return [e for e in self._events if kind is None or e.kind == kind]

    def verify(self) -> bool:
        prev = self.GENESIS
        for ev in self._events:
            if ev.prev_hash != prev or self._digest(ev.kind, ev.at, ev.by, ev.payload, prev) != ev.hash:
                return False
            prev = ev.hash
        return True

    def __len__(self) -> int:
        return len(self._events)


def execute(
    zone: Zone,
    candidate: Candidate,
    ratification: Ratification | None,
    ci_gate_pass: bool,
    executor: str,
    now: datetime,
    ledger: Ledger,
) -> Event:
    """Model a Z3 transition and write one EXECUTE row. Four refusals, in order:

    1. wrong zone;  2. no Z2 hash (CI enforces);  3. hash does not verify, or
    is not an ACCEPT;  4. CI gate not green. Only then is the EXECUTE row written.
    The VERDICT (prediction held / falsifier tripped) is a later event, emitted
    at window close by the measurement step (molt_cycle.py), not here.
    """
    _require(zone, Action.EXECUTE)
    _require_aware(now, "execution timestamp")
    if ratification is None:
        raise GateRefused(f"{candidate.candidate_id}: no Z2 hash — Z3 cannot execute without one (CI enforces)")
    if not verify_ratification(candidate, ratification):
        raise GateRefused(f"{candidate.candidate_id}: Z2 hash does not verify against the candidate as signed")
    if ratification.decision is not Decision.ACCEPT:
        raise GateRefused(
            f"{candidate.candidate_id}: ratification is {ratification.decision.value}, not ACCEPT; nothing to execute"
        )
    if not ci_gate_pass:
        raise GateRefused(f"{candidate.candidate_id}: z2_ratification_gate / CI not green; merge blocked")
    return ledger.append(
        "EXECUTE",
        now,
        executor,
        {"candidate_id": candidate.candidate_id, "z2_hash": ratification.hash, "pinned_sha": candidate.pinned_sha},
    )


# ── Anti-cascade envelope (MOLT_STATE.md rules 1, 3, 4; molt_cycle.py holds 2 and 5) ──


def anti_cascade(
    constant: str,
    open_molts: Mapping[str, str],
    consecutive_reverts: Mapping[str, int],
) -> list[str]:
    """Rules a new molt candidate on `constant` would break. Empty list = inside the envelope.

    open_molts: constant -> open molt id. consecutive_reverts: constant -> count.
    Rules 2 (no self-reference inside a window) and 5 (Priority Queue rank)
    need the event stream and the queue; they stay in molt_cycle.py.
    """
    broken: list[str] = []
    if constant in open_molts:
        broken.append(f"rule 1: one open molt per constant ({constant} has {open_molts[constant]} open)")
    if len(open_molts) >= K_OPEN_MOLTS:
        broken.append(f"rule 3: at most K={K_OPEN_MOLTS} molts open system-wide ({len(open_molts)} open)")
    if consecutive_reverts.get(constant, 0) >= REVERTS_TO_FREEZE:
        broken.append(
            f"rule 4: {constant} reverted {consecutive_reverts[constant]} times in a row → frozen; "
            "Z2 Tier-2 ruling required to reopen"
        )
    return broken


# ── Callouts (CLAUDE.md "Callout Mandatory Triggers") ───────────────────────

#: callout -> (routes, Z2 response). Q = Priority Queue, FS = findings scan,
#: OM = operator monitoring, MOLT = molt state, Z2 = direct to ratifier.
CALLOUTS: Mapping[str, tuple[tuple[str, ...], str]] = {
    "GAP": (("Q",), "Accept/edit/reject unblock"),
    "STALE": (("Q", "MOLT"), "Re-read constant or retire"),
    "RECEIPT-GAP": (("Q", "FS"), "Verify or file IC-CAND"),
    "GAUGE": (("Q", "OM"), "Re-evaluate context"),
    "AMBIGUITY": (("FS",), "Clarify or amend prior"),
    "VOID": (("FS",), "Falsify or retire claim"),
    "DRIFT": (("Q",), "Adjust dial or update dials"),
    "DISPUTED": (("Z2", "FS"), "Re-read and re-sign"),
    "MOLT": (("Z2",), "Ratify, edit, or reject"),
    "REVERT": (("FS", "Q"), "File F/IC candidate; rank in Q"),
}


def callout_route(kind: str) -> tuple[tuple[str, ...], str]:
    """Where a callout goes and what Z2 owes back. Unknown kinds are refused, not guessed."""
    if kind not in CALLOUTS:
        raise GateRefused(f"{kind!r} is not a mandatory callout; the ten are {sorted(CALLOUTS)}")
    return CALLOUTS[kind]


# ── Session rituals: §A open, §B close ──────────────────────────────────────


def session_open(state: Mapping[str, Any]) -> list[str]:
    """§A: the halts, in order. Empty list = the session may begin work.

    Keys read: pinned_sha, registered_read_at_sha, queue_read, zone_registry_ok,
    manifest_ok, position, destination, probability. A missing key is a halt,
    a missing key is a refusal — the cautious default, as in authorization_evidence.py.
    """
    halts: list[str] = []
    sha = state.get("pinned_sha")
    if not sha:
        halts.append("A.1: no pinned SHA (git fetch && git rev-parse HEAD)")
    if not state.get("registered_read_at_sha") or state.get("registered_read_at_sha") != sha:
        halts.append("A.2: REGISTERED.md not read live at the pinned SHA (IC-030 hard halt)")
    if not state.get("queue_read"):
        halts.append("A.3: PRIORITY_QUEUE.md (or z1-inbox patch) not read")
    if not state.get("zone_registry_ok"):
        halts.append("A.4: ZONE_REGISTRY.md not read at SHA / heading count ≠ active rows")
    if not state.get("manifest_ok"):
        halts.append("A.5: sha256 manifest verification not done")
    p = state.get("probability")
    # bool subclasses int: True/False would read as 1.0/0.0, a status standing in for a calibration.
    p_ok = isinstance(p, (int, float)) and not isinstance(p, bool) and 0.0 <= p <= 1.0
    if not state.get("position") or not state.get("destination") or not p_ok:
        halts.append("A.6: position · destination · probability (0..1, a number not a flag) not stated")
    return halts


@dataclass(frozen=True)
class Receipt:
    """B.6 output: which claims the tree confirms, and which it does not."""

    matched: tuple[str, ...]
    gaps: tuple[str, ...]  # RECEIPT-GAP: claimed, not in the tree → Priority Queue

    @property
    def clean(self) -> bool:
        return not self.gaps


def reconcile(claims: Iterable[str], tree: Iterable[str]) -> Receipt:
    """Walk claim vs tree. The gap is the finding (IC-031: overstatement has a cost class).

    `claims` are the statements a transcript makes; `tree` is what the B.0
    verification block actually showed (paths, hashes, counts). A claim with no
    matching entry is a RECEIPT-GAP, and the receipt must be walked back to the
    tree — the tree is not explained up to the claim.
    """
    have = set(tree)
    matched, gaps = [], []
    for c in claims:
        (matched if c in have else gaps).append(c)
    return Receipt(tuple(matched), tuple(gaps))


def session_close(state: Mapping[str, Any], ledger: Ledger, now: datetime, by: str) -> Receipt:
    """§B: B.0 refuses the close outright; B.6 reconciles and writes the receipt.

    Keys read: code_ran, prereg_verified, claims, tree, handoff_written.
    """
    _require_aware(now, "session-close timestamp")
    if not state.get("code_ran"):
        raise GateRefused("B.0: code did not run this session; close refused")
    if not state.get("prereg_verified"):
        raise GateRefused("B.0: prereg hash not verified in REGISTERED.md; close refused")
    if not state.get("handoff_written"):
        raise GateRefused("B: z1-inbox/<date>/HANDOFF.md not written; close refused")
    receipt = reconcile(state.get("claims", ()), state.get("tree", ()))
    ledger.append("RECEIPT", now, by, {"matched": list(receipt.matched), "gaps": list(receipt.gaps)})
    for gap in receipt.gaps:
        routes, _ = callout_route("RECEIPT-GAP")
        ledger.append("CALLOUT", now, by, {"kind": "RECEIPT-GAP", "claim": gap, "routes": list(routes)})
    return receipt


# ── Smoke test: one candidate through the whole gate, every refusal once ────


def _smoke_test() -> int:
    t0 = datetime(2026, 10, 11, 12, 0, tzinfo=timezone.utc)
    ledger = Ledger()
    checks = 0

    def refused(fn, *a, **kw) -> None:
        nonlocal checks
        try:
            fn(*a, **kw)
        except GateRefused:
            checks += 1
            return
        raise AssertionError(f"expected GateRefused from {getattr(fn, '__name__', fn)}")

    def ok(cond: bool, label: str) -> None:
        nonlocal checks
        if not cond:
            raise AssertionError(label)
        checks += 1

    # §A: a session that skipped the pin halts; a complete open does not.
    ok(session_open({}) and session_open({})[0].startswith("A.1"), "empty open must halt at A.1")
    opened = {
        "pinned_sha": "bda7c88", "registered_read_at_sha": "bda7c88", "queue_read": True,
        "zone_registry_ok": True, "manifest_ok": True,
        "position": "REGISTERED.md pinned at bda7c88", "destination": "Layer 0 kernel", "probability": 0.85,
    }
    ok(session_open(opened) == [], "complete §A must not halt")
    ok("A.2" in session_open({**opened, "registered_read_at_sha": "stale"})[0], "cached REGISTERED.md is an IC-030 halt")
    ok("A.6" in session_open({**opened, "probability": True})[0], "a boolean is a status, not a probability")

    # Z1 proposes: falsifier and pinned SHA are required; Z2 cannot propose. A refusal writes no row.
    refused(propose, Zone.Z1, "Q-X", "Q", "body", "TBD", "bda7c88", "claude", t0, ledger)
    refused(propose, Zone.Z1, "Q-X", "Q", "body", "fails if smoke test does not exit 0", "", "claude", t0, ledger)
    refused(propose, Zone.Z2, "Q-X", "Q", "body", "fails if smoke test does not exit 0", "bda7c88", Z2_DISPLAY_NAME, t0, ledger)
    ok(len(ledger) == 0, "a refused proposal writes nothing")
    cand = propose(Zone.Z1, "Q-CORE-CONCEPT-01", "Q", "humanaios_core.py encodes the serial gate",
                   "falsified if any gate step passes without its doctrine's precondition",
                   "bda7c88", "claude", t0, ledger)
    ok(len(ledger) == 1 and ledger.events("PROPOSE")[0].payload["candidate_id"] == cand.candidate_id,
       "an accepted proposal is a PROPOSE row")
    ok(can(Zone.Z1, Action.PROPOSE) and not can(Zone.Z1, Action.RATIFY), "Z1 proposes and does not ratify")
    ok(can(Zone.Z2, Action.RATIFY) and not can(Zone.Z2, Action.EXECUTE), "Z2 ratifies and does not execute")
    ok(can(Zone.Z3, Action.EXECUTE) and not can(Zone.Z3, Action.RATIFY), "Z3 executes and does not ratify")

    # Z3 cannot execute without a hash; Z1 cannot ratify; an unknown identity cannot sign;
    # the display name "Night" is a label, not a signer.
    refused(execute, Zone.Z3, cand, None, True, "z3", t0, ledger)
    refused(ratify, Zone.Z1, cand, "claude", t0, Decision.ACCEPT)
    refused(ratify, Zone.Z2, cand, "someone@example.com", t0, Decision.ACCEPT)
    refused(ratify, Zone.Z2, cand, Z2_DISPLAY_NAME, t0, Decision.ACCEPT, ledger=ledger)
    refused(ratify, Zone.Z2, cand, "carly.r.anderson@gmail.com", t0, Decision.REJECT)  # REJECT needs a reason
    ok(len(ledger) == 1, "a refused ratification writes nothing")

    # Window: open inside 48h, expired after; contest only after expiry or a REJECT.
    ok(window_state(cand, t0 + timedelta(hours=47), decided=False) == "OPEN", "47h: open")
    ok(window_state(cand, t0 + timedelta(hours=49), decided=False) == "EXPIRED", "49h: expired")
    ok(window_state(cand, t0 + timedelta(hours=25), decided=False, urgent=True) == "EXPIRED", "urgent: 24h")
    refused(contest, Zone.Z1, cand, None, t0 + timedelta(hours=1), "too slow")
    ok("no decision inside window" in contest(Zone.Z1, cand, None, t0 + timedelta(hours=49), "GAP"), "expired → contest")

    # REJECT, contest, Admiral re-reads: a new event, the prior intact.
    t1 = t0 + timedelta(hours=2)
    rej = ratify(Zone.Z2, cand, "carly.r.anderson@gmail.com", t1, Decision.REJECT, reason="falsifier too broad",
                 ledger=ledger)
    ok(verify_ratification(cand, rej), "REJECT hash verifies")
    ok(ledger.events("RATIFY")[-1].payload["decision"] == "REJECT", "a signed REJECT is a RATIFY row")
    refused(execute, Zone.Z3, cand, rej, True, "z3", t1, ledger)  # a verified REJECT executes nothing
    ok("contested" in contest(Zone.Z1, cand, rej, t1 + timedelta(hours=3), "falsifier is the standard one"), "contest in window")
    refused(contest, Zone.Z1, cand, rej, t1 + timedelta(hours=49), "late")
    refused(contest, Zone.Z1, cand, rej, t1 - timedelta(hours=1), "dated before the REJECT")
    other = propose(Zone.Z1, "Q-OTHER-01", "Q", "another block", "falsified if X", "bda7c88", "claude", t0)
    refused(contest, Zone.Z1, other, rej, t1 + timedelta(hours=1), "a REJECT signed for a different candidate")
    forged_rej = Ratification(cand.candidate_id, rej.by, rej.at, Decision.REJECT, "0" * 64, None, "forged")
    refused(contest, Zone.Z1, cand, forged_rej, t1 + timedelta(hours=1), "a REJECT whose hash does not verify")
    t2 = t1 + timedelta(hours=4)
    acc = ratify(Zone.Z2, cand, "aioshuman@gmail.com", t2, Decision.ACCEPT,
                 contest_response="re-read: falsifier is adequate", ledger=ledger)
    ok(acc.hash != rej.hash and verify_ratification(cand, rej) and verify_ratification(cand, acc),
       "a new RATIFY event preserves the prior one")
    refused(contest, Zone.Z1, cand, acc, t2, "an ACCEPT is not contestable")
    ok(ledger.events("RATIFY")[-1].payload["contested"] is True, "the re-read is its own RATIFY row")

    # Hash formula: CLAUDE.md's segments with the ratified identity as signer, sensitive to every field.
    expected = hashlib.sha256(
        f"{cand.canonical()} | by=aioshuman@gmail.com | at={t2.isoformat()} | decision=ACCEPT"
        " | contest_response=re-read: falsifier is adequate".encode()
    ).hexdigest()
    ok(acc.hash == expected, "hash is sha256(candidate | by=<signer> | at=ts | decision=... | contest_response=...)")
    tampered = Candidate(cand.candidate_id, cand.kind, cand.body + " and more", cand.falsifier,
                         cand.pinned_sha, cand.proposed_by, cand.proposed_at)
    ok(not verify_ratification(tampered, acc), "an edited candidate no longer matches its signature")
    forged = Ratification(acc.candidate_id, "aioshuman@gmail.com", acc.at, Decision.ACCEPT, "0" * 64, acc.contest_response)
    refused(execute, Zone.Z3, cand, forged, True, "z3", t2, ledger)
    refused(execute, Zone.Z3, tampered, acc, True, "z3", t2, ledger)

    # Z3 executes: zone, hash, ACCEPT, CI — then the row lands.
    refused(execute, Zone.Z2, cand, acc, True, "Night", t2, ledger)
    refused(execute, Zone.Z3, cand, acc, False, "z3", t2, ledger)
    ev = execute(Zone.Z3, cand, acc, True, "z3-operations", t2, ledger)
    ok(ev.kind == "EXECUTE" and ev.payload["z2_hash"] == acc.hash, "EXECUTE row carries the Z2 hash")

    # Anti-cascade envelope.
    ok(anti_cascade("c1", {}, {}) == [], "empty envelope: inside")
    ok(any(r.startswith("rule 1") for r in anti_cascade("c1", {"c1": "M-1"}, {})), "one open molt per constant")
    ok(any(r.startswith("rule 3") for r in anti_cascade("c4", {"c1": "a", "c2": "b", "c3": "c"}, {})), "K=3")
    ok(any(r.startswith("rule 4") for r in anti_cascade("c1", {}, {"c1": 2})), "freeze after 2 reverts")
    ok(anti_cascade("c1", {}, {"c1": 1}) == [], "one revert is not a freeze")

    # Callouts.
    ok(callout_route("RECEIPT-GAP") == (("Q", "FS"), "Verify or file IC-CAND"), "RECEIPT-GAP routes to Q + FS")
    ok(len(CALLOUTS) == 10, "ten mandatory callouts")
    refused(callout_route, "VIBES")

    # §B: B.0 refuses; B.6 reconciles claim vs tree; gaps become callouts in the ledger.
    refused(session_close, {"code_ran": False}, ledger, t2, "claude")
    refused(session_close, {"code_ran": True, "prereg_verified": False}, ledger, t2, "claude")
    close_state = {
        "code_ran": True, "prereg_verified": True, "handoff_written": True,
        "claims": ["humanaios_core.py", "CORE_CONCEPT_MAPPING.md", "deployed to production"],
        "tree": ["humanaios_core.py", "CORE_CONCEPT_MAPPING.md", "test_humanaios_core_tier1.py"],
    }
    receipt = session_close(close_state, ledger, t2, "claude")
    ok(receipt.gaps == ("deployed to production",) and not receipt.clean, "the overstated claim is the gap")
    ok(len(ledger.events("CALLOUT")) == 1 and ledger.events("CALLOUT")[0].payload["kind"] == "RECEIPT-GAP",
       "RECEIPT-GAP callout written")
    ok(reconcile(["a"], ["a"]).clean, "a claim the tree confirms is clean")

    # Ledger: append-only, chained; a rewritten prior row breaks verify().
    ok(ledger.verify() and [e.kind for e in ledger.events()]
       == ["PROPOSE", "RATIFY", "RATIFY", "EXECUTE", "RECEIPT", "CALLOUT"],
       "chain verifies: PROPOSE, RATIFY (REJECT), RATIFY (ACCEPT), EXECUTE, RECEIPT, CALLOUT")
    first = ledger._events[0]
    ledger._events[0] = Event(first.kind, first.at, "someone-else", first.payload, first.prev_hash, first.hash)
    ok(not ledger.verify(), "an edited prior line breaks the chain")

    print(f"humanaios_core smoke: {checks} checks OK — propose→ratify→execute gated, "
          "hash verified, windows/contest honored, envelope bounded, claims reconciled, ledger chained")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--smoke-test"]:
        return _smoke_test()
    print(__doc__)
    print("usage: python3 humanaios_core.py --smoke-test")
    return 0 if not args else 2


if __name__ == "__main__":
    sys.exit(main())
