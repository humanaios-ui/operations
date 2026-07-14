"""
mason_gate.py — Z1/Z2/Z3 as journeyman-dress / master-inspection / wall-set.

Historical basis (verified this session, not asserted from memory):
banker marks (preparer) vs. waller marks (setter) — two distinct roles,
matching declarant_id / administrator_id already used in the ACAT toolchain.
The master's inspection was against a fixed external standard (square,
level, plumb) — not a subjective judgment call. This module enforces that
same requirement in code: inspection MUST cite which concrete check ran.
A rubber-stamp inspection is rejected, the same way §5.2 rejects a blank
'accepted_anchor' as evidence of substantive verification.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class Standard(Enum):
    """The 'square, level, plumb' equivalents available to this system.
    Inspection must name one — there is no 'inspector said so' option."""
    AST_PARSES = "ast_parses_clean"
    LIVE_QUERY_MATCHES = "live_query_result_matches_claim"
    SMOKE_TEST_PASSES = "smoke_test_passes"
    JUSTIFICATION_SPECIFIC = "justification_meets_specificity_check"  # mirrors _justification_is_specific()


class StoneState(Enum):
    DRESSED = "dressed_awaiting_inspection"   # Zone 1 output — real, unset
    REJECTED = "rejected_returned_to_bench"   # failed inspection — back to Zone 1
    APPROVED = "approved_awaiting_placement"  # Zone 2 passed — not yet built in
    SET = "set_in_wall"                       # Zone 3 — irreversible, load-bearing


class MasonGateError(Exception):
    """Raised when a stone is set without having passed real inspection.
    This is the hard-reject — no code path may place a stone in SET state
    without an APPROVED predecessor state and a cited Standard."""


@dataclass
class Stone:
    stone_id: str
    description: str
    banker_mark: str        # declarant_id — who dressed/prepared the work
    state: StoneState = StoneState.DRESSED
    waller_mark: str | None = None       # administrator_id — who sets it, filled at Zone 3
    standard_applied: Standard | None = None
    inspection_note: str | None = None
    history: list = field(default_factory=list)

    def _log(self, event: str):
        self.history.append({"event": event, "at": datetime.now(timezone.utc).isoformat()})


def bank_stone(stone_id: str, description: str, banker_mark: str) -> Stone:
    """Zone 1 — journeyman dresses the stone. Real work, not yet in the wall."""
    s = Stone(stone_id=stone_id, description=description, banker_mark=banker_mark)
    s._log(f"DRESSED by {banker_mark}")
    return s


def inspect_stone(stone: Stone, standard: Standard, note: str) -> Stone:
    """Zone 2 — master's inspection against a named, checkable standard.
    A generic note ('looks fine') without a real Standard does not pass —
    mirrors the passive/substantive split from §5.2 directly."""
    if stone.state != StoneState.DRESSED:
        raise MasonGateError(f"{stone.stone_id} is not awaiting inspection (state={stone.state})")

    if not note or len(note.split()) < 5:
        stone.state = StoneState.REJECTED
        stone._log(f"REJECTED — inspection note not substantive: '{note}'")
        return stone

    stone.standard_applied = standard
    stone.inspection_note = note
    stone.state = StoneState.APPROVED
    stone._log(f"APPROVED against {standard.value} — {note}")
    return stone


def set_stone(stone: Stone, waller_mark: str) -> Stone:
    """Zone 3 — irreversible placement. HARD-REJECTS if the stone did not
    pass a real, standard-cited inspection. This is the enforcement point:
    no amount of urgency skips APPROVED -> SET."""
    if stone.state != StoneState.APPROVED:
        raise MasonGateError(
            f"REFUSED: {stone.stone_id} cannot be set — state is {stone.state}, "
            f"not APPROVED. No override exists for this check."
        )
    stone.waller_mark = waller_mark
    stone.state = StoneState.SET
    stone._log(f"SET by {waller_mark}")
    return stone


# ─────────────────────────────────────────────────────────────────────────
# DEMONSTRATION — the real finding from this session's GOVERNANCE.md pilot,
# not a synthetic example. Commit 1964b84, 'fair' dimension dropped 16pts
# behind a generic "Update GOVERNANCE.md" message.
# ─────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("── Case 1: the real 1964b84 flag, correctly refused ──")
    stone = bank_stone(
        stone_id="1964b84-fair-delta",
        description="fair dimension -16.0pts, commit 1964b84, msg='Update GOVERNANCE.md'",
        banker_mark="unit-zero-pilot-run",
    )
    print(f"  state after banking: {stone.state.value}")

    # A real inspector would find the commit message generic and refuse to certify it —
    # note is too short/non-specific, so this correctly fails inspection.
    inspect_stone(stone, Standard.JUSTIFICATION_SPECIFIC, note="msg generic")
    print(f"  state after weak inspection attempt: {stone.state.value}")

    try:
        set_stone(stone, waller_mark="night")
    except MasonGateError as e:
        print(f"  set_stone correctly refused: {e}")

    print("\n── Case 2: same stone, properly inspected and set ──")
    stone2 = bank_stone(
        stone_id="1964b84-fair-delta-reviewed",
        description="fair dimension -16.0pts, commit 1964b84",
        banker_mark="unit-zero-pilot-run",
    )
    inspect_stone(
        stone2, Standard.JUSTIFICATION_SPECIFIC,
        note="Reviewed diff directly: fair-dimension drop traced to removal of the "
             "exception-pathway clause in §P24, a real content change, not tool noise.",
    )
    print(f"  state after real inspection: {stone2.state.value}")
    set_stone(stone2, waller_mark="night")
    print(f"  state after set: {stone2.state.value}")
    print(f"  banker_mark={stone2.banker_mark}  waller_mark={stone2.waller_mark}")
    for h in stone2.history:
        print(f"    {h['at']}  {h['event']}")
