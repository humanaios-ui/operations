"""
drift_transfer_gate.py — Drift Signal handoff, as a state machine.

GOVERNANCE.md text: "Drift = transfer the chat. Do not continue in a
drifted session. Night names the signal; Claude acknowledges and
transfers."

Note on this demo, unlike the other three gates: no real drift signal
was actually named in this session, so the demonstration below uses a
realistic-but-hypothetical trigger (a drift code from GOVERNANCE.md's
own catalog), not a real session event. Flagging that distinction
explicitly rather than implying otherwise.

Codes the handoff sequence and the hard stop. Does NOT judge whether a
given session state actually IS drift — that's Night's call, named in
the plain sense of "Night names the signal."
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

# Real drift codes, taken directly from SEED.md §7.3's own catalog —
# not invented for this demo.
KNOWN_DRIFT_CODES = {
    "C-08": "stale declared state",
    "C-09": "tool pipeline assumption without verification",
    "D-04": "subtle inconsistency between layers",
    "D-COMP": "compensation scoring above corpus mean",
    "F31": "stillpoint ritualization — autodream without operator gates",
    "F-INTENT-PARSE-MUTATION": "intent mutation at interpretation step",
    "IC-021": "dataset claims without corpus rows",
    "IC-022": "off-by-one N count drift",
}


class DriftState(Enum):
    NORMAL = "normal"
    SIGNAL_NAMED = "signal_named_by_night"
    ACKNOWLEDGED = "acknowledged_by_claude"
    TRANSFERRED = "session_transferred"


class DriftGateError(Exception):
    """Hard-reject: 'Do not continue in a drifted session' enforced as
    code, not as a reminder Claude might skip under momentum."""


@dataclass
class Session:
    session_id: str
    state: DriftState = DriftState.NORMAL
    drift_code: str | None = None
    named_by: str | None = None
    history: list = field(default_factory=list)

    def _log(self, event: str):
        self.history.append({"event": event, "at": datetime.now(timezone.utc).isoformat()})


def name_drift(session: Session, drift_code: str, named_by: str) -> Session:
    """Night's move. Only Night names drift, per the principle text —
    this function does not evaluate whether drift is really occurring,
    it only requires the code to be a real, catalogued one."""
    if drift_code not in KNOWN_DRIFT_CODES:
        raise DriftGateError(f"REFUSED: '{drift_code}' is not a catalogued drift code (SEED.md §7.3)")
    session.drift_code = drift_code
    session.named_by = named_by
    session.state = DriftState.SIGNAL_NAMED
    session._log(f"SIGNAL_NAMED: {drift_code} ({KNOWN_DRIFT_CODES[drift_code]}) by {named_by}")
    return session


def acknowledge(session: Session) -> Session:
    """Claude's required response — acknowledge, not argue, not continue."""
    if session.state != DriftState.SIGNAL_NAMED:
        raise DriftGateError(f"Nothing to acknowledge (state={session.state})")
    session.state = DriftState.ACKNOWLEDGED
    session._log(f"ACKNOWLEDGED: {session.drift_code}")
    return session


def transfer(session: Session) -> Session:
    session.state = DriftState.TRANSFERRED
    session._log("TRANSFERRED")
    return session


def continue_work(session: Session, task_description: str) -> str:
    """The actual hard stop. Any attempt to keep producing work after
    drift is named, before transfer completes, is refused outright —
    this is the literal code translation of 'do not continue in a
    drifted session.'"""
    if session.state in (DriftState.SIGNAL_NAMED, DriftState.ACKNOWLEDGED):
        raise DriftGateError(
            f"REFUSED: cannot continue '{task_description}' — session {session.session_id} "
            f"is in {session.state.value} (drift {session.drift_code}). Transfer required first."
        )
    return f"proceeding: {task_description}"


if __name__ == "__main__":
    print("── Case 1: attempt to keep working immediately after drift is named — refused ──")
    s = Session(session_id="S-DEMO-01")
    name_drift(s, drift_code="C-08", named_by="night")
    try:
        continue_work(s, "draft next artifact")
    except DriftGateError as e:
        print(f"  continue_work() correctly refused: {e}")

    print("\n── Case 2: proper sequence — acknowledge, transfer, only then can a NEW session continue ──")
    acknowledge(s)
    transfer(s)
    print(f"  final state of {s.session_id}: {s.state.value}")
    for h in s.history:
        print(f"    {h['at']}  {h['event']}")

    print("\n── Case 3: an invalid, non-catalogued drift code is refused at the naming step itself ──")
    s2 = Session(session_id="S-DEMO-02")
    try:
        name_drift(s2, drift_code="MADE-UP-CODE", named_by="night")
    except DriftGateError as e:
        print(f"  name_drift() correctly refused: {e}")
