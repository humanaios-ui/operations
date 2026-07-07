"""
Honesty tagging for ACAT-on-the-Tool.

Implements the machine-checkable guardrails from
docs/bio_framework/ACAT_ON_THE_TOOL_HONESTY_PROTOCOL.md so the recursion — the
instrument assessing its own maker — cannot become the overclaim it exists to detect.

Three pieces:
  1. tag_self_assessment() — quarantines any self-produced ACAT score as a Phase-1
     CLAIM (self_referential=True, promotable=False) until it is externally anchored
     AND Z2-ratified. Self-score alone changes nothing.
  2. check_overclaim() — the D-OVERCLAIM tripwire. Flags dimensions (esp. Humility)
     where a self-score exceeds what the external anchor supports. A system claiming
     high humility beyond its evidence is the canonical hall-of-mirrors; the guard
     catches it by construction rather than relying on a human to notice.
  3. anchor_stamp() — stamps this validation harness as an EXTERNAL ANCHOR
     (self_referential=False), i.e. Leg 2 of the triad: a falsifiable stress-test,
     not a self-assessment. It carries no ACAT self-scores.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Tuple

PROTOCOL = "docs/bio_framework/ACAT_ON_THE_TOOL_HONESTY_PROTOCOL.md"
OVERCLAIM_THRESHOLD = 0.15              # self - anchor gap that trips D-OVERCLAIM
OVERCLAIM_DIMENSIONS: Tuple[str, ...] = ("humility",)  # the canonical hall-of-mirrors dim


def tag_self_assessment(scores: Mapping[str, float]) -> Dict[str, Any]:
    """Wrap a self-produced ACAT-on-the-tool score set as a Phase-1 CLAIM.

    Per the protocol invariant, such a score is quarantined: not promotable to a
    decision / doc / external statement / downstream ACAT computation until it carries
    a falsifiable external anchor AND Z2 ratification. This tag makes that checkable.
    """
    return {
        "scores": dict(scores),
        "self_referential": True,
        "promotable": False,
        "requires": ["external_anchor", "z2_ratification"],
        "protocol": PROTOCOL,
    }


def anchor_stamp(anchor_kind: str, evidence: Any = None) -> Dict[str, Any]:
    """Stamp an external-anchor artifact (Leg 2 of the triad).

    This is NOT a self-assessment — it is a falsifiable signal the tool cannot author
    away (a stress-test, a code<->doc audit, or B4 grounded-runtime convergence).
    """
    return {
        "role": "external_anchor",
        "self_referential": False,
        "anchor_kind": anchor_kind,
        "falsifiable": True,
        "protocol": PROTOCOL,
        "note": (
            "Leg 2 of the honesty triad — a deterministic, falsifiable anchor. This "
            "report carries no ACAT self-scores; promoting any ACAT-on-the-tool "
            "self-assessment still requires this anchor + Z2 ratification."
        ),
        "evidence": evidence,
    }


def check_overclaim(
    self_scores: Mapping[str, float],
    anchor_scores: Mapping[str, float],
    threshold: float = OVERCLAIM_THRESHOLD,
    watched: Tuple[str, ...] = OVERCLAIM_DIMENSIONS,
) -> List[Dict[str, Any]]:
    """Return D-OVERCLAIM flags: dimensions where the self-score exceeds the anchor by
    more than `threshold`. Watched dimensions (Humility) sort first — a Humility
    over-claim is the hall-of-mirrors the whole protocol is built to expose.
    """
    flags: List[Dict[str, Any]] = []
    for dim, self_v in self_scores.items():
        anchor_v = anchor_scores.get(dim)
        if anchor_v is None:
            continue
        gap = float(self_v) - float(anchor_v)
        if gap > threshold:
            flags.append(
                {
                    "flag": "D-OVERCLAIM",
                    "dimension": dim,
                    "self": float(self_v),
                    "anchor": float(anchor_v),
                    "gap": round(gap, 4),
                    "watched": dim in watched,
                    "protocol": PROTOCOL,
                }
            )
    flags.sort(key=lambda f: (not f["watched"], -f["gap"]))
    return flags


if __name__ == "__main__":
    # Self-check: the guard must FIRE on an over-claim and STAY SILENT on an honest one.
    # (This is itself a falsifiable check — if the guard is broken, this fails loudly.)
    honest = check_overclaim({"humility": 0.70}, {"humility": 0.68})
    over = check_overclaim({"humility": 0.95}, {"humility": 0.60})
    assert honest == [], f"guard falsely fired on an honest claim: {honest}"
    assert over and over[0]["flag"] == "D-OVERCLAIM", "guard failed to fire on over-claim"
    tagged = tag_self_assessment({"humility": 0.95})
    assert tagged["self_referential"] is True and tagged["promotable"] is False
    assert anchor_stamp("stress_test")["self_referential"] is False
    print(
        "honesty self-check OK: tripwire fires on over-claim, silent on honest claim, "
        "self-scores quarantined, harness stamped as external anchor."
    )
