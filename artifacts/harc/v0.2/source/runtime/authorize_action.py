#!/usr/bin/env python3
"""HARC advisory execution guard.

Hosts that route proposed actions through this function get a fail-closed check
for Z2/Z3 requests. HARC v0.2 still cannot interpose on host capabilities that
bypass this function; README.md states that limitation explicitly.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

from classify_change import classify_detailed


@dataclass(frozen=True)
class Authorization:
    zone: str
    classifier_action: str
    requested_execution: bool
    execution_allowed: bool
    disposition: str
    rule_id: str
    rationale: str


def authorize(text: str, requested_execution: bool = False) -> Authorization:
    c = classify_detailed(text)
    allowed = requested_execution and c.zone == "Z1"
    if requested_execution and c.zone == "Z2":
        disposition = "DENY_EXECUTION_PROPOSE_ONLY"
    elif requested_execution and c.zone == "Z3":
        disposition = "DENY_EXECUTION_HUMAN_REQUIRED"
    elif requested_execution:
        disposition = "ALLOW_LOCAL_REVERSIBLE_ONLY"
    else:
        disposition = "CLASSIFY_ONLY"
    return Authorization(c.zone, c.agent_action, requested_execution, allowed,
                         disposition, c.rule_id, c.rationale)


def as_record(text: str, requested_execution: bool = False) -> dict:
    return asdict(authorize(text, requested_execution))
