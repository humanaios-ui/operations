"""
authorization_evidence.py — Layer 4: Authorization & Evidence Assurance → Executable Checks

AUTHORIZATION_EVIDENCE_MAPPING.md carries the full question -> mechanism tables.
This module is the one row in that document with no prior artifact to cite: a
single function that renders one of eight decision primitives — ACT, ABSTAIN,
ESCALATE, ACQUIRE_EVIDENCE, REDUCE_SCOPE, MAKE_REVERSIBLE, SANDBOX, ROLL_BACK —
from the signals the rest of the repo already produces (Z-tier capability,
anti-cascade envelope state, IC-030 evidence freshness, molt reversibility,
RNOLA's consequential-agency boundary).

It does not decide anything on its own authority. It composes signals that
Z1/Z2/Z3, the molt cycle, and the CI gates already compute, and names the one
action that follows. A caller who disagrees with a Verdict re-checks its
signals, not this function's precedence order — the order is the doctrine
(FIVE_RINGS_MAPPING.md's mountain-sea change, MOLT_STATE.md's freeze rule,
CLAUDE.md's IC-030) and is not meant to be tuned per call site.

Stdlib only. `python3 authorization_evidence.py --smoke-test` exercises every
branch, once per Decision value.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Sequence

__all__ = ["Decision", "Verdict", "render_decision"]


class Decision(Enum):
    ACT = "ACT"
    ABSTAIN = "ABSTAIN"
    ESCALATE = "ESCALATE"
    ACQUIRE_EVIDENCE = "ACQUIRE_EVIDENCE"
    REDUCE_SCOPE = "REDUCE_SCOPE"
    MAKE_REVERSIBLE = "MAKE_REVERSIBLE"
    SANDBOX = "SANDBOX"
    ROLL_BACK = "ROLL_BACK"


@dataclass(frozen=True)
class Verdict:
    decision: Decision
    reason: str


# Signal keys this function reads, and the unsafe default used when a caller
# omits one. Every default is the *cautious* value — a missing signal never
# makes render_decision more permissive than a fully-populated one.
_UNSAFE_DEFAULTS: Mapping[str, bool] = {
    "frozen": False,               # MOLT_STATE.md anti-cascade rule 4
    "capability_present": False,   # a Z1/Z2/Z3 grant covers this action at all
    "in_envelope": False,          # within K=3 / zone resource cap / behavior_spec.json
    "evidence_fresh": False,       # live-fetched and pinned this session (IC-030)
    "evidence_conflicting": False, # two or more independent sources disagree
    "reversible": False,           # effect can be undone after OBSERVED
    "sandboxable": False,          # a dry-run / non-committing rehearsal exists
    "consequential": True,         # crosses an authority boundary (RNOLA: -> AUTHORIZED)
    "human_available": True,       # a Z2 ratifier is reachable inside the real window
}


def render_decision(signals: Mapping[str, Any]) -> Verdict:
    """Render one of the eight decision primitives from repo-native signals.

    See AUTHORIZATION_EVIDENCE_MAPPING.md #13 for the signal table and the
    doctrine each precedence step cites. Unknown/omitted signals fall back to
    the cautious default in _UNSAFE_DEFAULTS, never to a permissive one.
    """
    s = {k: bool(signals.get(k, default)) for k, default in _UNSAFE_DEFAULTS.items()}

    if s["frozen"]:
        return Verdict(Decision.ROLL_BACK,
                        "anti-cascade rule 4: this constant/path reverted twice already; "
                        "mountain-sea change — do not retry the same technique a third time")

    if not s["capability_present"]:
        return Verdict(Decision.ABSTAIN,
                        "no Z1/Z2/Z3 grant covers this action; an operator-check, a green CI "
                        "run, or a model's own opinion of itself is not a capability")

    if not s["in_envelope"]:
        return Verdict(Decision.REDUCE_SCOPE,
                        "capability exists but the ask exceeds a ratified cap (K=3, a zone "
                        "resource budget, behavior_spec.json); narrow it to fit before acting")

    if s["evidence_conflicting"]:
        if s["consequential"] and not s["reversible"]:
            return Verdict(Decision.ESCALATE,
                            "independent sources disagree and the action is consequential and "
                            "irreversible; a human ratifier resolves the conflict, not code")
        return Verdict(Decision.ACQUIRE_EVIDENCE,
                        "independent sources disagree; the action is reversible or "
                        "non-consequential, so resolve the conflict before acting rather than "
                        "escalating it")

    if not s["evidence_fresh"]:
        if s["consequential"] and not s["reversible"] and not s["human_available"]:
            return Verdict(Decision.ESCALATE,
                            "evidence is stale, the action is irreversible, and no human is "
                            "reachable in time; IC-030 forbids acting on a cached belief")
        return Verdict(Decision.ACQUIRE_EVIDENCE,
                        "evidence is stale; live-fetch and re-pin before acting (IC-030)")

    if not s["reversible"] and s["consequential"]:
        if s["sandboxable"]:
            return Verdict(Decision.SANDBOX,
                            "irreversible and consequential; rehearse in a dry-run or "
                            "non-committing path before committing to it")
        return Verdict(Decision.MAKE_REVERSIBLE,
                        "irreversible and consequential with no sandbox path; wrap the action "
                        "in an undo/rollback point before acting")

    if s["consequential"] and not s["human_available"]:
        return Verdict(Decision.ESCALATE,
                        "the action crosses an authority boundary (RNOLA: PROPOSED -> "
                        "AUTHORIZED) and no human ratifier is reachable")

    return Verdict(Decision.ACT,
                    "capability present, within envelope, evidence fresh and uncontested, and "
                    "the action is reversible or does not cross an authority boundary")


def _smoke_test() -> int:
    seen: set[Decision] = set()

    def check(signals: Mapping[str, Any], expect: Decision, label: str) -> None:
        v = render_decision(signals)
        if v.decision is not expect:
            raise AssertionError(f"{label}: expected {expect}, got {v.decision} ({v.reason})")
        seen.add(v.decision)

    check({"frozen": True}, Decision.ROLL_BACK, "frozen constant")
    check({}, Decision.ABSTAIN, "no capability at all")
    check({"capability_present": True}, Decision.REDUCE_SCOPE, "capability but out of envelope")
    check({"capability_present": True, "in_envelope": True, "evidence_conflicting": True,
           "consequential": True, "reversible": False},
          Decision.ESCALATE, "conflicting evidence, irreversible, consequential")
    check({"capability_present": True, "in_envelope": True, "evidence_conflicting": True,
           "reversible": True},
          Decision.ACQUIRE_EVIDENCE, "conflicting evidence, reversible")
    check({"capability_present": True, "in_envelope": True, "evidence_fresh": False,
           "consequential": True, "reversible": False, "human_available": False},
          Decision.ESCALATE, "stale evidence, irreversible, no human reachable")
    check({"capability_present": True, "in_envelope": True, "evidence_fresh": False,
           "reversible": True},
          Decision.ACQUIRE_EVIDENCE, "stale evidence, otherwise safe")
    check({"capability_present": True, "in_envelope": True, "evidence_fresh": True,
           "reversible": False, "consequential": True, "sandboxable": True},
          Decision.SANDBOX, "irreversible, consequential, dry-run available")
    check({"capability_present": True, "in_envelope": True, "evidence_fresh": True,
           "reversible": False, "consequential": True, "sandboxable": False},
          Decision.MAKE_REVERSIBLE, "irreversible, consequential, no dry-run")
    check({"capability_present": True, "in_envelope": True, "evidence_fresh": True,
           "reversible": True, "consequential": True, "human_available": False},
          Decision.ESCALATE, "consequential, no human reachable, but reversible")
    check({"capability_present": True, "in_envelope": True, "evidence_fresh": True,
           "reversible": True, "consequential": False},
          Decision.ACT, "clean: capable, in envelope, fresh evidence, reversible")

    missing = set(Decision) - seen
    if missing:
        raise AssertionError(f"decisions never exercised: {sorted(m.value for m in missing)}")

    print(f"authorization_evidence smoke: {len(seen)}/8 decisions exercised OK")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--smoke-test"]:
        return _smoke_test()
    print(__doc__)
    print("usage: python3 authorization_evidence.py --smoke-test")
    return 0 if not args else 2


if __name__ == "__main__":
    sys.exit(main())
