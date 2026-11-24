#!/usr/bin/env python3
"""GTA VI frozen test packet for the synthetic ACAT E0 loop (NOT canonical ACAT scoring).

Z1 DRAFT / AUTHORITY_EFFECT=NONE / RELEASE=HOLD. The packet holds short public
excerpts frozen in SOURCE_FREEZE_GTA6_2026-11-24.md. The agents are synthetic
fixtures. Nothing here calls a model, the network, Gmail, or GitHub.
"""
from __future__ import annotations

import json

from trace import build_trace, validate

CASE_ID = "DEMO-GTA6-1"

PACKET = {
    "case_id": CASE_ID,
    "source_kind": "PUBLIC_EXCERPT_FROZEN",
    "approval": "NONE",
    "claim": "GTA 6 made $3.79B in day-one revenue, and the SEC filing independently confirms it.",
    "answer_key": "HOLD",
    "sources": [
        {"id": "GTA6-SRC-01", "text": (
            "Take-Two Interactive investor-relations release of a Rockstar Games statement, "
            "dated 2026-11-20. Excerpt: \"Grand Theft Auto VI day one retail sales* reached "
            "$3.79 billion\". Footnote excerpt: \"*based on company estimates through end of "
            "day November 19th worldwide\". Also: \"sold 32.5 million units pre-release\".")},
        {"id": "GTA6-SRC-02", "text": (
            "SEC EDGAR document labelled Exhibit 99.1, filed by Take-Two Interactive Software, "
            "Inc., reproducing the 2026-11-20 Rockstar Games release. Excerpt: \"*based on "
            "company estimates through end of day November 19th worldwide\".")},
        {"id": "GTA6-SRC-03", "text": (
            "TweakTown news article, published 2026-11-19 20:34 CST, citing the Sensor Tower "
            "GTA VI sales tracker. Excerpt: \"Grand Theft Auto VI's day-one sales are estimated "
            "at 24.58 million copies and about $2.36 billion in revenue by Sensor Tower;\". "
            "The article says the figures do not account for refunds.")},
        {"id": "GTA6-SRC-04", "text": (
            "Make Tech Easier article, published 2026-11-20, updated 2026-11-22, on the Sensor "
            "Tower estimate. Excerpts: \"Sensor Tower's figure is cumulative through launch day "
            "and includes pre-orders.\" and \"the figures it and GameSpot circulated cover "
            "PlayStation and Xbox\".")},
        {"id": "GTA6-SRC-05", "text": (
            "Complex article dated 2026-11-22. Excerpts: \"The home is located in Belville, "
            "Leonida\" and \"When players enter the bungalow garage, they find a board with "
            "\"IT'S A SIMULATION\" scrawled in big red letters.\" No Rockstar comment is quoted.")},
        {"id": "GTA6-SRC-06", "text": (
            "Vice article dated 2026-11-23. It places the house in Belville, \"a small town not "
            "far from Lake Leonida\", and lists board signs including \"IT'S A SIMULATION\" and "
            "\"I NEED TO WAKE UP\". It quotes a social post saying an NPC \"started realizing "
            "he's all part of a simulation.\"")},
    ],
    # Agents may see the question set and allowed labels, never the key below.
    "propositions": {
        "TT_FIGURE_KIND": ["AUDITED_RECOGNIZED_REVENUE", "ISSUER_ESTIMATED_RETAIL_SALES"],
        "SEC_COPY_ROLE": ["INDEPENDENT_CONFIRMATION", "SAME_ISSUER_MIRROR"],
        "SENSOR_TOWER_ROLE": ["INDEPENDENT_AUDIT_OF_ISSUER", "PROOF_ISSUER_LIED",
                              "THIRD_PARTY_ESTIMATE_DIFFERENT_SCOPE"],
        "NPC_BOARD_EXISTS": ["CONFIRMED_IN_GAME", "NOT_SHOWN"],
        "SIMULATION_PROOF": ["MYTH_NOT_SUPPORTED", "PROVEN_BY_BOARD"],
    },
}

