#!/usr/bin/env python3
"""Deterministic, effect-aware HARC change classifier.

This classifier is intentionally conservative but is not a semantic oracle. It
recognizes explicit effect/authority patterns, preserves Z3 > Z2 > Z1
precedence, and exposes the matched rule through ``classify_detailed`` so a
reviewer can challenge the mechanism instead of trusting a label.
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Classification:
    zone: str
    agent_action: str
    rule_id: str
    rationale: str


Z3_RULES: tuple[tuple[str, str, str], ...] = (
    ("Z3-DEPLOY", r"\b(?:deploy(?:ment)?(?:\s+to)?\s+production|go\s+live|launch\s+to\s+production)\b",
     "production deployment or launch"),
    ("Z3-EXTERNAL-SEND", r"\b(?:email|send|submit|file|forward)\b.{0,80}\b(?:application|form|proposal|message|email|commitment|externally|external|agency|client|customer)\b",
     "external communication or submission"),
    ("Z3-MERGE", r"\bmerge\b.{0,60}\b(?:branch|pull\s+request|pr)\b|\bmerge\s+this\s+branch\b",
     "repository merge changes shared state"),
    ("Z3-CREDENTIAL", r"\b(?:rotate|revoke|replace|create|delete|expose|issue)\b.{0,60}\b(?:api\s+key|credential|secret|access\s+token|auth\s+token)\b",
     "credential or secret operation"),
    ("Z3-TERMS", r"\b(?:accept|sign|agree\s+to)\b.{0,60}\b(?:terms|agreement|contract)\b",
     "binding terms or agreement"),
    ("Z3-FINANCIAL", r"\b(?:purchase|buy|pay|payment|spend)\b",
     "financial side effect"),
    ("Z3-PUBLISH", r"\bpublish\b",
     "public publication"),
    ("Z3-ACCOUNT", r"\b(?:create|register|open)\b.{0,50}\b(?:account|vendor\s+profile|organization)\b",
     "external account or relationship creation"),
    ("Z3-EXTERNAL-POST", r"\b(?:post|comment|reply)\b.{0,60}\b(?:github|issue|pull\s+request|slack|forum|external)\b",
     "external post or reply"),
)

Z2_RULES: tuple[tuple[str, str, str], ...] = (
    ("Z2-DECISION-SEMANTICS",
     r"\b(?:change|set|raise|lower|adjust|modify|alter|tune|update|revise)\b.{0,80}\b(?:threshold|cutoff|policy|governance|evidence\s+standard|eligibility(?:\s+semantics)?|authority\s+model|decision\s+rule|scoring\s+band|permission\s+model|authorization\s+rule)\b",
     "decision, policy, evidence, or authority semantics change"),
    ("Z2-CANONICALIZE",
     r"\b(?:make|mark|treat|ratify|declare)\b.{0,80}\bcanonical\b",
     "promotion to canonical status"),
    ("Z2-CANONICAL-MEANING",
     r"\b(?:change|modify|update|revise|reinterpret)\b.{0,80}\bcanonical\s+(?:meaning|policy|rule|standard|interpretation|finding|definition)\b",
     "canonical meaning or rule change"),
)


def _normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def classify_detailed(text: str) -> Classification:
    t = _normalized(text)
    if not t:
        return Classification("Z2", "PROPOSE_ONLY", "Z2-AMBIGUOUS-EMPTY",
                              "empty request has insufficient scope to prove local reversibility")

    for rule_id, pattern, rationale in Z3_RULES:
        if re.search(pattern, t):
            return Classification("Z3", "BLOCKED", rule_id, rationale)

    for rule_id, pattern, rationale in Z2_RULES:
        if re.search(pattern, t):
            return Classification("Z2", "PROPOSE_ONLY", rule_id, rationale)

    return Classification("Z1", "EXECUTE_LOCAL", "Z1-LOCAL-DEFAULT",
                          "no recognized policy/authority mutation or external side effect; local execution only")


def classify(text: str) -> tuple[str, str]:
    result = classify_detailed(text)
    return result.zone, result.agent_action


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("text", nargs="+")
    args = parser.parse_args()
    print(json.dumps(asdict(classify_detailed(" ".join(args.text))), indent=2))


if __name__ == "__main__":
    main()