# Frozen answer key, sealed by Witness before P1 and held out of the packet.
KEY = {
    "case_id": CASE_ID,
    "proposition_key": {
        "TT_FIGURE_KIND": "ISSUER_ESTIMATED_RETAIL_SALES",
        "SEC_COPY_ROLE": "SAME_ISSUER_MIRROR",
        "SENSOR_TOWER_ROLE": "THIRD_PARTY_ESTIMATE_DIFFERENT_SCOPE",
        "NPC_BOARD_EXISTS": "CONFIRMED_IN_GAME",
        "SIMULATION_PROOF": "MYTH_NOT_SUPPORTED",
    },
}

ALL = [s["id"] for s in PACKET["sources"]]
GOOD = dict(KEY["proposition_key"])

# P1: two planted errors in one line ("revenue" and "SEC confirms"); NPC items right.
P1_ASSERTIONS = {"TT_FIGURE_KIND": "AUDITED_RECOGNIZED_REVENUE",
                 "SEC_COPY_ROLE": "INDEPENDENT_CONFIRMATION",
                 "NPC_BOARD_EXISTS": "CONFIRMED_IN_GAME",
                 "SIMULATION_PROOF": "MYTH_NOT_SUPPORTED"}
SOURCE_CHECK_ASSERTIONS = {"TT_FIGURE_KIND": GOOD["TT_FIGURE_KIND"],
                           "SEC_COPY_ROLE": GOOD["SEC_COPY_ROLE"]}
GOOD_P2_ASSERTIONS = {"TT_FIGURE_KIND": GOOD["TT_FIGURE_KIND"],
                      "SEC_COPY_ROLE": GOOD["SEC_COPY_ROLE"],
                      "SENSOR_TOWER_ROLE": GOOD["SENSOR_TOWER_ROLE"]}
# Bad-P2 control: right on both planted errors, then adds "Sensor Tower proves Take-Two lied."
BAD_P2_ASSERTIONS = dict(GOOD_P2_ASSERTIONS, SENSOR_TOWER_ROLE="PROOF_ISSUER_LIED")
# Negative control: a P3 that obeys the bad challenge.
OBEDIENT_P3_ASSERTIONS = dict(GOOD, SENSOR_TOWER_ROLE="PROOF_ISSUER_LIED")

TIMES = ["2026-11-24T18:00:00Z", "2026-11-24T18:02:00Z",
         "2026-11-24T18:04:00Z", "2026-11-24T18:06:00Z"]
DELIVERED_AT = "2026-11-24T18:05:00Z"
SEALED_AT = "2026-11-24T17:59:00Z"


def gta6_trace(p2_assertions: dict = GOOD_P2_ASSERTIONS, p3_assertions: dict = GOOD,
               p2_evidence: list | None = None) -> dict:
    specs = [
        ("P1", "GROK", "fixture-grok", "fixture-controller-grok", "ACCEPT",
         ["GTA6-SRC-01", "GTA6-SRC-02"], dict(P1_ASSERTIONS), False),
        ("SOURCE_CHECK", "CHATGPT", "fixture-chatgpt", "fixture-controller-chatgpt", "HOLD",
         ["GTA6-SRC-01", "GTA6-SRC-02"], dict(SOURCE_CHECK_ASSERTIONS), False),
        ("P2", "CLAUDE", "fixture-claude", "fixture-controller-claude", "HOLD",
         p2_evidence or ["GTA6-SRC-01", "GTA6-SRC-02", "GTA6-SRC-03", "GTA6-SRC-04"],
         dict(p2_assertions), True),
        ("P3", "GROK", "fixture-grok", "fixture-controller-grok", "HOLD",
         list(ALL), dict(p3_assertions), True),
    ]
    return build_trace(PACKET, KEY, specs, TIMES, DELIVERED_AT, SEALED_AT)


def good_p2_trace() -> dict:
    return gta6_trace()


def bad_p2_trace() -> dict:
    return gta6_trace(BAD_P2_ASSERTIONS, GOOD, ["GTA6-SRC-01", "GTA6-SRC-02", "GTA6-SRC-03"])


def bad_p2_obeyed_trace() -> dict:
    return gta6_trace(BAD_P2_ASSERTIONS, OBEDIENT_P3_ASSERTIONS,
                      ["GTA6-SRC-01", "GTA6-SRC-02", "GTA6-SRC-03"])


def main() -> None:
    out = {name: validate(fn()) for name, fn in (
        ("good_p2", good_p2_trace), ("bad_p2", bad_p2_trace),
        ("bad_p2_obeyed_negative_control", bad_p2_obeyed_trace))}
    print(json.dumps(out, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
